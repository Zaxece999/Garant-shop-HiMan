from peewee_async import AioModel
from peewee import *


class Users(AioModel):
    id = BigAutoField()
    user_id = BigIntegerField()
    username = TextField(null=True)
    full_name = TextField(null=True)
    nickname = TextField()

    lang = CharField(max_length=2, default='no')
    admin = SmallIntegerField(default=0)
    balance = FloatField(default=0)
    when_start = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    referral = BigIntegerField(null=True)
    mailing = TextField(null=True)

    anti_flood_deal = DateTimeField(null=True, formats=['%Y-%m-%d %H:%M:%S'])

    def more_info_user(self):
        return f'@{self.username} {self.user_id}' if self.username else f'{self.full_name} {self.user_id}'

    def info_user(self):
        return f'@{self.username}' if self.username else self.full_name

    class Meta:
        from init import database
        database = database
