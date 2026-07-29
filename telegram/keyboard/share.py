from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types.keyboard_button import KeyboardButton
from language.keyboard.share import KShare


class ShareKeyboard(KShare):

    def __init__(self):
        KShare.__init__(self)

    def get_text(self, number):
        return self.kb[number]

    def choice_language(self):
        kb = ReplyKeyboardBuilder()

        kb.row(
            KeyboardButton(text=self.get_text('lang russian')),
            KeyboardButton(text=self.get_text('lang english'))
        )

        return kb.as_markup(resize_keyboard=True)
