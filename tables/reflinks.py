from peewee_async import AioModel
from peewee import *


class RefLinks(AioModel):
    id = BigAutoField()
    name = TextField()
    link_arg = TextField()
    clicks = IntegerField(default=0)

    class Meta:
        from init import database
        database = database
