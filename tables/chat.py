from peewee_async import AioModel
from peewee import *


class Chat(AioModel):
    id = BigAutoField()

    uniq_id_deal = TextField()
    user_id = BigIntegerField()
    text = TextField(null=True)
    attachments = TextField(null=True)

    created = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        from init import database
        database = database
