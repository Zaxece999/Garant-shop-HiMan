import logging
import typing
import datetime
from tables import StatusDeal

from telegram.misc.states import AdminState
from aiogram.fsm.context import FSMContext
from telegram.functions.func import *
from additional.functions import *
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from names import get_last_name
from random import randint
from aiogram import Router
from typing import List
from tables import *
from peewee import fn
from aiogram import F
from init import *
from re import *
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup


logger = logging.getLogger('CS1')

router_admin = Router()


@router_admin.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='admin')))
async def menu_admin(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    await state.clear()
    await m.answer(text=convert.admin_text(10), reply_markup=kb_admin.admin_menu(user=user))
    return


@router_admin.message(AdminState.add_balance_enter_amount, F.chat.type == 'private')
async def add_balance_amount(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    try:
        amount = round(float(m.text), 2)
    except ValueError:
        await m.answer(text="Пожалуйста, введите корректное число (например: 5 или -5)")
        return

    data = await state.get_data()
    await state.set_state(AdminState.add_balance_confirm)
    await state.update_data(user_id=data['user_id'], amount=amount)

    if amount > 0:
        text = convert.admin_text(16).format(amount=amount)
    else:
        text = convert.admin_text(17).format(amount=abs(amount))

    await m.answer(text=text, reply_markup=kb_admin.confirm_yes_cancel(user=user))
    return


@router_admin.callback_query(AdminState.add_balance_confirm, lambda cb: cb.data.split("_")[0] == 'yes')
async def confirm_add_balance(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer(cache_time=2)
    if user.admin == 0:
        return

    data = await state.get_data()
    amount = float(data['amount'])
    user_id = data['user_id']

    user_client: Users = await Users.aio_get(Users.user_id == user_id)

    old_balance = user_client.balance
    async with database.aio_atomic():
        await Users.update(balance = Users.balance + amount).where(Users.user_id == user_client.user_id).aio_execute()
        user_client: Users = await Users.aio_get(Users.id == user_client.id)

    logger.info(
        f'user: {user_client.user_id} add balance from admin success.\n'
        f'{" " * 14}{old_balance=} -> {user_client.balance}')

    await state.clear()
    await c.message.edit_text(
        text=convert.admin_text(18).format(
            username=user_client.username,
            balance=user_client.balance
        ),
        reply_markup=kb_admin.admin_menu(user=user))
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'admin' and cb.data != 'admin_shop' and not cb.data.startswith('admin_shop_'))
async def menu_admin(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    await state.clear()
    await c.message.edit_text(text=convert.admin_text(10), reply_markup=kb_admin.admin_menu(user=user))
    return


@router_admin.callback_query(lambda cb: cb.data == 'admin_shop')
async def shop_admin_redirect(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    await state.clear()

    try:
        from telegram.handler.shop_admin import admin_shop_menu
        await admin_shop_menu(c, state)
    except Exception as e:
        logger.error(f"Error redirecting to shop admin: {e}")
        await c.message.edit_text(
            "📝 <b>Admin Shop Panel</b>\n\n"
            "Welcome to the shop administration panel.\n"
            "Here you can manage categories, products, and view statistics.",
            reply_markup=kb_user.admin_shop_menu(user)
        )
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'usersCount')
async def users_count(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    users_count_result = await Users.select(fn.COUNT(Users.id).alias('cnt')).aio_execute()
    users_count = users_count_result[0].cnt

    await c.message.edit_text(
        text=convert.admin_text(11).format(count_users=users_count),
        reply_markup=kb_user.btn_back(user=user, callback='admin'))
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'usersBalance')
async def check_payment(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    users_balance: typing.List[Users] = await Users.select().order_by(Users.balance.desc()).limit(20).aio_execute()

    balances = ''
    for m_user in users_balance:
        balances += f'<b>{round(m_user.balance, 2):.2f}$</b> : <u>{m_user.full_name}</u>\n'

    await c.message.edit_text(
        text=balances,
        reply_markup=kb_user.btn_back(user=user, callback='admin'))
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'addBalance')
async def gateway_balances(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    await state.set_state(AdminState.add_balance_enter_user)
    await c.message.edit_text(text=convert.admin_text(13), reply_markup=kb_user.btn_back(user, 'admin'))
    return


@router_admin.message(AdminState.add_balance_enter_user, F.chat.type == 'private')
async def add_balance(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    user_id = m.text.replace('@', '')

    try:

        if user_id.isdigit():
            get_user: Users = await Users.aio_get(Users.user_id == int(user_id))
        else:
            get_user: Users = await Users.aio_get(Users.username == user_id)

    except Users.DoesNotExist:
        answer = await m.answer(text=convert.admin_text(14))
        loop.create_task(auto_delete_messages([answer, m], 5))
        return

    await state.set_state(AdminState.add_balance_enter_amount)
    await state.update_data(user_id=get_user.user_id)

    await m.answer(
        text=convert.admin_text(15).format(
            balance=get_user.balance,
            full_name=get_user.full_name))
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'makeMailing')
async def gateway_balances(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    if user.admin == 0:
        return

    await state.set_state(AdminState.get_mailing_text)
    await c.message.edit_text(text=convert.admin_text(24), reply_markup=kb_user.btn_back(user, 'admin'))
    return


@router_admin.message(AdminState.get_mailing_text, F.chat.type == 'private')
async def get_mailing_text(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    try:
        text = m.html_text
    except TypeError:
        text = None

    photo = None
    video = None
    document = None

    if m.photo:
        photo = m.photo[-1].file_id
    if m.video:
        video = m.video.file_id
    if m.document:
        document = m.document.file_id

    await state.set_state(AdminState.confirm_mailing)
    await state.update_data(text=text, video=video, photo=photo, document=document)

    if photo:
        await m.answer_photo(photo=photo, caption=text)
    elif video:
        await m.answer_video(video=video, caption=text)
    elif document:
        await m.answer_document(document=document, caption=text)
    else:
        await m.answer(text=text)

    await m.answer(text=convert.admin_text(25), reply_markup=kb_admin.confirm_yes_cancel(user=user))
    return


@router_admin.callback_query(AdminState.confirm_mailing, lambda cb: cb.data.split("_")[0] == 'yes')
async def confirm_start_mailing(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer(cache_time=5)

    data = await state.get_data()

    loop.create_task(global_mailing(
        update_message=c,
        text=data['text'],
        photo=data['photo'],
        video=data['video'],
        document=data['document']
    ))
    await c.message.edit_text(text=convert.admin_text(26))
    return


@router_admin.callback_query(AdminState.confirm_mailing, lambda cb: cb.data.split("_")[0] == 'enterTime')
async def get_enter_time(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()
    await state.set_state(AdminState.enter_time_mailing)

    now = datetime.datetime.now()
    next_date = datetime.timedelta(days=1) + now
    next_date = next_date.strftime('%d.%m.%Y %H:%M:%S')

    await c.message.edit_text(text=convert.admin_text(26).format(now_date=next_date), reply_markup=kb_user.btn_cancel(user=user))
    return


@router_admin.message(AdminState.enter_time_mailing, F.chat.type == 'private')
async def enter_time_for_mailing(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    need_time = m.text

    try:
        date_obj = datetime.datetime.strptime(need_time, "%d.%m.%Y %H:%M:%S")
    except ValueError:
        return await m.reply(text=convert.admin_text(31))

    data = await state.get_data()

    delayed_mailing: Mailing = await Mailing.aio_create(
        user_id=user.user_id,
        message=data['text'],
        photo_id=data['photo'],
        video_id=data['video'],
        document_id=data['document'],
        time=date_obj)

    await state.clear()
    await m.answer(text='Added!', reply_markup=kb_admin.deleteAutoMailing(mailing=delayed_mailing))
    return


@router_admin.callback_query(lambda cb: cb.data.split("_")[0] == 'deleteAutoMailing')
async def delete_auto_mailing(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer(cache_time=2)

    data = c.data.split('_')
    mailing_id = data[1]

    try:
        delayed_mailing: Mailing = await Mailing.aio_get(Mailing.id == mailing_id)
        await delayed_mailing.aio_delete_instance()
        await c.answer(text='✅', show_alert=True)
        await c.message.delete()
        return
    except Mailing.DoesNotExist:
        return await c.answer(text='This record not found')

@router_admin.callback_query(lambda cb: cb.data == 'adminCloseDeal')
async def admin_close_deal_start(c: CallbackQuery, user: Users, state: FSMContext):
    if user.admin == 0:
        return
    await state.set_state(AdminState.close_deal_enter_id)
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="admin")]
        ]
    )
    await c.message.edit_text(
        text=convert.admin_text(19),
        reply_markup=inline_kb
    )

@router_admin.message(AdminState.close_deal_enter_id, F.text.casefold() == "назад")
async def close_deal_back(m: Message, user: Users, state: FSMContext):
    await state.clear()
    await m.answer(text=convert.admin_text(10), reply_markup=kb_admin.admin_menu(user=user))

@router_admin.message(AdminState.close_deal_enter_id)
async def close_deal_enter_id(m: Message, user: Users, state: FSMContext):
    uniq_id = m.text.strip().replace("Сделка #", "").replace("#", "")
    try:
        deal: Deals = await Deals.aio_get(Deals.uniq_id == uniq_id)
    except Deals.DoesNotExist:
        await m.answer(convert.admin_text(23))
        return
    await state.set_state(AdminState.close_deal_confirm)
    await state.update_data(deal_uniq_id=uniq_id)

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Да", callback_data="adminCloseDealYes"),
        InlineKeyboardButton(text="Нет", callback_data="adminCloseDealNo")
    )
    await m.answer(convert.admin_text(20).format(uniq_id=uniq_id), reply_markup=kb.as_markup())

@router_admin.callback_query(AdminState.close_deal_confirm, lambda cb: cb.data == 'adminCloseDealNo')
async def close_deal_cancel(c: CallbackQuery, user: Users, state: FSMContext):
    await state.clear()
    await c.message.edit_text(convert.admin_text(22), reply_markup=kb_admin.admin_menu(user=user))

@router_admin.callback_query(AdminState.close_deal_confirm, lambda cb: cb.data == 'adminCloseDealYes')
async def close_deal_confirm(c: CallbackQuery, user: Users, state: FSMContext):
    data = await state.get_data()
    uniq_id = data['deal_uniq_id']
    try:
        deal: Deals = await Deals.aio_get(Deals.uniq_id == uniq_id)
    except Deals.DoesNotExist:
        await c.message.edit_text(convert.admin_text(23), reply_markup=kb_admin.admin_menu(user=user))
        await state.clear()
        return
    if deal.status == StatusDeal.canceled:
        await c.message.edit_text("Сделка уже отменена.", reply_markup=kb_admin.admin_menu(user=user))
        await state.clear()
        return
    who_start_user: Users = await Users.aio_get(Users.user_id == deal.who_start_deal)
    seller_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
    buyer_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)
    async with database.aio_atomic():
        await Deals.update(status=StatusDeal.canceled, end_time=datetime.datetime.now()).where(Deals.uniq_id == uniq_id).aio_execute()
        await Users.update(balance=Users.balance + deal.price).where(Users.user_id == who_start_user.user_id).aio_execute()
    text = convert.admin_text(55).format(uniq_id=uniq_id, username=who_start_user.username or who_start_user.user_id)
    try:
        await c.bot.send_message(chat_id=seller_user.user_id, text=text)
    except Exception:
        pass
    try:
        await c.bot.send_message(chat_id=buyer_user.user_id, text=text)
    except Exception:
        pass
    log_text = convert.admin_text(56).format(
        uniq_id=uniq_id,
        seller=seller_user.username or seller_user.user_id,
        buyer=buyer_user.username or buyer_user.user_id,
        username=who_start_user.username or who_start_user.user_id
    )
    try:
        await c.bot.send_message(chat_id=config["CHATS_ID"]["logs"], text=log_text)
    except Exception:
        pass
    await c.message.edit_text(convert.admin_text(21).format(uniq_id=uniq_id), reply_markup=kb_admin.admin_menu(user=user))
    await state.clear()

@router_admin.callback_query(lambda cb: cb.data == 'checkPayment')
async def check_payment_start(c: CallbackQuery, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    await state.set_state(AdminState.WAITING_FOR_HASH)
    await c.message.edit_text(
        "Отправьте hash транзакции для проверки:",
        reply_markup=kb_admin.btn_cancel(user)
    )

@router_admin.message(AdminState.WAITING_FOR_HASH)
async def check_payment_by_hash(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    hash_value = m.text.strip()

    try:
        invoice = await Invoices.aio_get(Invoices.hash == hash_value)

        invoice_user = await Users.aio_get(Users.user_id == invoice.user_id)

        payment_status = "Неизвестно"
        if invoice.provider == 'heleket' and invoice.invoice_id:
            payment_data = await heleket_api.check_payment(invoice.invoice_id)
            if payment_data:
                payment_status = payment_data.get('status', 'Неизвестно').upper()

        message = (
            f"🧾 Информация о платеже:\n\n"
            f"👤 Пользователь: @{invoice_user.username} (ID: {invoice_user.user_id})\n"
            f"💰 Сумма: {invoice.amount} USD\n"
            f"🔗 Hash: {invoice.hash}\n"
            f"🆔 Invoice ID: {invoice.invoice_id}\n"
            f"🌐 Сеть: {invoice.network or 'Не указана'}\n"
            f"💱 Валюта: {invoice.currency or 'Не указана'}\n"
            f"📊 Статус в базе: {invoice.status.upper()}\n"
            f"📡 Статус в системе: {payment_status}\n"
        )

        await m.answer(message, reply_markup=kb_admin.admin_menu(user))
        await state.clear()

    except Invoices.DoesNotExist:
        await m.answer(
            "❌ Платёж с таким hash не найден в системе.",
            reply_markup=kb_admin.admin_menu(user)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error checking payment by hash: {e}")
        await m.answer(
            "❌ Произошла ошибка при проверке платежа.",
            reply_markup=kb_admin.admin_menu(user)
        )
        await state.clear()


@router_admin.message(F.chat.type == 'private', F.text.startswith('/add_admin'))
async def add_admin_command(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    command_parts = m.text.split()
    if len(command_parts) != 2:
        await m.answer(
            "❌ Неправильный формат команды!\n\n"
            "Используйте:\n"
            "/add_admin @username\n"
            "или\n"
            "/add_admin 123456789\n\n"
            "Пример: /add_admin @username"
        )
        return

    target_identifier = command_parts[1].replace('@', '')

    try:
        if target_identifier.isdigit():
            target_user: Users = await Users.aio_get(Users.user_id == int(target_identifier))
        else:
            target_user: Users = await Users.aio_get(Users.username == target_identifier)

        if target_user.admin > 0:
            await m.answer(
                f"ℹ️ Пользователь {target_user.info_user()} уже является администратором (уровень: {target_user.admin})"
            )
            return

        old_admin_level = target_user.admin
        target_user.admin = 1
        await target_user.aio_save()

        logger.info(f"Admin {user.user_id} promoted user {target_user.user_id} to admin")

        await m.answer(
            f"✅ Пользователь {target_user.info_user()} (ID: {target_user.user_id}) успешно назначен администратором!\n\n"
            f"Было: {old_admin_level} → Стало: {target_user.admin}"
        )

        try:
            await m.bot.send_message(
                chat_id=target_user.user_id,
                text="🎉 Поздравляем! Вы назначены администратором бота!"
            )
        except Exception as e:
            logger.warning(f"Could not notify new admin {target_user.user_id}: {e}")
            await m.answer("⚠️ Не удалось отправить уведомление новому администратору (возможно, бот заблокирован)")

    except Users.DoesNotExist:
        await m.answer(
            f"❌ Пользователь '{target_identifier}' не найден в базе данных.\n\n"
            "Убедитесь, что пользователь хотя бы раз запускал бота."
        )
    except Exception as e:
        logger.error(f"Error in add_admin command: {e}")
        await m.answer(
            "❌ Произошла ошибка при назначении администратора. Проверьте логи."
        )


@router_admin.message(F.chat.type == 'private', F.text == '/list_admins')
async def list_admins_command(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    try:
        admins: typing.List[Users] = await Users.select().where(Users.admin > 0).order_by(Users.admin.desc()).aio_execute()

        if not admins:
            await m.answer("👥 Администраторы не найдены.")
            return

        admin_list = "👥 <b>Список администраторов:</b>\n\n"
        for admin in admins:
            admin_info = admin.info_user()
            admin_list += f"• {admin_info} (ID: <code>{admin.user_id}</code>) - уровень: {admin.admin}\n"

        admin_list += f"\n📊 Всего: {len(admins)} администратор(ов)"

        await m.answer(admin_list, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in list_admins command: {e}")
        await m.answer("❌ Произошла ошибка при получении списка администраторов.")


@router_admin.message(F.chat.type == 'private', F.text.startswith('/remove_admin'))
async def remove_admin_command(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    command_parts = m.text.split()
    if len(command_parts) != 2:
        await m.answer(
            "❌ Неправильный формат команды!\n\n"
            "Используйте:\n"
            "/remove_admin @username\n"
            "или\n"
            "/remove_admin 123456789\n\n"
            "Пример: /remove_admin @oldadmin"
        )
        return

    target_identifier = command_parts[1].replace('@', '')

    try:
        if target_identifier.isdigit():
            target_user: Users = await Users.aio_get(Users.user_id == int(target_identifier))
        else:
            target_user: Users = await Users.aio_get(Users.username == target_identifier)

        if target_user.admin == 0:
            await m.answer(
                f"ℹ️ Пользователь {target_user.info_user()} не является администратором."
            )
            return

        if target_user.user_id == user.user_id:
            await m.answer("❌ Вы не можете снять права администратора у самого себя!")
            return

        old_admin_level = target_user.admin
        target_user.admin = 0
        await target_user.aio_save()

        logger.info(f"Admin {user.user_id} removed admin rights from user {target_user.user_id}")

        await m.answer(
            f"✅ У пользователя {target_user.info_user()} (ID: {target_user.user_id}) сняты права администратора!\n\n"
            f"Было: {old_admin_level} → Стало: {target_user.admin}"
        )

        try:
            await m.bot.send_message(
                chat_id=target_user.user_id,
                text="📢 Ваши права администратора были сняты."
            )
        except Exception as e:
            logger.warning(f"Could not notify former admin {target_user.user_id}: {e}")

    except Users.DoesNotExist:
        await m.answer(
            f"❌ Пользователь '{target_identifier}' не найден в базе данных."
        )
    except Exception as e:
        logger.error(f"Error in remove_admin command: {e}")
        await m.answer(
            "❌ Произошла ошибка при снятии прав администратора. Проверьте логи."
        )


@router_admin.message(F.chat.type == 'private', F.text == '/admin_help')
async def admin_help_command(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    help_text = """
🔧 <b>Команды администратора:</b>

👥 <b>Управление администраторами:</b>
• <code>/add_admin @username</code> - назначить администратора
• <code>/add_admin 123456789</code> - назначить по ID
• <code>/list_admins</code> - список всех админов
• <code>/remove_admin @username</code> - снять права админа
• <code>/admin_help</code> - эта справка

💰 <b>Управление балансами:</b>
• Используйте админ-панель в боте для изменения балансов

�️ <b>Уведомления магазина:</b>
• <code>/notify_shop текст</code> - отправить уведомление всем пользователям
• Автоматические уведомления при добавлении товаров

�📊 <b>Статистика:</b>
• Используйте админ-панель для просмотра статистики

<b>Примеры:</b>
<code>/add_admin @username</code>
<code>/add_admin 123456789</code>
<code>/remove_admin @oldadmin</code>
<code>/notify_shop New Google accounts available!</code>
"""

    await m.answer(help_text, parse_mode='HTML')


@router_admin.message(F.chat.type == 'private', F.text == '/add_owner')
async def add_owner_command(m: Message, user: Users, state: FSMContext):
    if user.admin == 0:
        return

    owner_id = int(config['BOT']['owner_id'])
    owner_username = config['BOT']['owner_username']

    try:
        try:
            target_user: Users = await Users.aio_get(Users.user_id == owner_id)

            if target_user.admin > 0:
                await m.answer(
                    f"ℹ️ Пользователь @{owner_username} (ID: {owner_id}) уже является администратором (уровень: {target_user.admin})"
                )
                return

            target_user.admin = 1
            target_user.username = owner_username
            await target_user.aio_save()

            await m.answer(
                f"✅ Пользователь @{owner_username} (ID: {owner_id}) успешно назначен администратором!"
            )

        except Users.DoesNotExist:
            new_admin = await Users.aio_create(
                user_id=owner_id,
                username=owner_username,
                full_name=owner_username,
                nickname=owner_username,
                lang='ru',
                admin=1,
                balance=0.0,
                when_start=datetime.datetime.now()
            )

            await m.answer(
                f"✅ Создан новый администратор @{owner_username} (ID: {owner_id})!\n"
                f"Пользователь должен запустить бота командой /start для активации."
            )

        logger.info(f"Admin {user.user_id} added owner ({owner_id}) as admin via /add_owner command")

    except Exception as e:
        logger.error(f"Error in add_owner command: {e}")
        await m.answer(
            "❌ Произошла ошибка при добавлении владельца как администратора. Проверьте логи."
        )
