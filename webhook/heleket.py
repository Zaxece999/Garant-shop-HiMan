import logging
from additional.functions import calculate_percentage, get_random_smile
from telegram.functions.func import send_log
from tables.invoices import Invoices
from tables.users import Users
from aiohttp import web
from init import *
import traceback


logger = logging.getLogger('CS1')


async def heleket_webhook(request) -> web.Response:
    try:
        body_text = await request.text()
        logger.debug(f'Heleket webhook raw body: {body_text}')

        try:
            update_data = await request.json()
            logger.debug(f'Heleket webhook parsed JSON: {update_data}')
        except Exception as e:
            logger.error(f'Failed to parse Heleket webhook JSON: {e}')
            return web.Response(status=400, text='Invalid JSON')

        logger.info(f'Heleket webhook full data: {update_data}')

        payment_id = update_data.get('payment_id') or update_data.get('id')
        hash_value = update_data.get('hash') or update_data.get('invoice_hash')
        status = update_data.get('status', '').lower()

        amount = update_data.get('amount')
        currency = update_data.get('currency')
        network = update_data.get('network')

        if not all([payment_id, hash_value]):
            logger.error(f'Heleket webhook: Missing required fields in payload')
            return web.Response(status=400, text='Missing required fields')

        logger.info(
            f"Heleket webhook received: payment_id={payment_id}, hash={hash_value}, "
            f"status={status}, amount={amount}, currency={currency}, network={network}")

        successful_statuses = ['success', 'completed', 'paid', 'confirmed']
        if status not in successful_statuses:
            logger.info(f'Heleket payment {payment_id} status: {status} - not success')
            return web.Response(status=200, text='Status not indicating success')

        try:
            async with database.aio_atomic():
                try:
                    invoice: Invoices = await Invoices.aio_get(
                        (Invoices.hash == hash_value) &
                        (Invoices.status == 'wait') &
                        (Invoices.provider == 'heleket')
                    )
                    logger.info(f"Found invoice by hash: {invoice.id}")
                except Invoices.DoesNotExist:
                    try:
                        invoice: Invoices = await Invoices.aio_get(
                            (Invoices.invoice_id == payment_id) &
                            (Invoices.status == 'wait') &
                            (Invoices.provider == 'heleket')
                        )
                        logger.info(f"Found invoice by invoice_id: {invoice.id}")
                    except Invoices.DoesNotExist:
                        logger.error(
                            f'Heleket webhook: Invoice not found for hash={hash_value} or payment_id={payment_id}')
                        return web.Response(status=200, text='Invoice not found')

                if invoice.invoice_id and invoice.invoice_id != payment_id and invoice.hash != hash_value:
                    logger.warning(
                        f'Heleket webhook: Payment data mismatch. Invoice: {invoice.invoice_id}/{invoice.hash}, Got: {payment_id}/{hash_value}')
                    return web.Response(status=200, text='Invoice data mismatch')

                try:
                    user: Users = await Users.aio_get(Users.user_id == invoice.user_id)
                except Users.DoesNotExist:
                    logger.error(f'User not found for invoice {invoice.id}, user_id={invoice.user_id}')
                    return web.Response(status=200, text='User not found')

                invoice.status = 'paid'
                await invoice.aio_save()

                old_balance = user.balance
                user.balance += invoice.amount
                await user.aio_save()

            logger.info(
                f'Heleket: user {user.user_id} payment successful\n'
                f'{" " * 14}payment_id={payment_id}\n'
                f'{" " * 14}amount={invoice.amount} {invoice.currency} {invoice.network}\n'
                f'{" " * 14}balance: {old_balance} -> {user.balance}')

            try:
                await bot_main.send_message(
                    chat_id=user.user_id,
                    text=f"✅ Пополнение получено! Ваш баланс пополнен на {invoice.amount}$ {get_random_smile('money')}",
                    reply_markup=kb_user.btn_menu(user))

                await send_log(
                    f'💵 Пополнение баланса\n'
                    f'👤 Пользователь: {user.more_info_user()}\n'
                    f'💰 Сумма: {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                    f'🔗 Hash: {invoice.hash}\n'
                    f'🆔 Invoice ID: {invoice.invoice_id}\n'
                    f'💳 Баланс: {user.balance:.2f}$'
                )
            except Exception as e:
                logger.error(f'Failed to send payment notification to user {user.user_id}: {e}')

            await send_log(
                f'💵 {user.more_info_user()} пополнил баланс Heleket на {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                f'Баланс сейчас: {user.balance:.2f}$')

            if user.referral is not None:
                try:
                    ref_user: Users = await Users.aio_get(Users.user_id == user.referral)
                    bonus = calculate_percentage(amount=invoice.amount, percentage=config.getfloat('PRICES', 'toup_ref'))

                    old_ref_balance = ref_user.balance
                    async with database.aio_atomic():
                        await Users.update(balance=Users.balance + bonus).where(Users.id == ref_user.id).aio_execute()
                        ref_user: Users = await Users.aio_get(Users.id == ref_user.id)

                    logger.info(
                        f'user: {ref_user.user_id=} new cashback for {user.user_id=}\n'
                        f'{" " * 14}{old_ref_balance=} -> {ref_user.balance}')

                    await send_log(
                        f'⚪ {ref_user.more_info_user()} получил кешбэк {bonus:.2f}$ за друга {user.more_info_user()}\n'
                        f'Баланс сейчас: {ref_user.balance:.2f}$')

                    try:
                        await bot_main.send_message(
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
                    logger.warning(f'Referral {user.referral} for user {user.user_id} not found')

        except Invoices.DoesNotExist:
            logger.error(
                f'Heleket webhook: Invoice not found or already paid\n'
                f'{" " * 14}payment_id={payment_id}\n'
                f'{" " * 14}hash={hash_value}')
            return web.Response(status=200, text='Invoice not found or already paid')

    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f'Error in Heleket webhook handler: {e}\n{error_traceback}')
        return web.Response(status=500, text=f'Internal server error: {str(e)}')

    return web.Response(status=200, text='Payment processed successfully')
