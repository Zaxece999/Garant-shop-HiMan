from aiogram.types import BotCommand
from random import choice
from init import *
import asyncio
import logging


async def check_unprocessed_payments():
    logger.info("Checking for unprocessed payments...")

    from tables.invoices import Invoices
    from tables.users import Users
    from additional.functions import get_random_smile
    from telegram.functions.func import send_log

    try:
        pending_heleket_invoices = await Invoices.select().where(
            (Invoices.status == 'wait') &
            (Invoices.provider == 'heleket')
        ).aio_execute()

        for invoice in pending_heleket_invoices:
            try:
                if not invoice.invoice_id:
                    logger.warning(f"Skipping Heleket invoice {invoice.id} with no invoice_id")
                    continue

                payment_data = await heleket_api.check_payment(invoice.invoice_id)

                if payment_data and payment_data.get('status', '').lower() in ['paid', 'success', 'completed', 'confirmed']:
                    logger.info(f"Found unpaid Heleket invoice: {invoice.invoice_id} for user {invoice.user_id}")

                    async with database.aio_atomic():
                        user = await Users.aio_get(Users.user_id == invoice.user_id)

                        invoice.status = 'paid'
                        await invoice.aio_save()

                        old_balance = user.balance
                        user.balance += invoice.amount
                        await user.aio_save()

                    logger.info(
                        f'Fixed Heleket payment for user: {user.user_id}\n'
                        f'{" " * 14}invoice: {invoice.invoice_id}\n'
                        f'{" " * 14}amount: {invoice.amount}\n'
                        f'{" " * 14}currency: {invoice.currency}, network: {invoice.network}\n'
                        f'{" " * 14}balance: {old_balance} -> {user.balance}')

                    await bot_main.send_message(
                        chat_id=user.user_id,
                        text=f"✅ Обнаружен неучтенный платеж Heleket! Ваш баланс пополнен на {invoice.amount}$ {get_random_smile('money')}",
                        reply_markup=kb_user.btn_menu(user=user))

                    await send_log(
                        f'🔄 Исправлен пропущенный платеж Heleket для {user.more_info_user()}\n'
                        f'Сумма: {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network}) | Баланс: {user.balance:.2f}$')

            except Exception as e:
                logger.error(f"Error checking Heleket invoice {invoice.invoice_id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in check_unprocessed_payments: {e}")


async def on_start():

    me = await bot_main.me()
    logger.debug(me)

    me = await bot_main.me()
    config['GARANT']['required_signature'] = f'@{me.username}'

    random_word_start = choice(['START'])
    commands = [
        BotCommand(command='start', description=f'{random_word_start}'),
    ]
    await bot_main.set_my_commands(commands)

    from telegram.functions.auto_mailing import start_check_mailing
    from webhook.start import start_web_server

    loop.create_task(start_check_mailing())
    loop.create_task(start_web_server(host=config['APP']['host'], port=config['APP']['port']))

    loop.create_task(check_unprocessed_payments())

    async def periodic_payment_check():
        while True:
            await asyncio.sleep(3600)
            await check_unprocessed_payments()

    loop.create_task(periodic_payment_check())


async def on_shutdown():
    await bot_main.delete_webhook()
    await dp_main.storage.close()


async def app_bot():

    dp_main.startup.register(on_start)
    dp_main.shutdown.register(on_shutdown)

    from telegram.handler.commands.general_chat.start import router_general_sp
    from telegram.handler.commands.private_chat.start import router_private_sp

    from telegram.handler.withdrawal import router_withdrawal
    from telegram.handler.all_deals import router_all_deals
    from telegram.handler.balance import router_balance
    from telegram.handler.disput import router_disput
    from telegram.handler.admin import router_admin
    from telegram.handler.menu import router_menu
    from telegram.handler.info import router_info
    from telegram.handler.deal import router_deal
    from telegram.handler.shop import router_shop
    from telegram.handler.shop_admin import router_shop_admin

    from telegram.middleware.users import SingleOperationMiddleware
    dp_main.message.middleware(SingleOperationMiddleware())
    dp_main.callback_query.middleware(SingleOperationMiddleware())
    dp_main.inline_query.middleware(SingleOperationMiddleware())

    dp_main.include_router(router_private_sp)
    dp_main.include_router(router_general_sp)

    dp_main.include_router(router_disput)
    dp_main.include_router(router_menu)
    dp_main.include_router(router_info)
    dp_main.include_router(router_balance)
    dp_main.include_router(router_deal)
    dp_main.include_router(router_shop_admin)
    dp_main.include_router(router_admin)
    dp_main.include_router(router_all_deals)
    dp_main.include_router(router_withdrawal)
    dp_main.include_router(router_shop)

    await dp_main.start_polling(bot_main)


loop.run_until_complete(app_bot())
