from aiogram.fsm.state import StatesGroup, State


class DealState(StatesGroup):
    enter_user = State()
    enter_amount = State()
    enter_description = State()
    send_message_deal = State()
    write_message_disput = State()


class ReviewState(StatesGroup):
    review_write_comment = State()


class RefillBalance(StatesGroup):
    enter_amount = State()
    enter_amount_transfer = State()
    enter_nick_transfer = State()
    choose_currency = State()
    choose_network = State()
    enter_heleket_amount = State()
    waiting_payment = State()


class UserState(StatesGroup):
    choice_lang = State()
    enter_amount = State()
    withdrawal_amount = State()
    withdrawal_wallet = State()
    enter_new_desc_deal = State()
    enter_price = State()
    enter_token_payment = State()
    enter_new_token_payment = State()


class AdminState(StatesGroup):
    WAITING_FOR_BALANCE = State()
    WAITING_FOR_USER_ID = State()
    WAITING_FOR_MAILING_TEXT = State()
    WAITING_FOR_HASH = State()

    WAITING_FOR_CATEGORY_NAME = State()
    WAITING_FOR_PRODUCT_NAME = State()
    WAITING_FOR_PRODUCT_DESCRIPTION = State()
    WAITING_FOR_PRODUCT_PRICE = State()
    WAITING_FOR_PRODUCT_QUANTITY = State()
    WAITING_FOR_PRODUCT_KEYS = State()
    WAITING_FOR_PRODUCT_CATEGORY = State()
    WAITING_FOR_PRODUCT_IMAGE = State()
    WAITING_FOR_PRODUCT_CONFIRMATION = State()
    WAITING_FOR_INVENTORY_KEYS = State()
    WAITING_FOR_INVENTORY_QUANTITY = State()
    WAITING_FOR_INVENTORY_CONFIRMATION = State()
    WAITING_FOR_EDIT_FIELD = State()
    WAITING_FOR_EDIT_VALUE = State()
    WAITING_FOR_DELETE_CONFIRMATION = State()

    add_balance_enter_user = State()
    add_balance_enter_amount = State()
    add_balance_confirm = State()
    enter_time_mailing = State()
    get_mailing_text = State()
    confirm_mailing = State()
    enter_name_ref = State()
    enter_link_for_chat = State()
    close_deal_enter_id = State()
    close_deal_confirm = State()


class ChatPayment(StatesGroup):
    choose_currency = State()
    choose_network = State()
    waiting_payment = State()
    verify_channel = State()
