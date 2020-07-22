from peewee import *

from oort.shared.config import get_db_file_path

db = SqliteDatabase(get_db_file_path())


class BaseModel(Model):
    class Meta:
        database = db


class Dataset(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')


class Telescope(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')


class NightLog(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')


class Upload(BaseModel):
    filepath = CharField(unique=True)
    filedate = DateTimeField()

    filesize = IntegerField(default=0)
    status = CharField(default='ready')
    substatus = CharField('pending')
    progress = FloatField(default=0)

    started = DateTimeField(null=True)
    ended = DateTimeField(null=True)
    duration = FloatField(default=0)
    error = CharField(default='')

    dataset = ForeignKeyField(Dataset, null=True, backref='uploads')
    night_log = ForeignKeyField(NightLog, null=True, backref='uploads')
    telescope = ForeignKeyField(Telescope, null=True, backref='uploads')
