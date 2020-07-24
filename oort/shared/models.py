from peewee import *

from oort.shared.config import get_db_file_path

db = SqliteDatabase(get_db_file_path())


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def exists(cls, uuid):
        raise NotImplementedError()


class Organisation(BaseModel):
    subdomain = CharField(unique=True)

    @classmethod
    def exists(cls, subdomain):
        try:
            Organisation.get(Organisation.subdomain == subdomain)
        except DoesNotExist:
            return False
        else:
            return True


# class Role(BaseModel):
#     username = CharField(unique=True)
#     organisation = ForeignKeyField(Organisation, backref='roles')
#     role = CharField()


class Telescope(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    organisation = ForeignKeyField(Organisation, backref='telescopes')

    @classmethod
    def exists(cls, uuid):
        try:
            Telescope.get(Telescope.uuid == uuid)
        except DoesNotExist:
            return False
        else:
            return True


class NightLog(BaseModel):
    uuid = UUIDField(unique=True)
    date = CharField(default='')
    telescope_uuid = UUIDField(unique=True)

    @classmethod
    def exists(cls, date_string):
        try:
            NightLog.get(NightLog.date == date_string)
        except DoesNotExist:
            return False
        else:
            return True

# class Dataset(BaseModel):
#     uuid = UUIDField(unique=True)
#     name = CharField(default='')
#
#
# class Upload(BaseModel):
#     filepath = CharField(unique=True)
#     filedate = DateTimeField()
#
#     filesize = IntegerField(default=0)
#     status = CharField(default='ready')
#     substatus = CharField('pending')
#     progress = FloatField(default=0)
#
#     started = DateTimeField(null=True)
#     ended = DateTimeField(null=True)
#     duration = FloatField(default=0)
#     error = CharField(default='')
#
#     dataset = ForeignKeyField(Dataset, null=True, backref='uploads')
#     night_log = ForeignKeyField(NightLog, null=True, backref='uploads')
#     telescope = ForeignKeyField(Telescope, null=True, backref='uploads')
