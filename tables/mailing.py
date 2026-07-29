from peewee_async import AioModel
from peewee import *


class Mailing(AioModel):
    id = BigAutoField()
    user_id = BigIntegerField()

    message = TextField(null=True)
    photo_id = TextField(null=True)
    video_id = TextField(null=True)
    document_id = TextField(null=True)

    time = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        from init import database
        database = database
