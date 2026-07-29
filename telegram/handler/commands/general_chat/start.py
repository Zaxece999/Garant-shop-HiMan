from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F, Router
from init import *


router_general_sp = Router()


@router_general_sp.message(CommandStart(), F.chat.id == int(config['CHATS_ID']['general']))
async def start_general(m: Message):

    pass
