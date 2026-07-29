from peewee_async import AioModel
from peewee import *
from init import database


class Reviews(AioModel):
    id = BigAutoField()
    deal_uniq_id = TextField()
    rating = SmallIntegerField()

    from_user_id = BigIntegerField()
    to_user_id = BigIntegerField()
    message = TextField(null=True)
    created = DateTimeField(formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        database = database

    @classmethod
    async def get_user_rating(cls, user_id: int) -> float:
        reviews = await cls.select(
            fn.AVG(cls.rating).alias('avg_rating')
        ).where(
            cls.to_user_id == user_id
        ).aio_scalar()

        return float(reviews) if reviews else 0.0

    @classmethod
    async def has_review(cls, deal_uniq_id: str, from_user_id: int) -> bool:
        return await cls.select().where(
            (cls.deal_uniq_id == deal_uniq_id) &
            (cls.from_user_id == from_user_id)
        ).aio_exists()
