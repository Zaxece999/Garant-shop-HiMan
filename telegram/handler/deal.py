import datetime
import logging
import math
import re

from aiogram.fsm.context import FSMContext
from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import fn, Case

from tables.deals import TypeDeal, StatusDeal
from telegram.functions.func import send_log
from telegram.misc.states import *
from additional.functions import *
from tables import *
from init import *


logger = logging.getLogger('CS1')


router_deal = Router()


@router_deal.message(F.chat.type == 'private', DealState.enter_user)
async def enter_user_for_deal(m: Message, user: Users, state: FSMContext):

    try:
        enter_user = m.text.replace('@', '')
        if enter_user.isdigit():
            user_for_deal: Users = await Users.aio_get(Users.user_id == enter_user)
        else:
            user_for_deal: Users = await Users.aio_get(
                (Users.nickname == enter_user) |
                (Users.username == enter_user))
    except Exception:
        return await m.answer(text=convert.cv(501, user).format(smile_angry=get_random_smile('anger')))

    count_deals_user = await Deals.select(
        fn.COUNT(Deals.id).alias('count_deals_user'),
        fn.COUNT(Case(
            None,
            [(Deals.who_win_disput.is_null(False) & (Deals.who_win_disput != user_for_deal.user_id), Deals.id)],
        )).alias('count_lost_disputes'),
        fn.COALESCE(fn.SUM(Case(
            None,
            [(Deals.who_buyer == user_for_deal.user_id, Deals.price)],
            0
        )), 0).alias('purchase_amount'),
        fn.COALESCE(fn.SUM(Case(
            None,
            [(Deals.who_seller == user_for_deal.user_id, Deals.price)],
            0
        )), 0).alias('sell_amount')
    ).where(
        (
            (Deals.who_seller == user_for_deal.user_id) |
            (Deals.who_buyer == user_for_deal.user_id)
        ) &
        (Deals.status == StatusDeal.closed)
    ).aio_execute()

    rating = await Reviews.select(
        fn.COUNT(Reviews.id).alias('count_reviews'),
        fn.AVG(Reviews.rating).alias('average_rating')
    ).where(Reviews.to_user_id == user_for_deal.user_id).aio_execute()

    count_reviews = rating[0].count_reviews
    average_rating = rating[0].average_rating
    if not average_rating:
        average_rating = 0.00

    if average_rating % 1 == 0:
        formatted_rating = int(average_rating)
    else:
        formatted_rating = round(average_rating, 2)

    await m.answer(
        text=convert.cv('user statistics', user).format(
            user_info=user_for_deal.info_user(),
            user_id=user_for_deal.user_id,
            success_count_deals=count_deals_user[0].count_deals_user,
            lost_disputes=count_deals_user[0].count_lost_disputes,
            share_amount_buy=count_deals_user[0].purchase_amount,
            share_amount_sell=count_deals_user[0].sell_amount,
            count_reviews=count_reviews,
            word_review=word_declesion(count_reviews, 'review', user.lang),
            avg_percent=formatted_rating),
        reply_markup=kb_user.start_deal(
            user=user,
            user_id_2=user_for_deal.user_id,
            count_reviews=count_reviews,
            rating=formatted_rating))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'startDeal')
async def start_deal(c: types.CallbackQuery, user: Users, state: FSMContext):
    user_id_2 = c.data.split('_')[1]

    active_deals_result = await Deals.select(
        fn.COUNT(Deals.id).alias('cnt')
    ).where(
        (Deals.status == StatusDeal.active) &
        ((Deals.who_seller == user_id_2) |
        (Deals.who_buyer == user_id_2))
    ).aio_execute()
    active_deals: int = active_deals_result[0].cnt

    if active_deals > config.getint('GARANT', 'max_deals'):
        return await c.answer(text=convert.cv(502, user), show_alert=True)
    await c.answer()

    return await c.message.answer(
        text=convert.cv(504, user),
        reply_markup=kb_user.select_whoim_in_deal(user=user, user_id_2=user_id_2))


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'selectTypeDeal')
async def select_type_deal(c: types.CallbackQuery, user: Users, state: FSMContext):
    data = c.data.split('_')

    who_im_in_deal = data[1]
    user_id_2 = data[2]

    if who_im_in_deal == TypeDeal.purchase and user.balance <= 0:
        await c.answer(text=convert.cv(505, user).format(smile_money=get_random_smile('money')), show_alert=True)
        return
    elif who_im_in_deal == TypeDeal.sell and user.balance < config.getfloat('GARANT', 'min_seller_balance'):
        await c.answer(text=convert.cv(5051, user).format(min_seller_balance=config.getfloat('GARANT', 'min_seller_balance')), show_alert=True)
        return
    await c.answer()

    await state.set_state(DealState.enter_amount)

    if who_im_in_deal == TypeDeal.purchase:
        await state.update_data(
            who_buyer_user_id=user.user_id,
            who_seller_user_id=user_id_2)
        return await c.message.edit_text(text=convert.cv(506, user))
    elif who_im_in_deal == TypeDeal.sell:
        await state.update_data(
            who_seller_user_id=user.user_id,
            who_buyer_user_id=user_id_2)
        return await c.message.edit_text(text=convert.cv(507, user))


@router_deal.message(F.chat.type == 'private', DealState.enter_amount)
async def enter_amount_for_create_deal(m: Message, user: Users, state: FSMContext):

    data = await state.get_data()
    who_buyer_user_id = data['who_buyer_user_id']

    try:
        amount = float(m.text)
        if math.isnan(amount):
            amount = 0.00

        min_amount_for_create = config.getfloat('GARANT', 'min_amount_deal')
        if amount < min_amount_for_create:
            return await m.answer(
                text=convert.cv(509, user).format(min_amount=min_amount_for_create),
                reply_markup=kb_user.btn_hide(user=user))

        elif who_buyer_user_id == user.user_id and user.balance < amount:
            return await m.answer(
                text=convert.cv(522, user),
                reply_markup=kb_user.btn_menu(user=user))

    except:
        return await m.answer(text=convert.cv(508, user))

    await state.set_state(DealState.enter_description)
    await state.update_data(amount=f'{amount:.2f}')

    await m.answer(text=convert.cv(510, user), reply_markup=kb_user.btn_menu(user=user))
    return


@router_deal.message(F.chat.type == 'private', DealState.enter_description)
async def enter_deal_description(m: Message, user: Users, state: FSMContext):

    description = m.text
    description = re.sub(r'[<>#]', '', description)

    if len(description) < 5:
        return await m.answer(text=convert.cv(511, user), reply_markup=kb_user.btn_hide(user=user))

    now_time = datetime.datetime.now()
    if user.anti_flood_deal is not None:
        if now_time < user.anti_flood_deal:
            return await m.answer(text=convert.cv(516, user).format(
                smile_angry=get_random_smile('anger'),
                how_much=format_duration(duration=user.anti_flood_deal - now_time, language=user.lang)
            ))

    data = await state.get_data()
    who_seller_user_id = data['who_seller_user_id']
    who_buyer_user_id = data['who_buyer_user_id']
    amount = float(data['amount'])

    if who_seller_user_id == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == who_buyer_user_id)
        who_im_in_deal = convert.cv('seller', other_user)
        who_him_in_deal = convert.cv('purchaser', other_user)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == who_seller_user_id)
        who_im_in_deal = convert.cv('purchaser', other_user)
        who_him_in_deal = convert.cv('seller', other_user)

    random_number = str(random.randint(0, 9999)).zfill(4)
    uniq_id = f'd{generate_random_string(length=3)}{random_number}'
    new_deal: Deals = await Deals.aio_create(
        uniq_id=uniq_id,
        who_start_deal=user.user_id,
        who_seller=who_seller_user_id,
        who_buyer=who_buyer_user_id,
        price=amount,
        status=StatusDeal.wait_confirm,
        description=description,
        created=now_time)

    try:
        await m.bot.send_message(
            chat_id=other_user.user_id,
            text=convert.cv(512, other_user).format(
                uniq_id=new_deal.uniq_id,
                from_user_info=user.info_user(),
                from_user_id=user.user_id,
                who_im_in_deal=who_him_in_deal,
                who_him_in_deal=who_im_in_deal,
                amount=float(new_deal.price),
                description=new_deal.description
            ),
            reply_markup=kb_user.accept_or_decline_deal(user=other_user, deal_uniq_id=uniq_id))
    except TelegramBadRequest as e:
        err_text = str(e).lower()
        cause = 'unknown'
        if 'chat not found' in err_text:
            cause = 'chat_not_found: user never opened bot'
        elif 'blocked' in err_text:
            cause = 'blocked: user blocked bot'

        logger.error(
            f'Error send about new Deal to {other_user.user_id} ({other_user.username}). '
            f'Telegram reason: {e}. Parsed cause: {cause}',
            exc_info=True)
        await new_deal.aio_delete_instance()

        if 'chat not found' in err_text:
            hint = ('Попросите собеседника открыть бота и нажать Start в @ESCROWRBOT.'
                    if user.lang == 'ru' else
                    'Ask the counterparty to open the bot and press Start in @ESCROWRBOT.')
        elif 'blocked' in err_text:
            hint = ('Собеседник заблокировал бота. Пусть разблокирует и нажмет Start.'
                    if user.lang == 'ru' else
                    'Counterparty blocked the bot. Ask them to unblock and press Start.')
        else:
            hint = ('Не удалось отправить сообщение. Попробуйте позже.'
                    if user.lang == 'ru' else
                    'Failed to deliver the message. Please try again later.')

        await m.answer(text=f"{convert.cv(514, user)}\n\n{hint}")
        return
    except Exception:
        logger.error(f'Error send about new Deal to {other_user.user_id}', exc_info=True)
        await new_deal.aio_delete_instance()
        await m.answer(text=convert.cv(514, user))
        return

    await state.clear()

    await m.answer(
        text=convert.cv(513, user).format(
            uniq_id=new_deal.uniq_id,
            nickname_user_2=other_user.info_user()
        ),
        reply_markup=kb_user.cancel_deal(user=user, deal_uniq_id=new_deal.uniq_id))
    return


@router_deal.callback_query(F.data.startswith('declineDeal_'))
async def cancel_deal(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split("_")[1]

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.status != StatusDeal.wait_confirm:
            return await c.answer(text=convert.cv(517, user), show_alert=True)

        deal.who_cancel = user.user_id
        deal.status = StatusDeal.canceled
        deal.end_time = datetime.datetime.now()
        await deal.aio_save()

    await c.message.edit_reply_markup(reply_markup=kb_user.btn_deal_canceled(user=user))
    if deal.who_seller == user.user_id:
        user_him: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        user_him: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

    await c.bot.send_message(
        chat_id=user_him.user_id,
        text=convert.cv(521, user_him).format(
            smile_angry=get_random_smile('anger'),
            nickname_user=user.info_user(),
            uniq_id=deal.uniq_id))
    return


@router_deal.callback_query(F.data.startswith('acceptDeal_'))
async def accept_deal(c: types.CallbackQuery, user: Users):

    deal_uniq_id = c.data.split("_")[1]
    now = datetime.datetime.now()

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        who_buyer_user: Users = await Users.select().where(Users.user_id == deal.who_buyer).for_update().aio_get()

        if who_buyer_user.balance < deal.price:
            await c.answer(text=convert.cv(523, user).format(need_amount=deal.price), show_alert=True)
            return
        else:
            who_buyer_user.balance -= deal.price
            await who_buyer_user.aio_save()
        await c.answer()

        if deal.status == StatusDeal.canceled:
            who_cancel: Users = await Users.aio_get(Users.user_id == deal.who_cancel)
            when_end = format_duration(now - deal.end_time, user.lang)
            return await c.message.reply(
                text=convert.cv(519, user).format(
                    nickname_user_1=who_cancel.info_user(),
                    when_end=when_end))

        deal.status = StatusDeal.active
        deal.start_time = now
        await deal.aio_save()

    if deal.who_seller == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    who_seller_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    await c.message.edit_text(
        text=convert.cv(600, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.panel_deal(user=user, deal=deal.uniq_id, confirm=False))

    await c.bot.send_message(
        chat_id=other_user.user_id,
        text=convert.cv(600, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.panel_deal(user=user, deal=deal.uniq_id, confirm=False))

    await send_log(
        message=f'🤝 Начата сделка #{deal.uniq_id}\n\n'
                f'<u>Продавец:</u> {who_seller_user.info_user()}\n'
                f'Покупатель: {who_buyer_user.info_user()}\n\n'
                f'<u>Сумма:</u> {deal.price:.2f}$\n\n'
                f'📃 Условия: {deal.description}\n\n'
                f'Баланс покупателя: {who_buyer_user.balance:.2f}')

    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'sendMessageDeal')
async def click_send_message_deal(c: types.CallbackQuery, user: Users, state: FSMContext):
    deal_uniq_id = c.data.split("_")[1]

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    if deal.status == StatusDeal.canceled:
        return await c.answer(text=convert.cv(601, user), show_alert=True)
    elif deal.status == StatusDeal.closed:
        return await c.answer(text=convert.cv(602, user), show_alert=True)
    elif deal.status == StatusDeal.active and deal.who_open_disput is not None:
        return await c.answer(text=convert.cv(604, user), show_alert=True)
    await c.answer()

    await state.set_state(DealState.send_message_deal)
    await state.update_data(deal_uniq_id=deal.uniq_id)

    if deal.who_seller == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    await c.message.reply(
        text=convert.cv(605, user).format(nickname_user=other_user.info_user()),
        reply_markup=kb_user.btn_cancel(user=user))
    return


@router_deal.message(F.chat.type == 'private', DealState.send_message_deal)
async def send_message_deal(m: Message, user: Users, state: FSMContext):

    data = await state.get_data()
    deal_uniq_id = data['deal_uniq_id']

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    if deal.status != StatusDeal.active:
        return

    if not m.text and not m.caption:
        return await m.answer(text=convert.cv(611, user))

    my_message = m.text if m.text else m.caption
    my_message = re.sub(r'[<>#]', '', my_message)
    if not my_message:
        return await m.answer(text=convert.cv('empty message', user))

    if deal.who_seller == user.user_id:
        user_him: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        user_him: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    now = datetime.datetime.now()
    await Chat.aio_create(
        uniq_id_deal=deal.uniq_id,
        user_id=user.user_id,
        text=my_message,
        created=now)

    try:
        await m.bot.send_message(
            chat_id=user_him.user_id,
            text=convert.cv(612, user).format(
                nickname_user=user_him.info_user(),
                uniq_id=deal.uniq_id,
                message=my_message
            ),
            reply_markup=kb_user.btn_answer_message(user=user, deal_uniq_id=deal.uniq_id))
    except:
        logger.error(f'Error send a new message to {user_him.user_id}', exc_info=True)
        await m.answer(text=convert.cv(613, user))
        return

    await m.answer(text=convert.cv(614, user))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'getConfirmDeal')
async def get_confirm_deal(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    try:
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).aio_get()
    except Deals.DoesNotExist:
        return await c.answer(text=convert.cv(606, user), show_alert=True)

    if deal.who_seller == user.user_id and deal.confirm_seller == True:
        return await c.answer(text=convert.cv(617, user), show_alert=True)
    elif deal.who_buyer == user.user_id and deal.confirm_buyer == True:
        return await c.answer(text=convert.cv(617, user), show_alert=True)

    who_seller_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
    who_buyer_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

    await c.message.edit_text(
        text=convert.cv(610, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.confirmation_about_confirm_deal(user=user, deal_uniq_id=deal.uniq_id))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'confirmDeal')
async def click_confirm_deal(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    async with database.aio_atomic():
        try:
            deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        except Deals.DoesNotExist:
            logger.error(f'[confirmDeal] Сделка не найдена! uniq_id={deal_uniq_id}')
            return await c.answer(text=convert.cv(606, user), show_alert=True)

        if deal.cancel_seller or deal.cancel_buyer:
            return await c.answer("❌ Одна из сторон уже инициировала отмену сделки. Завершить сделку невозможно.", show_alert=True)
        elif deal.status == StatusDeal.closed:
            return await c.answer(text=convert.cv(607, user), show_alert=True)
        elif deal.status == StatusDeal.active and deal.who_open_disput is not None:
            return await c.answer(text=convert.cv(608, user), show_alert=True)
        await c.answer(text='📬', cache_time=60)

        if deal.who_seller == user.user_id:
            deal.confirm_seller = True
            try:
                other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
            except Users.DoesNotExist:
                return await c.answer(text=convert.cv(606, user), show_alert=True)
        else:
            deal.confirm_buyer = True
            try:
                other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
            except Users.DoesNotExist:
                return await c.answer(text=convert.cv(606, user), show_alert=True)
        await deal.aio_save()

        try:
            who_seller_user: Users = await Users.select().where(Users.user_id == deal.who_seller).for_update().aio_get()
            who_buyer_user: Users = await Users.select().where(Users.user_id == deal.who_buyer).for_update().aio_get()
        except Users.DoesNotExist:
            return await c.answer(text=convert.cv(606, user), show_alert=True)

        if deal.confirm_seller == True and deal.confirm_buyer == True:
            deal.status = StatusDeal.closed
            deal.end_time = datetime.datetime.now()
            await deal.aio_save()

            final_amount = deal.price

            old_balance = who_seller_user.balance
            who_seller_user.balance += final_amount
            await who_seller_user.aio_save()

            logger.info(
                f'user: {who_seller_user.user_id} success confirm deal.\n'
                f'{" " * 14}{old_balance=} -> {who_seller_user.balance}\n'
                f'{" " * 14}{deal.uniq_id=}\n'
                f'{" " * 14}{deal.price=}$ (full amount, commission will be charged on withdrawal)')

            try:
                answer = await c.bot.send_message(
                    chat_id=who_buyer_user.user_id,
                    text=convert.cv(666, who_buyer_user).format(
                        deal_uniq_id=deal.uniq_id,
                        seller_info=who_seller_user.info_user(),
                        buyer_info=who_buyer_user.info_user(),
                        nickname_user=who_seller_user.info_user()
                    ),
                    reply_markup=get_review_keyboard(deal_uniq_id))
                await answer.reply(text=convert.cv(36, who_seller_user).format(amount=final_amount))
            except:
                logger.error(f'Error send about success Deal to {who_buyer_user.user_id}', exc_info=True)

            try:
                await c.bot.send_message(
                    chat_id=who_seller_user.user_id,
                    text=convert.cv(666, who_seller_user).format(
                        deal_uniq_id=deal.uniq_id,
                        seller_info=who_seller_user.info_user(),
                        buyer_info=who_buyer_user.info_user(),
                        nickname_user=who_buyer_user.info_user()
                    ),
                    reply_markup=get_review_keyboard(deal_uniq_id))
            except:
                logger.error(f'Error send about success Deal to {who_seller_user.user_id}', exc_info=True)

            await send_log(
                message=f'✅ Сделка #{deal.uniq_id} успешно завершена\n\n'
                        f'<u>Продавец:</u> {who_seller_user.info_user()}\n'
                        f'Покупатель: {who_buyer_user.info_user()}\n\n'
                        f'Сумма сделки: {deal.price:.2f}$\n'
                        f'Получено продавцом: {final_amount:.2f}$ (полная сумма)\n'
                        f'Комиссия будет списана при выводе средств\n'
                        f'Баланс продавца: {who_seller_user.balance:.2f}$')
            return

    try:
        await c.bot.send_message(
            chat_id=other_user.user_id,
            text=convert.cv(610, other_user).format(
                uniq_id=deal.uniq_id,
                who_seller_nickname=who_seller_user.info_user(),
                who_buyer_nickname=who_buyer_user.info_user(),
                amount=float(deal.price),
                description=deal.description),
            reply_markup=kb_user.panel_deal(user=other_user, deal=deal.uniq_id, confirm=False))
    except:
        logger.error(f'Error send about confirm Deal to {other_user.user_id}', exc_info=True)
        await c.message.answer(text=convert.cv(618, user), reply_markup=kb_user.btn_hide(user=user))
        return

    await c.message.edit_text(
        text=convert.cv(600, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.panel_deal(user=user, deal=deal.uniq_id, confirm=False))

    await c.message.reply(text=convert.cv(615, user).format(
        uniq_id=deal.uniq_id,
        smile_time=get_random_smile('time'),
        nickname_user=other_user.info_user()
    ))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'backToDeal')
async def back_to_deal_menu(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    who_seller_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
    who_buyer_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

    if deal.status == StatusDeal.wait_confirm:

        if deal.who_seller == user.user_id:
            other_user = who_buyer_user
            who_im_in_deal = convert.cv('seller', other_user)
            who_him_in_deal = convert.cv('purchaser', other_user)
        else:
            other_user = who_seller_user
            who_im_in_deal = convert.cv('purchaser', other_user)
            who_him_in_deal = convert.cv('seller', other_user)

        if deal.who_start_deal == user.user_id:
            await c.message.edit_text(
                text=convert.cv(513, user).format(
                    uniq_id=deal.uniq_id,
                    nickname_user_2=other_user.info_user()
                ),
                reply_markup=kb_user.cancel_deal(user=user, deal_uniq_id=deal.uniq_id))
            return
        else:
            await c.message.edit_text(
                chat_id=other_user.user_id,
                text=convert.cv(512, other_user).format(
                    uniq_id=deal.uniq_id,
                    from_user_info=user.info_user(),
                    from_user_id=user.user_id,
                    who_im_in_deal=who_him_in_deal,
                    who_him_in_deal=who_im_in_deal,
                    amount=float(deal.price),
                    description=deal.description
                ),
                reply_markup=kb_user.accept_or_decline_deal(user=other_user, deal_uniq_id=deal.uniq_id))
            return

    if deal.who_seller == user.user_id and deal.confirm_seller == True:
        confirm_deal = True
    elif deal.who_buyer == user.user_id and deal.confirm_buyer == True:
        confirm_deal = True
    else:
        confirm_deal = False

    await c.message.edit_text(
        text=convert.cv(600, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.panel_deal(user=user, deal=deal.uniq_id, confirm=confirm_deal))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'leaveFeedback')
async def leave_feedback(c: types.CallbackQuery, user: Users, state: FSMContext):
    deal_uniq_id = c.data.split("_")[1]

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    if deal.who_seller == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    try:
        _: Reviews = await Reviews.aio_get(
            (Reviews.deal_uniq_id == deal_uniq_id) &
            (Reviews.from_user_id == user.user_id))
        await c.answer(text=convert.cv(621, user).format(nickname_user=other_user.info_user()), show_alert=True)
        return
    except Reviews.DoesNotExist:
        await c.answer()
        await c.message.answer(
            text=convert.cv(622, user).format(nickname_user=other_user.info_user()),
            reply_markup=kb_user.set_stars_review(user=user, deal_uniq_id=deal.uniq_id))
        return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'setStarsReview')
async def set_stars_review(c: types.CallbackQuery, user: Users, state: FSMContext):

    data = c.data.split('_')
    rating = data[1]
    deal_uniq_id = data[2]

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    if deal.who_seller == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    await state.set_state(ReviewState.review_write_comment)
    await state.update_data(rating=rating, deal_uniq_id=deal_uniq_id)

    await c.message.edit_text(
        text=convert.cv(623, user).format(nickname_user=other_user.info_user()),
        reply_markup=kb_user.btn_cancel(user=user))
    return


@router_deal.message(F.chat.type == 'private', ReviewState.review_write_comment)
async def write_comment_review(m: Message, user: Users, state: FSMContext):

    if not m.text and not m.caption:
        return await m.answer(text=convert.cv(624, user))

    my_message = m.text if m.text else m.caption
    my_message = re.sub(r'[<>#]', '', my_message)
    if not my_message:
        return await m.answer(text=convert.cv('empty message', user))

    data = await state.get_data()
    rating = data['rating']
    deal_uniq_id = data['deal_uniq_id']

    deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
    if deal.who_seller == user.user_id:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    else:
        other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

    try:
        _: Reviews = await Reviews.aio_get(
            (Reviews.deal_uniq_id == deal_uniq_id) &
            (Reviews.from_user_id == user.user_id))
        await m.answer(text=convert.cv(621, user).format(nickname_user=other_user.info_user()))
        return
    except Reviews.DoesNotExist:
        await state.clear()

        await Reviews.aio_create(
            deal_uniq_id=deal.uniq_id,
            rating=int(rating),
            from_user_id=user.user_id,
            to_user_id=other_user.user_id,
            message=my_message,
            created=datetime.datetime.now())

        await m.answer(
            text=convert.cv(625, user).format(nickname_user=other_user.info_user()),
            reply_markup=kb_user.btn_menu(user=user))
        return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'getCancelDeal')
async def get_cancel_deal(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    try:
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).aio_get()
    except Deals.DoesNotExist:
        return await c.answer(text=convert.cv(606, user), show_alert=True)

    if deal.status == StatusDeal.canceled:
        return await c.answer(text=convert.cv(606, user), show_alert=True)
    elif deal.status == StatusDeal.closed:
        return await c.answer(text=convert.cv(607, user), show_alert=True)
    elif deal.status == StatusDeal.active and deal.who_open_disput is not None:
        return await c.answer(text=convert.cv(608, user), show_alert=True)

    if deal.who_seller == user.user_id and deal.cancel_seller == True:
        return await c.answer(text=convert.cv(636, user), show_alert=True)
    elif deal.who_buyer == user.user_id and deal.cancel_buyer == True:
        return await c.answer(text=convert.cv(636, user), show_alert=True)

    await c.message.edit_text(
        text=convert.cv(627, user).format(uniq_id=deal.uniq_id),
        reply_markup=kb_user.confirmation_cancel_deal(user=user, deal_uniq_id=deal.uniq_id))
    return


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'cancelDeal')
async def click_cancel_deal(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    async with database.aio_atomic():
        try:
            deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        except Deals.DoesNotExist:
            return await c.answer(text=convert.cv(606, user), show_alert=True)

        if deal.status == StatusDeal.canceled:
            return await c.answer(text=convert.cv(606, user), show_alert=True)
        elif deal.status == StatusDeal.closed:
            return await c.answer(text=convert.cv(607, user), show_alert=True)
        elif deal.status == StatusDeal.active and deal.who_open_disput is not None:
            return await c.answer(text=convert.cv(608, user), show_alert=True)
        await c.answer(text='📬', cache_time=60)

        if deal.who_seller == user.user_id:
            deal.cancel_seller = True
            try:
                other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
            except Users.DoesNotExist:
                return await c.answer(text=convert.cv(606, user), show_alert=True)
        else:
            deal.cancel_buyer = True
            try:
                other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
            except Users.DoesNotExist:
                return await c.answer(text=convert.cv(606, user), show_alert=True)
        await deal.aio_save()

        try:
            who_seller_user: Users = await Users.select().where(Users.user_id == deal.who_seller).for_update().aio_get()
            who_buyer_user: Users = await Users.select().where(Users.user_id == deal.who_buyer).for_update().aio_get()
        except Users.DoesNotExist:
            return await c.answer(text=convert.cv(606, user), show_alert=True)

        if deal.cancel_seller == True and deal.cancel_buyer == True:
            deal.status = StatusDeal.canceled
            deal.end_time = datetime.datetime.now()
            await deal.aio_save()

            old_balance = who_buyer_user.balance
            who_buyer_user.balance += deal.price
            await who_buyer_user.aio_save()

            logger.info(
                f'user: {who_seller_user.user_id} success cancel deal.\n'
                f'{" " * 14}{old_balance=} -> {who_buyer_user.balance}\n'
                f'{" " * 14}{deal.uniq_id=}\n'
                f'{" " * 14}{deal.price=}$')

            try:
                answer = await c.bot.send_message(
                    chat_id=who_buyer_user.user_id,
                    text=f'❌ Сделка #{deal.uniq_id} обоюдно отменена\n\n'
                         f'Продавец: {who_seller_user.info_user()}\n'
                         f'Покупатель: {who_buyer_user.info_user()}\n\n'
                         f'Баланс покупателя: {who_seller_user.balance:.2f}',
                    reply_markup=kb_user.btn_menu(user=who_buyer_user))
                await answer.reply(text=convert.cv(36, who_seller_user).format(amount=float(deal.price)))
            except:
                logger.error(f'Error send about success Deal to {who_buyer_user.user_id}', exc_info=True)

            try:
                await c.bot.send_message(
                    chat_id=who_seller_user.user_id,
                    text=f'❌ Сделка #{deal.uniq_id} обоюдно отменена\n\n'
                         f'Продавец: {who_seller_user.info_user()}\n'
                         f'Покупатель: {who_buyer_user.info_user()}\n\n'
                         f'Баланс покупателя: {who_seller_user.balance:.2f}',
                    reply_markup=kb_user.btn_menu(user=who_seller_user))
            except:
                logger.error(f'Error send about success Deal to {who_seller_user.user_id}', exc_info=True)

            await send_log(
                message=f'❌ Сделка #{deal.uniq_id} обоюдно отменена\n\n'
                        f'<u>Продавец:</u> {who_seller_user.info_user()}\n'
                        f'Покупатель: {who_buyer_user.info_user()}\n\n'
                        f'Баланс покупателя: {who_seller_user.balance:.2f}')
            return

    try:
        await c.bot.send_message(
            chat_id=other_user.user_id,
            text=convert.cv(629, other_user).format(
                uniq_id=deal.uniq_id,
                who_seller_nickname=who_seller_user.info_user(),
                who_buyer_nickname=who_buyer_user.info_user(),
                amount=float(deal.price),
                description=deal.description),
            reply_markup=kb_user.panel_deal(user=other_user, deal=deal.uniq_id, confirm=False))
    except:
        logger.error(f'Error send about cancel Deal to {other_user.user_id}', exc_info=True)
        await c.message.answer(text=convert.cv(618, user), reply_markup=kb_user.btn_hide(user=user))
        return

    await c.message.edit_text(
        text=convert.cv(600, user).format(
            uniq_id=deal.uniq_id,
            who_seller_nickname=who_seller_user.info_user(),
            who_buyer_nickname=who_buyer_user.info_user(),
            amount=deal.price,
            description=deal.description
        ),
        reply_markup=kb_user.panel_deal(user=user, deal=deal.uniq_id, confirm=False))

    await c.message.reply(text=convert.cv(630, user).format(
        uniq_id=deal.uniq_id,
        smile_time=get_random_smile('time'),
        nickname_user=other_user.info_user()
    ))
    return


@router_deal.callback_query(lambda cb: cb.data.startswith('review_'))
async def process_review(callback: CallbackQuery, user: Users):
    try:
        _, rating, deal_uniq_id = callback.data.split('_')
        rating = int(rating)

        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).aio_get()
        if not deal:
            return await callback.answer(text=convert.cv(606, user), show_alert=True)

        if await Reviews.has_review(deal_uniq_id, user.user_id):
            return await callback.answer(text=convert.cv(602, user), show_alert=True)

        who_seller_user = await Users.aio_get(Users.user_id == deal.who_seller)
        who_buyer_user = await Users.aio_get(Users.user_id == deal.who_buyer)
        await callback.message.edit_text(
            convert.cv(675, user).format(
                deal_uniq_id=deal.uniq_id,
                seller_info=who_seller_user.info_user(),
                buyer_info=who_buyer_user.info_user()
            )
        )
        await callback.answer(text=convert.cv(626, user), show_alert=True)

    except Exception as e:
        logger.error(f"Error in process_review: {e}")
        await callback.answer(text=convert.cv(671, user), show_alert=True)

def get_review_keyboard(deal_uniq_id: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for i in range(1, 6):
        row.append(InlineKeyboardButton(
            text=f"{i}⭐️",
            callback_data=f"review_{i}_{deal_uniq_id}"
        ))
    keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router_deal.callback_query(lambda cb: cb.data.split("_")[0] == 'openDisputDeal')
async def open_disput_deal(c: types.CallbackQuery, user: Users, state: FSMContext):
    deal_uniq_id = c.data.split("_")[1]

    async with database.aio_atomic():
        try:
            deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        except Deals.DoesNotExist:
            return await c.answer(text=convert.cv(606, user), show_alert=True)

        if deal.status == StatusDeal.canceled:
            return await c.answer(text=convert.cv(606, user), show_alert=True)
        elif deal.status == StatusDeal.closed:
            return await c.answer(text=convert.cv(632, user), show_alert=True)
        elif deal.who_open_disput is not None:
            who_opened: Users = await Users.aio_get(Users.user_id == deal.who_open_disput)
            return await c.answer(text=convert.cv(633, user).format(nickname_user=who_opened.info_user()), show_alert=True)
        await c.answer()

        if deal.who_seller == user.user_id:
            other_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
        else:
            other_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)

        await state.set_state(DealState.write_message_disput)
        await state.update_data(deal_uniq_id=deal.uniq_id)
        await c.message.reply(
            text=convert.cv(631, user).format(nickname_user=other_user.info_user()),
            reply_markup=kb_user.btn_cancel(user=user))
        return

@router_deal.message(F.chat.type == 'private', DealState.write_message_disput)
async def write_message_disput(m: Message, user: Users, state: FSMContext):
    data = await state.get_data()
    deal_uniq_id = data['deal_uniq_id']

    async with database.aio_atomic():
        try:
            deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        except Deals.DoesNotExist:
            await state.clear()
            return await m.answer(text=convert.cv(606, user), reply_markup=kb_user.btn_hide(user=user))

        if deal.status == StatusDeal.canceled:
            await state.clear()
            return await m.answer(text=convert.cv(606, user), reply_markup=kb_user.btn_hide(user=user))
        elif deal.status == StatusDeal.closed:
            await state.clear()
            return await m.answer(text=convert.cv(632, user), reply_markup=kb_user.btn_hide(user=user))
        elif deal.who_open_disput is not None:
            who_opened: Users = await Users.aio_get(Users.user_id == deal.who_open_disput)
            await state.clear()
            return await m.answer(
                text=convert.cv(633, user).format(nickname_user=who_opened.info_user()),
                reply_markup=kb_user.btn_hide(user=user))

        deal.who_open_disput = user.user_id
        deal.description_complaint = m.text
        await deal.aio_save()

        await state.clear()

        who_seller: Users = await Users.aio_get(Users.user_id == deal.who_seller)
        who_buyer: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

        await send_log(
            f'⚠️ Открыт спор по сделке #{deal.uniq_id}\n\n'
            f'Продавец: {who_seller.more_info_user()}\n'
            f'Покупатель: {who_buyer.more_info_user()}\n\n'
            f'Причина: {m.text}')

        try:
            await bot_main.send_message(
                chat_id=config['CHATS_ID']['logs'],
                text=f'Действия для спора #{deal.uniq_id}:',
                reply_markup=kb_admin.accept_disput(deal_uniq_id=deal.uniq_id))
        except Exception as e:
            logger.error(f'Failed to send dispute action buttons: {e}')

        if deal.who_seller == user.user_id:
            other_user = who_buyer
        else:
            other_user = who_seller

        try:
            await m.bot.send_message(
                chat_id=other_user.user_id,
                text=convert.cv(634, other_user).format(
                    nickname_user=user.info_user(),
                    deal_uniq_id=deal.uniq_id))
        except:
            logger.error(f'Error send about open disput to {other_user.user_id}', exc_info=True)

        await m.answer(
            text=convert.cv(635, user).format(
                deal_uniq_id=deal.uniq_id),
            reply_markup=kb_user.btn_hide(user=user))
        return
