import logging
import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery
from typing import Callable, Any, Awaitable, Dict
from tables import Users
from init import config


logger = logging.getLogger('CS1')


class SingleOperationMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.locks = {}

        self.group_semaphores = {
            'zero_balance': asyncio.Semaphore(10),
            'non_zero_balance': asyncio.Semaphore(10)
        }

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
            logger.debug(f'user: {user_id} | message_text = {event.text}')
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            logger.debug(f'user: {user_id} | callback_data = {event.data}')
        elif isinstance(event, InlineQuery):
            user_id = event.from_user.id

        if user_id is not None:
            if user_id not in self.locks:
                self.locks[user_id] = asyncio.Semaphore(1)

            semaphore = self.locks[user_id]
            await semaphore.acquire()
            try:
                try:
                    user: Users = await Users.aio_get(Users.user_id == user_id)

                    if user.username != event.from_user.username:
                        user.username = event.from_user.username
                        await user.aio_save()

                    if user.full_name != event.from_user.full_name:
                        user.full_name = event.from_user.full_name
                        await user.aio_save()

                except Users.DoesNotExist:
                    user = None

                data['user'] = user

                balance_group = 'zero_balance' if user and user.balance == 0 else 'non_zero_balance'
                group_semaphore = self.group_semaphores[balance_group]

                async with group_semaphore:
                    return await handler(event, data)
            finally:
                semaphore.release()
                if semaphore._value == 1:
                    del self.locks[user_id]
        else:
            return await handler(event, data)
