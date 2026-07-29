import asyncio
import typing
import random
import time
import re

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.dispatcher.dispatcher import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from additional.functions import get_random_smile
from tables import *
from init import *


async def auto_delete_messages(messages: list, second):
    await asyncio.sleep(second)
    for message in messages:
        logger.debug(message.message_id)
        if message.message_id not in list_for_delete_messages:
            continue
        list_for_delete_messages.remove(message.message_id)
        await bot_main.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    return


async def send_log(message):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    full_message = f'{now}\n\n{message}'

    try:
        await bot_main.send_message(
            chat_id=config['CHATS_ID']['logs'],
            text=full_message,
            disable_notification=True)
    except Exception as e:
        logger.error(str(e))


async def get_main_menu(bot: Bot, user: Users, state: FSMContext = None):
    if state:
        await state.clear()

    await bot.send_message(
        chat_id=user.user_id,
        text=convert.cv(10, user).format(my_user_id=user.user_id, smile_random=get_random_smile()),
        reply_markup=kb_user.main_menu(user))

    return


async def global_mailing(
        update_message: typing.Union[CallbackQuery, Message],
        text: str = None,
        photo: str = None,
        video: str = None,
        document: str = None
    ):

    index = 0
    count_sended = 0
    block_count = 0
    flood_count = 0
    error_count = 0

    users: typing.List[Users] = await Users.select().aio_execute()

    if not users:
        logger.warning("No users found for mailing")
        try:
            no_users_text = "❌ Нет пользователей для рассылки"
            if isinstance(update_message, CallbackQuery):
                await update_message.message.edit_text(text=no_users_text)
            else:
                await update_message.edit_text(text=no_users_text)
        except Exception as e:
            logger.error(f"Error showing no users message: {e}")
        return

    logger.info(f"Starting mailing to {len(users)} users. Text: {text[:100] if text else 'None'}...")

    compile_deactivated = re.compile(r'user is deactivated')
    compile_not_found = re.compile(r'chat not found')
    compile_bot_blocked = re.compile(r'bot can\'t initiate conversation|Forbidden: bot can\'t initiate conversation|bot was blocked by the user')

    for user_bot in users:
        try:

            if user_bot.mailing in ['deactivated', 'chat not found']:
                if user_bot.mailing == 'deactivated':
                    block_count += 1
                else:
                    error_count += 1
                continue

            if user_bot.lang is not None and user_bot.lang == 'no':
                user_bot.lang = 'en'

            index += 1
            logger.debug(f"Processing user {index}/{len(users)}: {user_bot.user_id}")
            if (index % 50) == 0:
                try:
                    update_text = convert.admin_text(27).format(smile_time=get_random_smile('time'))
                    update_text += convert.admin_text(29).format(
                        msg_count=count_sended,
                        block_count=block_count,
                        flood_count=flood_count,
                        error_count=error_count)

                    if isinstance(update_message, CallbackQuery):
                        await update_message.message.edit_text(text=update_text)
                    else:
                        await update_message.edit_text(text=update_text)
                except Exception as update_error:
                    logger.error(f'Error updating mailing progress: {update_error}')

            if photo:
                await update_message.bot.send_photo(chat_id=user_bot.user_id, photo=photo, caption=text)

            elif video:
                await update_message.bot.send_video(chat_id=user_bot.user_id, video=video, caption=text)

            elif document:
                await update_message.bot.send_document(chat_id=user_bot.user_id, document=document, caption=text)

            else:
                await update_message.bot.send_message(chat_id=user_bot.user_id, text=text)
            count_sended += 1

        except TelegramForbiddenError as ex:
            block_count += 1
            logger.error(f'user: {user_bot.user_id} | {ex}')

            try:
                error = str(ex)
                if compile_deactivated.search(error):
                    user_bot.mailing = 'deactivated'
                    await user_bot.aio_save()
            except Exception as save_error:
                logger.error(f'Error saving user mailing status: {save_error}')

        except TelegramRetryAfter as ex:
            flood_count += 1
            logger.error(f'user: {user_bot.user_id} | {ex}', exc_info=True)

        except Exception as ex:
            error = str(ex)
            try:
                if compile_not_found.search(error):
                    user_bot.mailing = 'chat not found'
                    await user_bot.aio_save()
                elif compile_bot_blocked.search(error):
                    block_count += 1
                    user_bot.mailing = 'deactivated'
                    await user_bot.aio_save()
                    logger.error(f'user: {user_bot.user_id} | Bot blocked (conversation forbidden)')
                    continue
            except Exception as save_error:
                logger.error(f'Error saving user mailing status: {save_error}')

            error_count += 1
            logger.error(f'user: {user_bot.user_id} | {ex}', exc_info=True)

    try:
        update_text = convert.admin_text(28)
        update_text += convert.admin_text(29).format(
            msg_count=count_sended,
            block_count=block_count,
            flood_count=flood_count,
            error_count=error_count)

        if isinstance(update_message, CallbackQuery):
            await update_message.message.edit_text(text=update_text)
        else:
            await update_message.edit_text(text=update_text)
    except Exception as final_update_error:
        logger.error(f'Error updating final mailing result: {final_update_error}')
        try:
            fallback_text = f"✅ Рассылка завершена!\n\n📊 Результаты:\nОтправлено: {count_sended}\nЗаблокировали: {block_count}\nФлуд: {flood_count}\nОшибки: {error_count}"
            if isinstance(update_message, CallbackQuery):
                await update_message.message.answer(text=fallback_text)
            else:
                await update_message.answer(text=fallback_text)
        except Exception as fallback_error:
            logger.error(f'Fallback message also failed: {fallback_error}')

    logger.info(f"Mailing completed. Results: sent={count_sended}, blocked={block_count}, flood={flood_count}, errors={error_count}")
    return


def add_caption_to_last_element(media_list, caption=None):
    last_element = media_list[-1]
    if hasattr(last_element, 'caption'):
        last_element.caption = caption

    return media_list
