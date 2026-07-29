import peewee_async
import peewee


async def aio_save(self, force_insert=False, only=None):
    field_dict = self.__data__.copy()
    if self._meta.primary_key is not False:
        pk_field = self._meta.primary_key
        pk_value = self._pk
    else:
        pk_field = pk_value = None
    if only is not None:
        field_dict = self._prune_fields(field_dict, only)
    elif self._meta.only_save_dirty and not force_insert:
        field_dict = self._prune_fields(field_dict, self.dirty_fields)
        if not field_dict:
            self._dirty.clear()
            return False
    self._populate_unsaved_relations(field_dict)
    if self._meta.auto_increment and pk_value is None:
        field_dict.pop(pk_field.name, None)
    if pk_value is not None and not force_insert:
        if self._meta.composite_key:
            for pk_part_name in pk_field.field_names:
                field_dict.pop(pk_part_name, None)
        else:
            field_dict.pop(pk_field.name, None)
        if not field_dict:
            raise ValueError('no data to save!')
        rows = await self.update(**field_dict).where(self._pk_expr()).aio_execute()
    elif pk_field is not None:
        pk = await self.insert(**field_dict).aio_execute()
        if pk is not None and (self._meta.auto_increment or pk_value is None):
            self._pk = pk
            self._dirty.discard(pk_field.name)
    else:
        await self.insert(**field_dict).aio_execute()
    self._dirty -= set(field_dict)
    return True


async def aio_delete_instance(self, recursive=False, delete_nullable=False):
    if recursive:
        dependencies = self.dependencies()
        for query, fk in reversed(list(dependencies)):
            if fk.null_type == peewee.NULL_TYPE:
                query = query.naive()
            if delete_nullable and fk.null_type == peewee.NULL_TYPE:
                await query.aio_execute()
            else:
                await query.aio_execute()
    return await self.delete().where(self._pk_expr()).aio_execute()


def aio_atomic(self):
    return self.atomic_async()


peewee_async.AioModel.aio_save = aio_save
peewee_async.AioModel.aio_delete_instance = aio_delete_instance
peewee_async.PooledPostgresqlDatabase.aio_atomic = aio_atomic
