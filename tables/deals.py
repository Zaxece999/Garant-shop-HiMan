from dataclasses import dataclass
from peewee_async import AioModel
from peewee import *


class Deals(AioModel):
    id = BigAutoField()
    uniq_id = TextField(null=True)

    who_start_deal = BigIntegerField(null=True)
    who_seller = BigIntegerField()
    who_buyer = BigIntegerField()

    price = FloatField(null=True)
    status = TextField(default='wait')
    description = TextField()
    who_cancel = BigIntegerField(null=True)
    confirm_seller = BooleanField(default=0)
    confirm_buyer = BooleanField(default=0)
    cancel_seller = BooleanField(default=0)
    cancel_buyer = BooleanField(default=0)

    who_open_disput = BigIntegerField(null=True)
    description_complaint = TextField(null=True)
    who_win_disput = BigIntegerField(null=True)
    admin_disput = BigIntegerField(null=True)

    created = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])
    start_time = DateTimeField(null=True, formats=['%Y-%m-%d %H:%M:%S'])
    end_time = DateTimeField(null=True, formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        from init import database
        database = database

    def amount_to_credited(self, percent_disput: float = 0.0):

        percent_amount_disput = 0.0
        if self.admin_disput is not None:
            percent_amount_disput = self.price * percent_disput

        final_amount = self.price - percent_amount_disput

        final_amount = round(final_amount, 2)

        return {
            "amount": self.price,
            "percent_disput": int(percent_disput * 100),
            "percent_amount_disput": round(percent_amount_disput, 2),
            "final_amount": final_amount
        }


@dataclass
class TypeDeal:
    purchase = 'purchase'
    sell = 'sell'

@dataclass
class StatusDeal:
    active = 'active'
    closed = 'closed'
    canceled = 'canceled'
    wait_confirm = 'wait'
