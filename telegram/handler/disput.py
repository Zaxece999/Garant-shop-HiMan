import datetime

from aiogram.fsm.context import FSMContext
from aiogram import F, Router, types

from telegram.functions.func import send_log
from additional.functions import is_url, get_random_smile
from telegram.misc.states import AdminState
from tables.deals import StatusDeal
from init import *


router_disput = Router()


@router_disput.callback_query(lambda cb: cb.data.split("_")[0] == 'acceptDisput')
async def accept_disput_admin(c: types.CallbackQuery, user: Users, state: FSMContext):
    if not c.from_user.username:
        return await c.answer(text=convert.cv(44), show_alert=True)

    deal_uniq_id = c.data.split('_')[1]

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.admin_disput is not None:
            who_taked: Users = await Users.aio_get(Users.user_id == deal.admin_disput)
            await c.answer(text=convert.admin_text(41).format(nickname_admin=who_taked.more_info_user()), show_alert=True)
            return
        await c.answer()

        deal.admin_disput = user.user_id
        await deal.aio_save()

        me = await c.bot.me()
        link_to_go_complaint = f'https://t.me/{me.username}?start=complaint_{deal.uniq_id}'

        await c.message.edit_reply_markup(
            reply_markup=kb_admin.go_to_complaint(
                username=c.from_user.username,
                link_to_go=link_to_go_complaint))

        return


@router_disput.callback_query(lambda cb: cb.data.split("_")[0] == "sendLinkChatDisput")
async def send_link_chat_disput(c: types.CallbackQuery, user: Users, state: FSMContext):
    deal_uniq_id = c.data.split("_")[1]

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.status == StatusDeal.closed:
            return await c.answer(text=convert.admin_text(45), show_alert=True, cache_time=3)
        await c.answer()

        await state.set_state(AdminState.enter_link_for_chat)
        await state.update_data(deal_uniq_id=deal_uniq_id)
        await c.message.answer(
            text=convert.admin_text(46),
            reply_markup=kb_admin.btn_cancel(user=user))
        return


@router_disput.message(F.chat.type == 'private', AdminState.enter_link_for_chat)
async def send_link_for_chat(m: types.Message, user: Users, state: FSMContext):
    data = await state.get_data()
    deal_uniq_id = data['deal_uniq_id']

    link = m.text
    if is_url(link) is False:
        await m.reply(
            text=convert.admin_text(46),
            reply_markup=kb_admin.btn_cancel(user=user))
        return

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.status == StatusDeal.closed:
            await state.clear()
            await m.answer(text=convert.admin_text(45), reply_markup=kb_user.btn_hide(user=user))
            return

        who_seller: Users = await Users.aio_get(Users.user_id == deal.who_seller)
        who_buyer: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

        try:
            await m.bot.send_message(
                chat_id=who_seller.user_id,
                text=convert.cv(1000, who_seller).format(link=link, deal_uniq_id=deal.uniq_id))
        except:
            logger.error(f'Error send the link to {deal.who_seller}', exc_info=True)

        try:
            await m.bot.send_message(
                chat_id=who_buyer.user_id,
                text=convert.cv(1000, who_buyer).format(link=link, deal_uniq_id=deal.uniq_id))
        except:
            logger.error(f'Error send the link to {deal.who_buyer}', exc_info=True)

        await state.clear()
        await m.answer(text=convert.admin_text(47))
        return


@router_disput.callback_query(lambda cb: cb.data.split("_")[0] == 'getCloseDisput')
async def get_close_disput(c: types.CallbackQuery, user: Users):
    deal_uniq_id = c.data.split('_')[1]

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.status == StatusDeal.closed:
            return await c.answer(text=convert.admin_text(45), show_alert=True, cache_time=3)
        await c.answer()

        who_seller: Users = await Users.aio_get(Users.user_id == deal.who_seller)
        who_buyer: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

        await c.message.edit_text(
            text=convert.admin_text(48).format(
                who_seller=who_seller.more_info_user(),
                who_buyer=who_buyer.more_info_user()
            ),
            reply_markup=kb_admin.close_disput(deal_uniq_id=deal_uniq_id))
        return


@router_disput.callback_query(lambda cb: cb.data.split("_")[0] == 'closeDisput')
async def get_close_disput(c: types.CallbackQuery, user: Users):
    data = c.data.split('_')

    deal_uniq_id = data[1]

    async with database.aio_atomic():
        deal: Deals = await Deals.select().where(Deals.uniq_id == deal_uniq_id).for_update().aio_get()
        if deal.status == StatusDeal.closed:
            return await c.answer(text=convert.admin_text(45), show_alert=True, cache_time=3)
        await c.answer()

        who_win_disput = data[2]

        who_seller_user: Users = await Users.select().where(Users.user_id == deal.who_seller).for_update().aio_get()
        who_buyer_user: Users = await Users.select().where(Users.user_id == deal.who_buyer).for_update().aio_get()
        if who_win_disput == 'seller':
            who_win_disput = who_seller_user
        else:
            who_win_disput = who_buyer_user

        deal.who_win_disput = who_win_disput.user_id
        deal.status = StatusDeal.closed
        deal.end_time = datetime.datetime.now()
        await deal.aio_save()

        result = deal.amount_to_credited(percent_disput=config.getfloat('PRICES', 'percent_disput'))

        if deal.who_win_disput == deal.who_seller:
            who_win_user = who_seller_user

            old_balance = who_seller_user.balance
            who_seller_user.balance += result['final_amount']
            await who_seller_user.aio_save()
        else:
            who_win_user = who_buyer_user

            old_balance = who_buyer_user.balance
            who_buyer_user.balance += result['final_amount']
            await who_buyer_user.aio_save()

        logger.info(
            f'user: {who_win_user.user_id} success close disput deal.\n'
            f'{" " * 14}{old_balance=} -> {who_win_user.balance}\n'
            f'{" " * 14}{deal.uniq_id=}\n'
            f'{" " * 14}{result}')

        try:
            await c.bot.send_message(
                chat_id=who_seller_user.user_id,
                text=convert.cv(1001, user).format(
                    deal_uniq_id=deal.uniq_id,
                    who_win_disput_user=who_win_user.info_user()))
        except:
            logger.error(f'Error send about close disput to {who_seller_user.user_id}', exc_info=True)

        try:
            await c.bot.send_message(
                chat_id=who_buyer_user.user_id,
                text=convert.cv(1001, user).format(
                    deal_uniq_id=deal.uniq_id,
                    who_win_disput_user=who_win_user.info_user()))
        except:
            logger.error(f'Error send about close disput to {who_buyer_user.user_id}', exc_info=True)

        try:
            await c.bot.send_message(
                chat_id=who_win_user.user_id,
                text=convert.cv(620, who_win_user).format(
                    smile_money=get_random_smile('money'),
                    uniq_id=deal.uniq_id,
                    **result))
        except:
            logger.error(f'Error send about add money to {who_win_user.user_id}', exc_info=True)

        await send_log(
            message=f'⚠️ Админ {user.info_user()} закрыл спор #{deal.uniq_id}\n\n'
                    f'Закрыто в пользу -> {who_win_user.more_info_user()}')

        await c.message.edit_text(text=convert.admin_text(49))
        return
