import datetime
import logging
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router

from additional.functions import get_random_smile, generate_random_string
from telegram.functions.func import send_log
from telegram.misc.states import UserState
from tables import *
from init import *


logger = logging.getLogger('CS1')


router_withdrawal = Router()


@router_withdrawal.message(F.chat.type == 'private', UserState.withdrawal_amount)
async def enter_withdrawal_amount(m: Message, user: Users, state: FSMContext):

    try:
        amount = round(float(m.text), 2)

        min_withdrawal = config.getfloat('GARANT', 'min_withdrawal')
        if amount < min_withdrawal:
            await m.answer(text=convert.cv(803, user).format(min_withdrawal=min_withdrawal))
            return
    except ValueError:
        await m.answer(text=convert.cv(802, user), reply_markup=kb_user.btn_menu(user=user))
        return

    if user.balance < amount:
        await m.answer(text=convert.cv(804, user).format(
            smile_money=get_random_smile('money'),
            balance=user.balance
        ))
        return

    await state.clear()

    percent_amount_service = round(amount * config.getfloat('PRICES', 'percent_service'), 2)
    amount_after_commission = amount - percent_amount_service

    await m.answer(
        text=convert.cv(805, user).format(amount=amount_after_commission, percent_amount_service=percent_amount_service),
        reply_markup=kb_user.select_method_withdrawal(user=user, amount=amount_after_commission))
    return


@router_withdrawal.callback_query(lambda cb: cb.data.split("_")[0] == 'withdrawalMethod')
async def select_method_withdrawal(c: CallbackQuery, user: Users, state: FSMContext):
    data = c.data.split('_')

    if len(data) == 4 and data[1] == 'usdt' and (data[2] == 'bep20' or data[2] == 'erc20'):
        method = f"{data[1]}_{data[2]}"
        amount = round(float(data[3]), 2)
    else:
        method = data[1]
        amount = round(float(data[2]), 2)

    await state.update_data(withdrawal_method=method, withdrawal_amount=amount)
    await state.set_state(UserState.withdrawal_wallet)

    await c.answer()
    await c.message.edit_text(
        text=convert.cv(2044, user),
        reply_markup=kb_user.btn_cancel(user=user))


@router_withdrawal.message(F.chat.type == 'private', UserState.withdrawal_wallet)
async def enter_wallet_address(m: Message, user: Users, state: FSMContext):
    wallet_address = m.text.strip()

    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        await m.answer(
            text=convert.cv(2041, user),
            reply_markup=kb_user.btn_cancel(user=user))
        return

    data = await state.get_data()
    method = data.get('withdrawal_method')
    amount = data.get('withdrawal_amount')

    if not method or not amount:
        await m.answer(text=convert.cv(2042, user), reply_markup=kb_user.btn_menu(user=user))
        await state.clear()
        return

    async with database.aio_atomic():
        user: Users = await Users.select().where(Users.user_id == user.user_id).for_update().aio_get()

        percent_service = config.getfloat('PRICES', 'percent_service')
        total_amount = round(amount / (1 - percent_service), 2)

        if user.balance < total_amount:
            return await m.answer(text=convert.cv(806, user), reply_markup=kb_user.btn_menu(user=user))

        user.balance -= total_amount
        await user.aio_save()

        random_number = str(random.randint(0, 9999)).zfill(4)
        uniq_id = f'w{generate_random_string(length=3)}{random_number}'
        new_withdrawal: Withdrawal = await Withdrawal.aio_create(
            user_id=user.user_id,
            uniq_id=uniq_id,
            amount=amount,
            method=method,
            wallet_address=wallet_address,
            created=datetime.datetime.now())

        await m.bot.send_message(
            chat_id=config['CHATS_ID']['withdrawal'],
            text=convert.cv(2014, user).format(withdrawal_id=new_withdrawal.uniq_id) +
                 f"👤 Пользователь: {user.more_info_user()}\n"
                 f"💰 Сумма: {new_withdrawal.amount} USD\n"
                 f"🔄 Метод: USDT {'BEP20' if method == 'usdt_bep20' else 'ERC20'}\n"
                 f"📝 Адрес: <code>{wallet_address}</code>",
            reply_markup=kb_admin.status_withdrawal(user_id=user.user_id, withdrawal_id=new_withdrawal.id, success=False))

        await state.clear()
        await m.answer(
            text=convert.cv(807, user).format(
                uniq_id=new_withdrawal.uniq_id,
                amount=new_withdrawal.amount,
                smile_time=get_random_smile('time')))
        return


@router_withdrawal.callback_query(lambda cb: cb.data.startswith('withdrawal_'))
async def process_withdrawal_status(c: CallbackQuery, user: Users):
    data = c.data.split('_')
    if len(data) != 3:
        await c.answer("Некорректный формат данных", show_alert=True)
        return

    user_id = data[1]
    withdrawal_id = int(data[2])

    try:
        withdrawal = await Withdrawal.aio_get(Withdrawal.id == withdrawal_id)
        target_user = await Users.aio_get(Users.user_id == user_id)

        try:
            wallet_address = withdrawal.wallet_address
            if wallet_address is None or wallet_address == '':
                wallet_address = "Не указан"
        except (AttributeError, Exception):
            wallet_address = "Не указан"
            logger.warning(f"У вывода {withdrawal_id} отсутствует поле wallet_address")

        await c.message.edit_reply_markup(
            reply_markup=kb_admin.status_withdrawal(
                user_id=user_id,
                withdrawal_id=withdrawal_id,
                success=True
            )
        )

        await c.bot.send_message(
            chat_id=target_user.user_id,
            text=convert.cv(2015, target_user) +
                 f"💰 Сумма: {withdrawal.amount} USD\n"
                 f"🔄 Метод: {withdrawal.method}\n\n",
            reply_markup=kb_user.btn_menu(user=target_user)
        )

        await c.answer("Статус выплаты обновлен, уведомление отправлено пользователю")
        await send_log(f"👤 Администратор {user.more_info_user()} отметил вывод #{withdrawal.uniq_id} для {target_user.more_info_user()} как выплаченный")

    except (Withdrawal.DoesNotExist, Users.DoesNotExist) as e:
        logger.error(f"Ошибка при обработке статуса вывода: {e}")
        await c.answer("Ошибка: Не удалось найти данные о выводе или пользователе", show_alert=True)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при обработке статуса вывода: {e}", exc_info=True)
        await c.answer("Произошла ошибка при обработке запроса", show_alert=True)


@router_withdrawal.message(F.chat.id == int(config['CHATS_ID']['withdrawal']))
async def enter_receipt_withdrawal(m: Message, user: Users):
    return

    if not m.reply_to_message:
        answer = await m.reply(text=convert.admin_text(51))
        await asyncio.sleep(10)
        await answer.delete()
        await m.delete()
        return

    try:
        callback_data = m.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data

        if callback_data.startswith('withdrawal_'):
            parts = callback_data.split('_')
            user_id = parts[1]
        else:
            user_id = callback_data

        other_user: Users = await Users.aio_get(Users.user_id == user_id)
        await m.bot.send_message(
            chat_id=other_user.user_id,
            text=convert.cv(808, other_user).format(link=m.text))

        if not callback_data.startswith('withdrawal_'):
            await m.reply_to_message.edit_reply_markup(
                reply_markup=kb_admin.status_withdrawal(user_id=user_id, success=True))

    except Exception as e:
        logger.error(f'Error send receipt to user: {e}', exc_info=True)

    return
