from peewee_async import AioModel
from peewee import *


class Invoices(AioModel):
    id = BigAutoField()
    user_id = BigIntegerField()
    hash = TextField()
    invoice_id = TextField(null=True)
    amount = FloatField()
    status = TextField(default='wait')
    provider = TextField(default='cryptobot')
    currency = TextField(null=True)
    network = TextField(null=True)
    payment_address = TextField(null=True)

    paid_at = TextField(null=True)
    paid_amount = TextField(null=True)
    paid_asset = TextField(null=True)
    paid_usd_rate = TextField(null=True)
    fee_amount = TextField(null=True)
    description = TextField(null=True)
    pay_url = TextField(null=True)
    bot_invoice_url = TextField(null=True)

    class Meta:
        from init import database
        database = database
