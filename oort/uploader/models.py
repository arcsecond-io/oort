from peewee import *

from .utils import *

db = SqliteDatabase(get_db_file_path())


class BaseModel(Model):
    class Meta:
        database = db


class RootFolder(BaseModel):
    path = CharField(unique=True)
    username = CharField()
    subdomain = CharField()


class Organisation(BaseModel):
    subdomain = CharField(unique=True)
    name = CharField()


class Telescope(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField()
    organisation = ForeignKeyField(Organisation, backref='telescopes', null=True)


class NightLog(BaseModel):
    uuid = UUIDField(unique=True)
    date = DateField()
    organisation = ForeignKeyField(Organisation, backref='nightlogs', null=True)


class Uploader(BaseModel):
    username = CharField()
    role = CharField()
    organisation = ForeignKeyField(Organisation, backref='astronomers', null=True)
