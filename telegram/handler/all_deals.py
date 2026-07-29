import logging
import typing

from aiogram import F, Router
from aiogram.types import CallbackQuery

from tables import *
from init import *


logger = logging.getLogger('CS1')


router_all_deals = Router()


@router_all_deals.callback_query(F.data.startswith("getPageDeals"))
async def get_page_deals(c: CallbackQuery, user: Users):
    page_number = int(c.data.split("_")[1])

    all_deals: typing.List[Deals] = await Deals.select().where(
        (Deals.who_buyer == user.user_id) |
        (Deals.who_seller == user.user_id)
    ).order_by(Deals.id.desc()).aio_execute()

    await c.message.edit_text(
        text=convert.cv(702, user).format(page_number=page_number + 1),
        reply_markup=kb_user.my_deals(user=user, deals=all_deals, page_number=page_number))
    return
