import logging
import typing

from aiogram.types import FSInputFile, Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import F, Router

from additional.functions import *
from telegram.functions.func import get_main_menu, send_log
from telegram.misc.states import *
from tables.deals import StatusDeal
from peewee import fn, Case
from tables import *
from init import *

logger = logging.getLogger('CS1')

router_menu = Router()


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='start deal')))
async def menu_start_deal(m: Message, user: Users, state: FSMContext):

    await m.answer(
        text=convert.cv(500, user),
        reply_markup=kb_user.btn_menu(user=user))

    await state.set_state(DealState.enter_user)
    return


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='all deals')))
async def all_my_deals(m: Message, user: Users):

    all_deals: typing.List[Deals] = await Deals.select().where(
        (Deals.who_buyer == user.user_id) |
        (Deals.who_seller == user.user_id)
    ).order_by(Deals.id.desc()).aio_execute()
    if not all_deals:
        await m.answer(text=convert.cv(700, user))
        return

    await m.answer(
        text=convert.cv(701, user),
        reply_markup=kb_user.my_deals(user=user, deals=all_deals, page_number=0))
    return


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='my profile')))
async def my_profile(m: Message, user: Users):

    count_deals_user = await Deals.select(
        fn.COUNT(Deals.id).alias('count_deals_user'),
        fn.COUNT(Case(
            None,
            [(Deals.who_win_disput.is_null(False) & (Deals.who_win_disput != user.user_id), Deals.id)],
        )).alias('count_lost_disputes'),
        fn.COALESCE(fn.SUM(Case(
            None,
            [(Deals.who_buyer == user.user_id, Deals.price)],
            0
        )), 0).alias('purchase_amount'),
        fn.COALESCE(fn.SUM(Case(
            None,
            [(Deals.who_seller == user.user_id, Deals.price)],
            0
        )), 0).alias('sell_amount')
    ).where(
        (
            (Deals.who_seller == user.user_id) |
            (Deals.who_buyer == user.user_id)
        ) &
        (Deals.status == StatusDeal.closed)
    ).aio_execute()

    rating = await Reviews.select(
        fn.COUNT(Reviews.id).alias('count_reviews'),
        fn.AVG(Reviews.rating).alias('average_rating')
    ).where(Reviews.to_user_id == user.user_id).aio_execute()

    count_reviews = rating[0].count_reviews
    average_rating = rating[0].average_rating
    if not average_rating:
        average_rating = 0.00

    if average_rating % 1 == 0:
        formatted_rating = int(average_rating)
    else:
        formatted_rating = round(average_rating, 2)

    await m.answer(
        text=convert.cv('my profile', user).format(
            user_info=user.info_user(),
            user_id=user.user_id,
            smile_money=get_random_smile('money'),
            balance=user.balance,
            success_count_deals=count_deals_user[0].count_deals_user,
            lost_disputes=count_deals_user[0].count_lost_disputes,
            share_amount_buy=count_deals_user[0].purchase_amount,
            share_amount_sell=count_deals_user[0].sell_amount,
            count_reviews=count_reviews,
            word_review=word_declesion(count_reviews, 'review', user.lang),
            avg_percent=formatted_rating),
        reply_markup=kb_user.reviews_check(user=user))
    return


@router_menu.callback_query(lambda c: c.data.split("_")[0] == 'checkReviews')
async def check_reviews(c: CallbackQuery, user: Users):
    user_id = c.data.split('_')[1]

    reviews: typing.List[Reviews] = await Reviews.select().where(
        (Reviews.to_user_id == user_id)
    ).order_by(
        Reviews.id.desc()
    ).aio_execute()
    if not reviews:
        return await c.answer(text=convert.cv(900, user), show_alert=True)
    await c.answer(cache_time=1)

    await c.message.answer(
        text=convert.cv(901, user).format(page_number=1),
        reply_markup=kb_user.reviews_user(
            user=user,
            reviews=reviews,
            page_number=0
        )
    )
    return

@router_menu.callback_query(lambda c: c.data.split("_")[0] == 'nextPageReviews')
async def next_page_review(c: CallbackQuery, user: Users):
    data = c.data.split("_")
    user_id = data[1]
    page_number = int(data[2])

    reviews: typing.List[Reviews] = await Reviews.select().where(
        (Reviews.to_user_id == user_id)
    ).order_by(
        Reviews.id.desc()
    ).aio_execute()

    await c.message.edit_text(
        text=convert.cv(901, user).format(page_number=page_number + 1),
        reply_markup=kb_user.reviews_user(
            user=user,
            reviews=reviews,
            page_number=page_number
        )
    )
    return


@router_menu.callback_query(lambda c: c.data.split("_")[0] == 'checkReview')
async def check_review(c: CallbackQuery, user: Users):
    data = c.data.split('_')
    review_id = data[1]
    page_number = data[2]

    this_review: Reviews = await Reviews.aio_get(Reviews.id == review_id)
    from_user: Users = await Users.aio_get(Users.user_id == this_review.from_user_id)

    now = datetime.datetime.now()

    if not this_review.message:
        comment = convert.cv(903, user)
    else:
        comment = this_review.message

    await c.message.edit_text(
        text=convert.cv(902, user).format(
            nickname_user=from_user.info_user(),
            message=comment,
            smile_time=get_random_smile('time'),
            when_write=format_duration(now - this_review.created, user.lang)
        ),
        reply_markup=kb_user.btn_back(user=user, callback=f'nextPageReviews_{this_review.to_user_id}_{page_number}'))


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='menu')))
async def menu(m: Message, user: Users, state: FSMContext):
    await state.clear()
    await get_main_menu(bot=m.bot, user=user, state=state)
    return


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='withdrawal')))
async def withdrawal(m: Message, user: Users, state: FSMContext):

    minimum_amount = config.getfloat('GARANT', 'min_withdrawal')
    if user.balance < minimum_amount:
        return await m.answer(text=convert.cv(800, user).format(
            smile_spanch=get_random_smile(),
            need_amount=minimum_amount
        ))

    await state.set_state(UserState.withdrawal_amount)
    await m.answer(
        text=convert.cv(801, user).format(
            smile_money=get_random_smile('money'),
            balance=user.balance,
            min_withdrawal=minimum_amount
        ),
        reply_markup=kb_user.btn_menu(user=user))
    return


@router_menu.callback_query(F.data == 'cancel')
async def cancel(c: CallbackQuery, user: Users, state: FSMContext):
    await state.clear()
    await c.message.delete()
    await c.answer()
    return


@router_menu.callback_query(F.data == 'hide')
async def delete_message(c: CallbackQuery):
    await c.message.delete()
    await c.answer()
    return


@router_menu.callback_query(F.data == 'randomSmile')
async def answer_random_smile(c: CallbackQuery):
    random_smile = get_random_smile()
    await c.answer(text=random_smile)
    return


@router_menu.message(F.chat.type == 'private', F.text.in_(kb_user.get_text(key='chat')))
async def chat_button_handler(m: Message, user: Users, state: FSMContext):
    logger.info(f"🔘 Нажата кнопка CHAT пользователем {user.user_id}")

    try:
        chat_member = await m.bot.get_chat_member(chat_id=config['CHATS_ID']['general'], user_id=user.user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="Join Private Chat", url=config['LINKS']['private_chat']))
            await m.answer(
                text="✅ You already have access to the private chat! Click below to join:",
                reply_markup=kb.as_markup()
            )
            return
    except Exception as e:
        logger.error(f"❌ Error checking access for {user.user_id}: {str(e)}")

    logger.info(f"💰 Showing payment message to user {user.user_id}")

    text = (
        "💰 Entry costs $40 — after payment, you'll get the private link in chat.\n\n"
        "📲 Your $40 stays on your balance in @ESCROWRBOT and can be used for any deal.\n"
        "🛑 No noise. No scammers. Only verified users.\n"
        f"💼 Admin @{config['BOT']['owner_username']}   group @{config['BOT']['channel_username']}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Pay", callback_data="chat_payment_start"))
    await m.answer(text=text, reply_markup=kb.as_markup())

@router_menu.callback_query(lambda c: c.data == "chat_payment_start")
async def chat_payment_start(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()

    await state.set_state(ChatPayment.choose_currency)
    await state.update_data(amount=40)

    kb_curr = InlineKeyboardBuilder()
    kb_curr.row(InlineKeyboardButton(text='💰 USDT', callback_data='chat_currency_USDT'))
    kb_curr.row(InlineKeyboardButton(text='₿ BTC', callback_data='chat_currency_BTC'))
    kb_curr.row(InlineKeyboardButton(text='Ξ ETH', callback_data='chat_currency_ETH'))
    kb_curr.row(InlineKeyboardButton(text='Ł LTC', callback_data='chat_currency_LTC'))
    kb_curr.row(InlineKeyboardButton(text='Cancel', callback_data='back_to_chat'))
    reply_markup=kb_curr.as_markup()

    await c.message.edit_text(
        text=f"""💰 Entry costs $40 — after payment, you'll get the private link in chat.

📲 Your $40 stays on your balance in @ESCROWRBOT and can be used for any deal.
🛑 No noise. No scammers. Only verified users.
💼 Admin @{config['BOT']['owner_username']} group @{config['BOT']['channel_username']}""",
        reply_markup=reply_markup
    )

@router_menu.callback_query(lambda cb: cb.data.startswith("chat_currency_"))
async def chat_currency_selection(c: CallbackQuery, user: Users, state: FSMContext):
    currency = c.data.split('_')[2]
    await c.answer(cache_time=3)

    state_data = await state.get_data()

    await state.update_data(currency=currency)
    await state.set_state(ChatPayment.choose_network)

    kb_net = InlineKeyboardBuilder()
    if currency == 'USDT':
        kb_net.row(InlineKeyboardButton(text='🔄 TRC20', callback_data='chat_network_TRC20'))
        kb_net.row(InlineKeyboardButton(text='🔄 ERC20', callback_data='chat_network_ERC20'))
        kb_net.row(InlineKeyboardButton(text='🔄 BEP20 (BSC)', callback_data='chat_network_BEP20'))
    elif currency == 'BTC':
        kb_net.row(InlineKeyboardButton(text='🔄 Bitcoin', callback_data='chat_network_BTC'))
        kb_net.row(InlineKeyboardButton(text='🔄 Lightning', callback_data='chat_network_LIGHTNING'))
    elif currency == 'ETH':
        kb_net.row(InlineKeyboardButton(text='🔄 Ethereum', callback_data='chat_network_ETH'))
    elif currency == 'LTC':
        kb_net.row(InlineKeyboardButton(text='🔄 Litecoin', callback_data='chat_network_LTC'))
    kb_net.row(InlineKeyboardButton(text='Cancel', callback_data='back_to_chat'))
    reply_markup=kb_net.as_markup()

    await c.message.edit_text(
        text=f"Select network for {currency} payment:",
        reply_markup=reply_markup
    )

@router_menu.callback_query(lambda cb: cb.data.startswith("chat_network_"))
async def chat_network_selection(c: CallbackQuery, user: Users, state: FSMContext):
    network = c.data.split('_')[2]
    await c.answer(cache_time=3)

    state_data = await state.get_data()
    amount = state_data.get('amount')
    currency = state_data.get('currency')

    logger.info(f"Creating Heleket invoice for chat access - Amount: {amount}, Currency: {currency}, Network: {network}")

    try:
        draft_invoice_data = await heleket_api.create_invoice(
            amount=amount,
            currency=currency,
            network=network,
            is_crypto_amount=False
        )

        if not draft_invoice_data:
            logger.error(f"Failed to create draft Heleket invoice for user {user.user_id}")
            return await c.message.edit_text(
                text="❌ Failed to create payment. Please try again later.",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text="Back", callback_data="back_to_chat")
                ).as_markup()
            )

        exact_crypto_amount = draft_invoice_data.get('payer_amount')

        if not exact_crypto_amount:
            logger.error(f"Failed to get crypto amount from Heleket API for user {user.user_id}")
            return await c.message.edit_text(
                text="❌ Failed to create payment. Please try again later.",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text="Back", callback_data="back_to_chat")
                ).as_markup()
            )

        logger.info(f"Got exact crypto amount: {exact_crypto_amount} {currency} for {amount} USD")

        invoice_data = await heleket_api.create_invoice(
            amount=exact_crypto_amount,
            currency=currency,
            network=network,
            is_crypto_amount=True
        )

        if not invoice_data:
            logger.error(f"Failed to create Heleket invoice for user {user.user_id}")
            return await c.message.edit_text(
                text="❌ Failed to create payment. Please try again later.",
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(text="Back", callback_data="back_to_chat")
                ).as_markup()
            )

        invoice_id = invoice_data.get('id') or invoice_data.get('payment_id')
        payment_address = invoice_data.get('address') or invoice_data.get('payment_address')
        invoice_hash = invoice_data.get('hash') or invoice_data.get('invoice_hash')

        invoice = await Invoices.aio_create(
            hash=invoice_hash,
            user_id=user.user_id,
            amount=amount,
            provider='heleket',
            currency=currency,
            network=network,
            payment_address=payment_address,
            invoice_id=invoice_id,
            payment_type='chat'
        )

        logger.info(
            f'Created chat payment invoice for user: {user.user_id}\n'
            f'{" " * 14}invoice_id={invoice_id}\n'
            f'{" " * 14}amount={exact_crypto_amount} {currency} ({network})')

        payment_text = f"""🔒 Invoice <code>#{invoice_hash}</code>

Payment address:
<code>{payment_address}</code>

Amount: <code>{exact_crypto_amount}</code> {currency}
Network: {network}

‼️ After transferring, click the 'Check' button ‼️
Transfer the exact amount to avoid losing money!
Consider the network fee!"""

        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="✅ Check payment", callback_data=f"check_chat_payment_{invoice_id}"))
        kb.row(InlineKeyboardButton(text="❌ Cancel", callback_data="back_to_chat"))

        await state.set_state(ChatPayment.waiting_payment)
        await state.update_data(invoice_id=invoice_id)

        await c.message.edit_text(text=payment_text, reply_markup=kb.as_markup())

    except Exception as e:
        logger.error(f"Error creating chat payment: {e}")
        await c.message.edit_text(
            text="❌ Error creating payment. Please try again later.",
            reply_markup=InlineKeyboardBuilder().row(
                InlineKeyboardButton(text="Back", callback_data="back_to_chat")
            ).as_markup()
        )

@router_menu.callback_query(lambda c: c.data.startswith("check_chat_payment_"))
async def check_chat_payment(c: CallbackQuery, user: Users, state: FSMContext):
    invoice_id = c.data.split('_')[-1]

    logger.info(f"Checking chat payment for user={user.user_id}, invoice_id={invoice_id}")

    payment_data = await heleket_api.check_payment(invoice_id)

    if not payment_data:
        await c.answer("Payment not found or still pending. Please try again later.", show_alert=True)
        return

    payment_status = payment_data.get('status', '').lower()
    logger.info(f"Payment status: {payment_status} for invoice_id={invoice_id}")

    successful_statuses = ['paid', 'paid_over', 'success', 'completed', 'confirmed', 'wrong_amount_waiting']

    if payment_status == 'wrong_amount_waiting':
        payer_amount = float(payment_data.get('payer_amount', '0'))
        if payer_amount > 0:
            logger.info(f"Force accepting payment with wrong_amount_waiting, amount received: {payer_amount}")
            payment_status = 'paid'

    if payment_status not in successful_statuses:
        await c.answer("Payment not received yet. Please try again later.", show_alert=True)
        return

    try:
        invoice = await Invoices.aio_get(Invoices.invoice_id == invoice_id)

        if invoice.status == 'paid':
            logger.info(f"Invoice {invoice_id} already processed for user {user.user_id}")

            try:
                await send_log(
                    f'💬 Chat access paid \n'
                    f'👤 User: {user.more_info_user()}\n'
                    f'💰 Amount: {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                    f'🔗 Hash: {invoice.hash}\n'
                    f'🆔 Invoice ID: {invoice.invoice_id}'
                )
            except Exception as e:
                logger.error(f'Error sending chat payment log: {e}')

            try:
                chat_member = await c.bot.get_chat_member(chat_id=config['CHATS_ID']['channel'], user_id=user.user_id)
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    kb = InlineKeyboardBuilder()
                    kb.row(InlineKeyboardButton(text=f"Join @{config['BOT']['channel_username']}", url=config['LINKS']['channel']))
                    kb.row(InlineKeyboardButton(text="I've joined ✅", callback_data="verify_channel_join"))

                    await c.message.edit_text(
                        text="To access the private chat, you need to join our channel first:",
                        reply_markup=kb.as_markup()
                    )
                else:
                    kb = InlineKeyboardBuilder()
                    kb.row(InlineKeyboardButton(text="Join Private Chat", url=config['LINKS']['private_chat']))

                    await c.message.edit_text(
                        text="✅ Payment received and processed! Here's your private chat link:",
                        reply_markup=kb.as_markup()
                    )
            except Exception as e:
                logger.error(f"Error checking channel membership: {e}")
                kb = InlineKeyboardBuilder()
                kb.row(InlineKeyboardButton(text=f"Join @{config['BOT']['channel_username']}", url=config['LINKS']['channel']))
                kb.row(InlineKeyboardButton(text="I've joined ✅", callback_data="verify_channel_join"))

                await c.message.edit_text(
                    text="To access the private chat, you need to join our channel first:",
                    reply_markup=kb.as_markup()
                )
            return

        elif invoice.status == 'wait':
            logger.info(f"Processing pending invoice {invoice_id} for user {user.user_id}")

            async with database.aio_atomic():
                invoice.status = 'paid'
                await invoice.aio_save()

                old_balance = user.balance
                user.balance += invoice.amount
                await user.aio_save()

            logger.info(f"Chat payment processed - invoice {invoice_id} for user {user.user_id}")

            try:
                await send_log(
                    f'💬 Chat access paid\n'
                    f'👤 User: {user.more_info_user()}\n'
                    f'💰 Amount: {invoice.amount:.2f}$ ({invoice.currency}, {invoice.network})\n'
                    f'🔗 Hash: {invoice.hash}\n'
                    f'🆔 Invoice ID: {invoice.invoice_id}'
                )
            except Exception as e:
                logger.error(f'Error sending chat payment log: {e}')

            try:
                chat_member = await c.bot.get_chat_member(chat_id=config['CHATS_ID']['channel'], user_id=user.user_id)
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    kb = InlineKeyboardBuilder()
                    kb.row(InlineKeyboardButton(text=f"Join @{config['BOT']['channel_username']}", url=config['LINKS']['channel']))
                    kb.row(InlineKeyboardButton(text="I've joined ✅", callback_data="verify_channel_join"))

                    await state.set_state(ChatPayment.verify_channel)

                    await c.message.edit_text(
                        text="✅ Payment received! To access the private chat, you need to join our channel first:",
                        reply_markup=kb.as_markup()
                    )
                else:
                    kb = InlineKeyboardBuilder()
                    kb.row(InlineKeyboardButton(text="Join Private Chat", url=config['LINKS']['private_chat']))

                    await state.clear()

                    await c.message.edit_text(
                        text="✅ Payment received and processed! Here's your private chat link:",
                        reply_markup=kb.as_markup()
                    )
            except Exception as e:
                logger.error(f"Error checking channel membership: {e}")
                kb = InlineKeyboardBuilder()
                kb.row(InlineKeyboardButton(text=f"Join @{config['BOT']['channel_username']}", url=config['LINKS']['channel']))
                kb.row(InlineKeyboardButton(text="I've joined ✅", callback_data="verify_channel_join"))

                await state.set_state(ChatPayment.verify_channel)

                await c.message.edit_text(
                    text="✅ Payment received! To access the private chat, you need to join our channel first:",
                    reply_markup=kb.as_markup()
                )

    except Exception as e:
        logger.error(f"Error processing chat payment: {e}")
        await c.answer("Error processing payment. Please try again later.", show_alert=True)

@router_menu.callback_query(lambda c: c.data == "verify_channel_join")
async def verify_channel_join(c: CallbackQuery, user: Users, state: FSMContext):
    await c.answer()

    try:
        chat_member = await c.bot.get_chat_member(chat_id=config['CHATS_ID']['channel'], user_id=user.user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="Join Private Chat", url=config['LINKS']['private_chat']))

            await state.clear()

            await c.message.edit_text(
                text="✅ Channel joined! Here's your private chat link:",
                reply_markup=kb.as_markup()
            )
        else:
            await c.answer("You haven't joined the channel yet!", show_alert=True)
    except Exception as e:
        logger.error(f"Error verifying channel membership: {e}")
        await c.answer("Error checking channel membership. Please try again.", show_alert=True)

@router_menu.callback_query(lambda c: c.data == "back_to_chat")
async def back_to_chat(c: CallbackQuery, user: Users, state: FSMContext):
    await state.clear()
    await c.message.delete()
    await c.answer("Payment cancelled", show_alert=False)

@router_menu.message(Command("start"))
async def command_start(m: Message, user: Users, state: FSMContext):
    if user.lang == 'no':
        await state.set_state(UserState.choice_lang)
        await m.answer(text=convert.share(10), reply_markup=kb_share.choice_language())
        return

    return await get_main_menu(bot=m.bot, user=user, state=state)
