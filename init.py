import logging
import asyncio
import configparser

from aiogram.fsm.storage.redis import RedisStorage, Redis
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from aiogram.client.default import DefaultBotProperties
from peewee_async import PooledPostgresqlDatabase
from aiogram import Bot, Dispatcher
from aiohttp import web

import peewee_async_patch

from telegram.keyboard.share import ShareKeyboard
from telegram.keyboard.admin import KeyboardAdmin
from telegram.keyboard.user import UserKeyboard
from language.converter import Converter


config = configparser.ConfigParser(inline_comment_prefixes="#")
config.read("config.ini")
loop = asyncio.get_event_loop()

logger = logging.getLogger('CS1')
logger.propagate = False
logger.setLevel(logging.DEBUG)

strfmt = "[%(levelname)-2s]: %(message)s (%(filename)s:%(funcName)s:%(lineno)s)"

formatter = logging.Formatter(strfmt)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.info('Set up logger')

database = PooledPostgresqlDatabase(
    user=config['DATABASE']['user'],
    host=config['DATABASE']['host'],
    password=config['DATABASE']['pass'],
    port=int(config['DATABASE']['port']),
    database=config['DATABASE']['db'],
    isolation_level=ISOLATION_LEVEL_READ_COMMITTED
)

from tables import *
Users.create_table(safe=True)
Chat.create_table(safe=True)
Deals.create_table(safe=True)
Mailing.create_table(safe=True)
Reviews.create_table(safe=True)
Invoices.create_table(safe=True)
RefLinks.create_table(safe=True)
Withdrawal.create_table(safe=True)
ShopCategories.create_table(safe=True)
ShopProducts.create_table(safe=True)
ShopInventory.create_table(safe=True)
ShopOrders.create_table(safe=True)

database.close()
database.set_allow_sync(False)

REDIS_HOST = config['REDIS']['host']
REDIS_PORT = config['REDIS']['port']
REDIS_DB = config['REDIS']['db']
REDIS_PASSWORD = config['REDIS']['password']
redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
redis = Redis.from_url(redis_url, decode_responses=True)
storage = RedisStorage(redis=redis)

bot_main = Bot(token=config['BOT']['bot_token'], default=DefaultBotProperties(parse_mode='HTML'))
dp_main = Dispatcher(bot=bot_main, storage=storage)
list_for_delete_messages = []

kb_user = UserKeyboard(config=config)
kb_admin = KeyboardAdmin(config=config)
kb_share = ShareKeyboard()

user_media = {}
media_file_ids = {}
convert = Converter()

from additional.heleket import HeleketAPI
heleket_api = HeleketAPI(config)
