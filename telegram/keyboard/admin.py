from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from language.keyboard.admin import KAdmin
from configparser import ConfigParser


class KeyboardAdmin(KAdmin):

    def __init__(self, config: ConfigParser):

        self.config = config
        KAdmin.__init__(self)

    def convert_text(self, number):
        return self.adm_kb[number]

    def admin_menu(self, user):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(text=self.convert_text(10), callback_data='usersCount'))
        kb.row(InlineKeyboardButton(text=self.convert_text(11), callback_data='usersBalance'))
        kb.row(InlineKeyboardButton(text=self.convert_text(13), callback_data='addBalance'))
        kb.row(InlineKeyboardButton(text=self.convert_text(14), callback_data='makeMailing'))
        kb.row(InlineKeyboardButton(text=self.convert_text(48), callback_data='adminCloseDeal'))
        kb.row(InlineKeyboardButton(text=self.convert_text(49), callback_data='checkPayment'))
        kb.row(InlineKeyboardButton(text=self.convert_text(50), callback_data='admin_shop'))

        return kb.as_markup()

    def confirm_yes_cancel(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.convert_text(20), callback_data='yes'))
        kb.row(InlineKeyboardButton(text=self.convert_text(22), callback_data='enterTime'))
        kb.row(InlineKeyboardButton(text=self.convert_text(21), callback_data='cancel'))
        return kb.as_markup()

    def deleteAutoMailing(self, mailing):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.convert_text(30), callback_data=f'deleteAutoMailing_{mailing.id}'))
        return kb.as_markup()

    def accept_disput(self, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.convert_text(40), callback_data=f'acceptDisput_{deal_uniq_id}'))
        return kb.as_markup()

    def go_to_complaint(self, username, link_to_go):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=username, callback_data='randomSmile'))
        kb.row(InlineKeyboardButton(text=self.convert_text(41), url=link_to_go))
        return kb.as_markup()

    def control_panel_disput(self, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.convert_text(42), callback_data=f'sendLinkChatDisput_{deal_uniq_id}'))
        kb.row(InlineKeyboardButton(text=self.convert_text(43), callback_data=f'getCloseDisput_{deal_uniq_id}'))
        return kb.as_markup()

    def status_withdrawal(self, user_id, withdrawal_id=None, success=False):
        kb = InlineKeyboardBuilder()

        callback_data = f"{user_id}"
        if withdrawal_id:
            callback_data = f"withdrawal_{user_id}_{withdrawal_id}"

        if success is False:
            kb.row(InlineKeyboardButton(text=self.convert_text(44), callback_data=callback_data))
        else:
            kb.row(InlineKeyboardButton(text=self.convert_text(45), callback_data=callback_data))

        return kb.as_markup()

    def close_disput(self, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text=self.convert_text(46), callback_data=f'closeDisput_{deal_uniq_id}_seller'),
            InlineKeyboardButton(text=self.convert_text(47), callback_data=f'closeDisput_{deal_uniq_id}_buyer')
        )
        kb.row(InlineKeyboardButton(text=self.convert_text(0), callback_data='hide'))
        return kb.as_markup()

    def btn_cancel(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.convert_text(0), callback_data='admin'))
        return kb.as_markup()
