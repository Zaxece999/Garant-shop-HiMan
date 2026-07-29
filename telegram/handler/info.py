import logging
import typing

from aiogram.fsm.context import FSMContext
from telegram.misc.states import UserState
from aiogram import F, Router
from peewee import fn

from telegram.functions.func import get_main_menu
from additional.functions import *
from tables import *
from init import *


logger = logging.getLogger('CS1')


router_info = Router()


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='information')))
async def menu_info(m: Message, user: Users):

    await m.answer(
        text=convert.share(10).format(my_user_id=user.user_id, smile_random=get_random_smile()),
        reply_markup=kb_user.info_menu(user))


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key=70)))
async def menu_info(m: Message, user: Users):
    await m.answer(text=convert.cv(72, user).format(
        smile_random=get_random_smile(),
        link_admin=config['LINKS']['admin']
    ))
    return


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key=74)))
async def get_rules(m: Message, user: Users):
    await m.answer(
        text=convert.cv(70, user),
        reply_markup=kb_user.info_inline_admin(user))
    return


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key=75)))
async def get_instructions(m: Message, user: Users):
    await m.answer(text=convert.cv(74, user))
    return


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key=71)))
async def my_ref(m: Message, user: Users):
    bot = await m.bot.me()
    my_ref = f'https://t.me/{bot.username}?start={user.nickname}'

    count_ref_result = await Users.select(
        fn.COUNT(Users.id).alias('cnt')
    ).where(
        Users.referral == user.user_id
    ).aio_execute()
    count_ref = count_ref_result[0].cnt

    await m.answer(
        text=convert.cv(73, user).format(
            ref_link=my_ref,
            link_admin=config['LINKS']['admin'],
            percent_ref=config.getfloat('PRICES', 'toup_ref'),
            my_count_ref=count_ref),
        reply_markup=kb_user.my_ref(user=user, ref_link=my_ref))
    return


@router_info.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key=76)))
async def change_language(m: Message, user: Users, state: FSMContext):
    await state.set_state(UserState.choice_lang)
    await m.answer(text=convert.share(10), reply_markup=kb_share.choice_language())
    return


@router_info.message(UserState.choice_lang, F.chat.type == 'private')
async def choice_language(m: Message, user: Users, state: FSMContext):

    if m.text.lower() == 'русский':
        user.lang = 'ru'
    else:
        user.lang = 'en'
    await user.aio_save()

    await get_main_menu(bot=m.bot, user=user, state=state)
    return


@router_info.callback_query(F.data == 'withdrawalCashback')
async def withdrawal_cashback(c: CallbackQuery, user: Users):

    if user.cashback < 0.30:
        return await c.answer(text=convert.cv(92, user).format(amount=0.30), show_alert=True)

    await c.answer(text=convert.cv(93, user).format(amount=user.cashback), show_alert=True)

    old_balance = user.balance
    async with database.aio_atomic():
        await Users.update(balance = Users.balance + user.cashback, cashback = 0).where(Users.id == user.id).aio_execute()
        user: Users = await Users.aio_get(Users.id == user.id)

    logger.info(
        f'user: {user.user_id=} success withdrawal cashback\n'
        f'{" " * 14}{old_balance=} -> {user.balance=}')

    return


@router_info.callback_query(F.data == 'resetApiKey')
async def withdrawal_cashback(c: CallbackQuery, user: Users):

    new_api_key = f'{user.nickname}:{generate_random_string(8)}'
    user.api_key = new_api_key
    await user.aio_save()

    await c.message.edit_text(
        text=convert.cv(100, user).format(
            api_key=user.api_key),
        reply_markup=kb_user.my_api(user=user))
    await c.answer(text='✅')
    return
