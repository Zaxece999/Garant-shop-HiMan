import datetime
import asyncio

from tables.mailing import Mailing
from telegram.functions.func import global_mailing

from init import *


async def start_check_mailing():

    logger.debug('Start check for mailing..')

    while True:
        await asyncio.sleep(15)

        try:
            now = datetime.datetime.now()
            wait_mailing: Mailing = await Mailing.aio_get((now > Mailing.time))
        except Mailing.DoesNotExist:
            continue

        main_message = await bot_main.send_message(chat_id=wait_mailing.user_id, text=convert.admin_text(22))

        await asyncio.sleep(3)

        loop.create_task(global_mailing(
            update_message=main_message,
            text=wait_mailing.message,
            photo=wait_mailing.photo_id,
            video=wait_mailing.video_id,
            document=wait_mailing.document_id
        ))

        await wait_mailing.aio_delete_instance()
        continue
