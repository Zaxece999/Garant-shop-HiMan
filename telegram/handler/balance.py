import logging
import random

from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F, Router

from telegram.misc.states import RefillBalance
from telegram.functions.func import *
from additional.functions import *
from tables import *
from init import *
from re import *


logger = logging.getLogger('CS1')


router_balance = Router()


@router_balance.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='refill balance')))
async def menu_refill_balance(m: Message, user: Users, state: FSMContext):

    answer = await m.answer(
        text=convert.cv(30, user).format(
            smile_money=get_random_smile('money'),
            balance=round(user.balance, 2)),
        reply_markup=kb_user.refill_balance(user))

    await state.set_state(RefillBalance.enter_amount)
    await state.update_data(old_message_id=answer.message_id)

    return


@router_balance.message(F.chat.type == 'private', RefillBalance.enter_amount)
async def enter_amount_balance(m: Message, user: Users, state: FSMContext):
    try:
        amount = float(m.text)
    except (ValueError, TypeError):
        answer = await m.reply(text=convert.cv(31, user))
        loop.create_task(auto_delete_messages([answer], 5))
        return

    if amount <= 0:
        return await m.answer(text=convert.cv('amount is low', user))

    await state.clear()
    await state.update_data(amount=amount)
    await m.answer(text=convert.cv(32, user), reply_markup=kb_user.choice_merchant_top_up(user=user, amount=amount))
    return


@router_balance.message(F.chat.type == 'private', RefillBalance.enter_nick_transfer)
async def enter_nick_transfer(m: Message, user: Users, state: FSMContext):
    user_id = m.text.strip()

    if user_id == str(user.user_id):
        return await m.answer(text=convert.cv(405, user))

    try:
        get_user: Users = await Users.aio_get(Users.user_id == user_id)
    except Users.DoesNotExist:
        return await m.answer(text=convert.cv(402, user), reply_markup=kb_user.btn_cancel(user))

    if user.balance <= 0:
        return await m.answer(
            text=convert.cv(400, user).format(smile_money=get_random_smile('money')),
            reply_markup=kb_user.btn_menu(user))

    data = await state.get_data()
    send_money = data['amount_transfer']

    random_number = str(random.randint(0, 9999)).zfill(4)
    transfer_id = f't{generate_random_string(length=3)}{random_number}'

    async with database.aio_atomic():
        await Users.update(balance=Users.balance - send_money).where(Users.id == user.id).aio_execute()
        await Users.update(balance=Users.balance + send_money).where(Users.id == get_user.id).aio_execute()

    await send_log(f'🏦 Перевод #{transfer_id}: {user.more_info_user()} перевел {send_money}$ пользователю {get_user.more_info_user()}')

    await state.clear()
    await m.answer(
        text=convert.cv(403, user).format(transfer_id=transfer_id, amount=send_money),
        reply_markup=kb_user.btn_menu(user=user))

    try:
        await m.bot.send_message(
            chat_id=get_user.user_id,
            text=convert.cv(404, get_user).format(amount=send_money, nickname=user.nickname, transfer_id=transfer_id),
            reply_markup=kb_user.btn_hide(user=get_user))
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о переводе: {e}")


@router_balance.callback_query(lambda cb: cb.data == 'topUpHeleket')
async def top_up_heleket_start(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer(cache_time=3)

    state_data = await state.get_data()
    amount = state_data.get('amount')

    await state.set_state(RefillBalance.choose_currency)
    await state.update_data(amount=amount)

    await c.bot.edit_message_text(
        text=convert.cv(2031, user),
        chat_id=c.from_user.id,
        message_id=c.message.message_id,
        reply_markup=kb_user.choose_heleket_currency(user))


@router_balance.callback_query(lambda cb: cb.data.startswith('heleket_currency_'))
async def top_up_heleket_currency(c: CallbackQuery, user: Users, state: FSMContext):
    currency = c.data.split('_')[2]
    await c.answer(cache_time=3)

    state_data = await state.get_data()

    await state.update_data(currency=currency)
    await state.set_state(RefillBalance.choose_network)

    await c.bot.edit_message_text(
        text=convert.cv(2017, user).format(currency=currency),
        chat_id=c.from_user.id,
        message_id=c.message.message_id,
        reply_markup=kb_user.choose_heleket_network(user, currency))


@router_balance.callback_query(lambda cb: cb.data.startswith('heleket_network_'))
async def top_up_heleket_network(c: CallbackQuery, user: Users, state: FSMContext):
    network = c.data.split('_')[2]
    await c.answer(cache_time=3)

    state_data = await state.get_data()
    currency = state_data.get('currency')
    amount = state_data.get('amount')

    logger.info(f"Preparing Heleket payment - Amount: {amount}, Currency: {currency}, Network: {network}")

    if amount is None or amount == '':
        logger.error(f"Amount is None or empty for user {user.user_id}")
        return await c.bot.send_message(
            chat_id=c.from_user.id,
            text=convert.cv(2033, user),
            reply_markup=kb_user.btn_menu(user))

    await state.update_data(network=network)

    try:
        logger.info(f"Creating Heleket invoice with amount={amount}, currency={currency}, network={network}")

        crypto_amount = amount * 1.10

        draft_invoice_data = await heleket_api.create_invoice(
            amount=amount,
            currency=currency,
            network=network,
            is_crypto_amount=False
        )

        if not draft_invoice_data:
            logger.error(f"Failed to create draft Heleket invoice for user {user.user_id}")
            return await c.bot.send_message(
                chat_id=c.from_user.id,
                text=convert.cv(2034, user),
                reply_markup=kb_user.btn_menu(user))

        exact_crypto_amount = draft_invoice_data.get('payer_amount')

        if not exact_crypto_amount:
            logger.error(f"Failed to get crypto amount from Heleket API for user {user.user_id}")
            return await c.bot.send_message(
                chat_id=c.from_user.id,
                text=convert.cv(2034, user),
                reply_markup=kb_user.btn_menu(user))

        logger.info(f"Got exact crypto amount: {exact_crypto_amount} {currency} for {amount} USD")

        invoice_data = await heleket_api.create_invoice(
            amount=exact_crypto_amount,
            currency=currency,
            network=network,
            is_crypto_amount=True
        )

        if not invoice_data:
            logger.error(f"Failed to create Heleket invoice for user {user.user_id}")
            return await c.bot.send_message(
                chat_id=c.from_user.id,
                text=convert.cv(2034, user),
                reply_markup=kb_user.btn_menu(user))

        invoice_id = invoice_data.get('id') or invoice_data.get('payment_id')
        payment_address = invoice_data.get('address') or invoice_data.get('payment_address')
        invoice_hash = invoice_data.get('hash') or invoice_data.get('invoice_hash')
        crypto_amount = invoice_data.get('payer_amount') or invoice_data.get('amount')

        invoice = await Invoices.aio_create(
            hash=invoice_hash,
            user_id=user.user_id,
            amount=amount,
            provider='heleket',
            currency=currency,
            network=network,
            payment_address=payment_address,
            invoice_id=invoice_id
        )

        logger.info(
            f'user: {user.user_id=} created receipt Heleket\n'
            f'{" " * 14}{amount=} {currency=} {network=}\n'
            f'{" " * 14}{invoice_id=} crypto_amount={crypto_amount}')

        payment_text = convert.cv(2032, user).format(
            invoice_id=invoice_id,
            payment_address=payment_address,
            crypto_amount=crypto_amount,
            currency=currency,
            network=network
        )

        await state.set_state(RefillBalance.waiting_payment)
        await state.update_data(invoice_id=invoice_id)

        await c.bot.edit_message_text(
            text=payment_text,
            chat_id=c.from_user.id,
            message_id=c.message.message_id,
            reply_markup=kb_user.heleket_check_payment(user, invoice_id))

    except Exception as e:
        logger.error(f"Error creating Heleket payment: {e}")
        await c.bot.send_message(
            chat_id=c.from_user.id,
            text=convert.cv(2035, user),
            reply_markup=kb_user.btn_menu(user)
        )


@router_balance.callback_query(lambda cb: cb.data.startswith('heleket_check_'))
async def check_heleket_payment(c: CallbackQuery, user: Users, state: FSMContext):
    invoice_id = c.data.split('_')[2]

    logger.info(f"Checking Heleket payment for user={user.user_id}, invoice_id={invoice_id}")

    payment_data = await heleket_api.check_payment(invoice_id)

    if not payment_data:
        await c.answer(convert.cv(2036, user), show_alert=True)
        return

    payment_status = payment_data.get('status', '').lower()
    logger.info(f"Payment status: {payment_status} for invoice_id={invoice_id}")

    successful_statuses = ['paid', 'paid_over', 'success', 'completed', 'confirmed', 'wrong_amount_waiting']

    if payment_status == 'wrong_amount_waiting':
        payer_amount = float(payment_data.get('payer_amount', '0'))
        payment_amount = float(payment_data.get('payment_amount', '0'))

        if payer_amount > 0:
            deviation_percent = abs(payer_amount - payment_amount) / payment_amount * 100
            if deviation_percent <= 1.5:
                logger.info(f"Accepting payment with wrong_amount_waiting, amount received: {payer_amount}, deviation: {deviation_percent:.2f}%")
                payment_status = 'paid'
            else:
                logger.info(f"Rejecting payment with wrong_amount_waiting, amount received: {payer_amount}, expected: {payment_amount}, deviation: {deviation_percent:.2f}%")

    if payment_status not in successful_statuses:
        await c.answer(convert.cv(2037, user), show_alert=True)
        return

    if payment_status == 'wrong_amount_waiting':
        payer_amount = float(payment_data.get('payer_amount', 0))
        expected_amount = float(payment_data.get('payment_amount', 0))

        if payer_amount > 0:
            deviation_percent = abs(payer_amount - expected_amount) / expected_amount * 100
            if deviation_percent <= 1.5:
                logger.info(f"Accepting payment with wrong_amount_waiting. Expected: {expected_amount}, Got: {payer_amount}, deviation: {deviation_percent:.2f}%")
                payment_status = 'paid'
            else:
                logger.info(f"Rejecting payment with wrong_amount_waiting. Expected: {expected_amount}, Got: {payer_amount}, deviation: {deviation_percent:.2f}%")
                await c.answer(convert.cv(2037, user), show_alert=True)
                return
        else:
            await c.answer(convert.cv(2037, user), show_alert=True)
            return

    try:
        invoice = await Invoices.aio_get(
            Invoices.invoice_id == invoice_id
        )

        if invoice.status == 'paid':
            logger.info(f"Invoice {invoice_id} already processed for user {user.user_id}")

            try:
                await send_log(
                    f'💵 Пользователь {user.more_info_user()} пополнил баланс Heleket на {invoice.amount:.2f}$ '
                    f'({invoice.currency}, {invoice.network})\n'
                    f'🔗 Hash: {invoice.hash}\n'
                    f'🆔 Invoice ID: {invoice.invoice_id}\n'
                    f'💳 Баланс: {user.balance:.2f}$'
                )
            except Exception as e:
                logger.error(f'Error sending duplicate balance log: {e}')

            await c.answer("✅ Платеж уже обработан и зачислен на ваш баланс!", show_alert=True)

            await c.bot.edit_message_text(
                text=convert.cv(2018, user).format(balance=user.balance, smile_money=get_random_smile('money')),
                chat_id=c.from_user.id,
                message_id=c.message.message_id,
                reply_markup=kb_user.btn_menu_inline(user)
            )
            await state.clear()
            return

        elif invoice.status == 'wait':
            logger.info(f"Processing pending invoice {invoice_id} for user {user.user_id}")

            async with database.aio_atomic():
                invoice.status = 'paid'
                await invoice.aio_save()

                old_balance = user.balance
                await Users.update(balance=Users.balance + invoice.amount).where(Users.id == user.id).aio_execute()
                user = await Users.aio_get(Users.id == user.id)

            logger.info(f"Balance updated: {old_balance} -> {user.balance} for user {user.user_id}")

            await c.bot.edit_message_text(
                text=convert.cv(2019, user).format(amount=invoice.amount, smile_money=get_random_smile('money')),
                chat_id=c.from_user.id,
                message_id=c.message.message_id,
                reply_markup=kb_user.btn_menu_inline(user)
            )

            await send_log(
                f'💵 {user.more_info_user()} пополнил баланс Heleket на {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                f'🔗 Hash: {invoice.hash}\n'
                f'🆔 Invoice ID: {invoice.invoice_id}\n'
                f'Баланс сейчас: {user.balance:.2f}$')

            if user.referral is not None:
                try:
                    ref_user: Users = await Users.aio_get(Users.user_id == user.referral)
                    bonus = calculate_percentage(amount=invoice.amount, percentage=config.getfloat('PRICES', 'toup_ref'))

                    old_balance = ref_user.balance
                    async with database.aio_atomic():
                        await Users.update(balance=Users.balance + bonus).where(Users.id == ref_user.id).aio_execute()
                        ref_user: Users = await Users.aio_get(Users.id == ref_user.id)

                    logger.info(
                        f'user: {ref_user.user_id=} new cashback for {user.user_id=}\n'
                        f'{" " * 14}{old_balance=} -> {ref_user.balance}')

                    await send_log(
                        f'⚪ {ref_user.more_info_user()} получил кешбэк {bonus:.2f}$ за друга {user.more_info_user()}\n'
                        f'Баланс сейчас: {ref_user.balance:.2f}$')

                    try:
                        await c.bot.send_message(
                            chat_id=ref_user.user_id,
                            text=convert.cv(38, ref_user).format(
                                smile_money=get_random_smile('money'),
                                amount=bonus
                            ),
                            reply_markup=kb_user.btn_hide(ref_user)
                        )
                    except Exception as e:
                        logger.warning(
                            f'user: {ref_user.user_id=} error send message about cashback\n'
                            f'{" " * 14}{e}\n'
                            f'{" " * 14}{bonus=}')
                except Users.DoesNotExist:
                    pass

        else:
            logger.warning(f"Invoice {invoice_id} has unexpected status: {invoice.status}")
            await c.answer(convert.cv(2039, user).format(status=invoice.status), show_alert=True)

    except Invoices.DoesNotExist:
        logger.warning(f"Invoice not found but payment confirmed by Heleket: invoice_id={invoice_id}, user={user.user_id}")

        try:
            hash_value = payment_data.get('hash') or payment_data.get('invoice_hash') or invoice_id

            invoice = await Invoices.aio_get(
                (Invoices.hash == hash_value) &
                (Invoices.user_id == user.user_id)
            )

            logger.info(f"Found invoice by hash: {invoice.id}, status={invoice.status}")

            if invoice.status == 'paid':
                await c.answer("✅ Платеж уже обработан и зачислен на ваш баланс!", show_alert=True)
                await c.bot.edit_message_text(
                    text=convert.cv(2018, user).format(balance=user.balance, smile_money=get_random_smile('money')),
                    chat_id=c.from_user.id,
                    message_id=c.message.message_id,
                    reply_markup=kb_user.btn_menu_inline(user)
                )
            elif invoice.status == 'wait':
                logger.info(f"Processing invoice found by hash: {invoice.id}")
                async with database.aio_atomic():
                    invoice.status = 'paid'
                    invoice.invoice_id = invoice_id
                    await invoice.aio_save()

                    old_balance = user.balance
                    await Users.update(balance=Users.balance + invoice.amount).where(Users.id == user.id).aio_execute()
                    user = await Users.aio_get(Users.id == user.id)

                await c.bot.edit_message_text(
                    text=convert.cv(2019, user).format(amount=invoice.amount, smile_money=get_random_smile('money')),
                    chat_id=c.from_user.id,
                    message_id=c.message.message_id,
                    reply_markup=kb_user.btn_menu_inline(user)
                )

                await send_log(
                    f'💵 {user.more_info_user()} пополнил баланс Heleket на {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                    f'🔗 Hash: {invoice.hash}\n'
                    f'🆔 Invoice ID: {invoice.invoice_id}\n'
                    f'Баланс сейчас: {user.balance:.2f}$')

                if user.referral is not None:
                    pass

        except Invoices.DoesNotExist:
            await c.answer(convert.cv(2040, user), show_alert=True)
            logger.error(f"Payment confirmed but invoice not found for user {user.user_id}, invoice_id={invoice_id}")

    await state.clear()

@router_balance.callback_query(lambda cb: cb.data == 'go_to_menu')
async def go_to_menu_handler(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    await state.clear()

    try:
        await c.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

    await c.message.answer(
        text=convert.cv('main menu', user).format(smile=get_random_smile('hello')),
        reply_markup=kb_user.main_menu(user)
    )

@router_balance.callback_query(F.data == 'getTopUpBalance')
async def get_top_up_balance(callback: CallbackQuery, user: Users, state: FSMContext):
    await state.set_state(RefillBalance.enter_amount)
    await callback.message.edit_text(
        text=convert.cv(30, user).format(
            smile_money=get_random_smile('money'),
            balance=round(user.balance, 2)
        ),
        reply_markup=kb_user.btn_cancel(user)
    )
    await callback.answer()
