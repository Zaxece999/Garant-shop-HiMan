from peewee_async import AioModel
from peewee import *


class ShopCategories(AioModel):
    id = BigAutoField()
    name = TextField()
    description = TextField(null=True)
    image_url = TextField(null=True)
    is_active = BooleanField(default=True)
    sort_order = IntegerField(default=0)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        from init import database
        database = database
