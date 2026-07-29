from peewee_async import AioModel
from peewee import *


class ShopInventory(AioModel):
    id = BigAutoField()
    product_id = BigIntegerField()
    content = TextField()
    is_sold = BooleanField(default=False)
    sold_to = BigIntegerField(null=True)
    sold_at = DateTimeField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        from init import database
        database = database
