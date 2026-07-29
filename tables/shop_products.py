from peewee_async import AioModel
from peewee import *


class ShopProducts(AioModel):
    id = BigAutoField()
    category_id = BigIntegerField()
    name = TextField()
    description = TextField(null=True)
    price = FloatField()
    image_url = TextField(null=True)
    is_active = BooleanField(default=True)
    quantity = IntegerField(default=0)
    product_type = TextField(default="key")
    sort_order = IntegerField(default=0)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        from init import database
        database = database
