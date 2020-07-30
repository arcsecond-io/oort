from peewee import *

from oort.shared.config import get_db_file_path

db = SqliteDatabase(get_db_file_path())


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def exists(cls, **kwargs):
        try:
            cls.get(**kwargs)
        except DoesNotExist:
            return False
        else:
            return True


class Organisation(BaseModel):
    subdomain = CharField(unique=True)


class Telescope(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    organisation = ForeignKeyField(Organisation, backref='telescopes', null=True)


class NightLog(BaseModel):
    uuid = UUIDField(unique=True)
    date = CharField(default='')
    telescope = ForeignKeyField(Telescope, backref='night_logs', null=True)
    organisation = ForeignKeyField(Organisation, backref='night_logs', null=True)


class Observation(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    night_log = ForeignKeyField(Organisation, backref='observations')


class Calibration(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    night_log = ForeignKeyField(Organisation, backref='calibrations')


class Dataset(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    observation = ForeignKeyField(Observation, unique=True, null=True)
    calibration = ForeignKeyField(Calibration, unique=True, null=True)


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

db.connect()
db.create_tables([Organisation, Telescope, NightLog, Observation, Calibration])
