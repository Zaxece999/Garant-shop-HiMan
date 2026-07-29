import logging
from datetime import datetime
from random import randint

from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F, Router

from telegram.functions.func import *
from telegram.misc.states import UserState
from names import get_first_name
from init import *


logger = logging.getLogger('CS1')


router_private_sp = Router()

@router_private_sp.message(CommandStart(), F.chat.type == 'private')
async def start_private(m: Message, user: Users, state: FSMContext, command: CommandObject):

    if user is None:

        nickname = f'{get_first_name()}-{randint(1000, 9999)}'
        user: Users = await Users.aio_create(
            user_id=m.from_user.id,
            nickname=nickname,
            when_start=datetime.now())

        if command.args:
            argument = command.args.split("_")

            try:
                ref_user: Users = await Users.aio_get(Users.nickname == argument[0])
                user.referral = ref_user.user_id
                await user.aio_save()
            except Users.DoesNotExist:
                pass

            try:
                ref_link: RefLinks = await RefLinks.aio_get(RefLinks.link_arg == argument[0])
                ref_link.clicks += 1
                await ref_link.aio_save()
            except RefLinks.DoesNotExist:
                pass
    else:
        if command.args:
            argument = command.args.split("_")
            if argument[0] == "complaint":

                deal_uniq_id = argument[1]
                deal: Deals = await Deals.aio_get(Deals.uniq_id == deal_uniq_id)
                if deal.admin_disput != user.user_id and user.admin == 0:
                    return await m.answer(text=convert.admin_text(43))

                seller_user: Users = await Users.aio_get(Users.user_id == deal.who_seller)
                buyer_user: Users = await Users.aio_get(Users.user_id == deal.who_buyer)

                if deal.who_open_disput == seller_user.user_id:
                    who_accused_in_deal = buyer_user.more_info_user()
                else:
                    who_accused_in_deal = seller_user.more_info_user()

                await m.answer(
                    text=convert.admin_text(42).format(
                        uniq_id=deal.uniq_id,
                        who_seller_nickname=seller_user.more_info_user(),
                        who_buyer_nickname=buyer_user.more_info_user(),
                        amount=float(deal.price),
                        description=deal.description,
                        complaint=deal.description_complaint,
                        who_accused_in_deal=who_accused_in_deal
                    ),
                    reply_markup=kb_admin.control_panel_disput(deal_uniq_id=deal.uniq_id)
                )
                return

    if user.lang == 'no':
        await state.set_state(UserState.choice_lang)
        await m.answer(text=convert.share(10), reply_markup=kb_share.choice_language())
        return

    return await get_main_menu(bot=m.bot, user=user, state=state)
