from dataclasses import dataclass

from peewee_async import AioModel
from peewee import *


class Withdrawal(AioModel):
    id = BigAutoField()
    user_id = BigIntegerField()
    uniq_id = TextField()
    amount = FloatField()
    method = TextField()
    wallet_address = TextField(null=True)
    created = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        from init import database
        database = database

    def get_wallet_address(self):
        try:
            return self.wallet_address or "Не указан"
        except (AttributeError, Exception):
            return "Не указан"


@dataclass
class MethodWithdrawal:
    usdt_bep20 = 'usdt_bep20'
    usdt_erc20 = 'usdt_erc20'
