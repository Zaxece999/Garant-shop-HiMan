from peewee_async import AioModel
from peewee import *


class ShopOrders(AioModel):
    id = BigAutoField()
    user_id = BigIntegerField()
    product_id = BigIntegerField()
    product_name = TextField(null=True)
    product_type = TextField(null=True)
    inventory_id = BigIntegerField(null=True)
    inventory_content = TextField(null=True)
    amount = FloatField()
    status = TextField(default="pending")
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    completed_at = DateTimeField(null=True)

    class Meta:
        from init import database
        database = database
