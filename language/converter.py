from language.text.russian import Russian
from language.text.english import English
from language.text.admin import Admin
from language.text.share import Share


class Converter(Admin, Share, Russian, English):
    def __init__(self):

        Admin.__init__(self)
        Share.__init__(self)
        Russian.__init__(self)
        English.__init__(self)

    def share(self, key):
        return self.share_text[key]

    def admin_text(self, key):
        return self.adm_text[key]

    def cv(self, key, user):

        if user.lang == 'ru':
            return self.ru_text[key]
        elif user.lang == 'en':
            return self.en_text[key]
