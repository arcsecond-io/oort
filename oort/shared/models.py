import pathlib
from datetime import datetime
from enum import Enum

from peewee import (
    CharField,
    DateTimeField,
    DoesNotExist,
    Field,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    UUIDField
)
from playhouse.signals import Signal

from oort.shared.config import get_db_file_path
from oort.shared.config import get_logger
from oort.shared.constants import ZIP_EXTENSIONS
from oort.uploader.engine.errors import MultipleDBInstanceError

db = SqliteDatabase(get_db_file_path(), pragmas={'journal_mode': 'wal', 'cache_size': -1024 * 64})

upload_post_save_signal = Signal()

logger = get_logger()


class BaseModel(Model):
    class Meta:
        database = db

    _primary_field = 'uuid'

    @classmethod
    def exists(cls, **kwargs):
        try:
            cls.get(**kwargs)
        except DoesNotExist:
            return False
        else:
            return True

    @classmethod
    def get_field(cls, name):
        return cls._meta.sorted_fields[cls._meta.sorted_field_names.index(name)]

    @classmethod
    def get_primary_field(cls):
        return cls.get_field(cls._primary_field or 'uuid')

    @classmethod
    def join_get(cls, foreign_field: Field, foreign_value, **kwargs):
        qs = cls.select()
        for field_name, value in kwargs.items():
            qs = qs.where(cls.get_field(field_name) == value)
        qs = qs.join(foreign_field.model).where(foreign_field == foreign_value)
        if qs.count() == 0:
            raise DoesNotExist()
        elif qs.count() == 1:
            return qs.get()
        else:
            msg = f'Multiple instances found for query params: {kwargs}'
            raise MultipleDBInstanceError(msg)

    @classmethod
    def smart_get(cls, **kwargs):
        foreign_key_names = [key for key in kwargs if isinstance(cls.get_field(key), ForeignKeyField)]
        if len(foreign_key_names) > 0:
            value = kwargs.pop(foreign_key_names[0])
            foreign_model = cls.get_field(foreign_key_names[0]).rel_model
            return cls.join_get(foreign_model.get_primary_field(), value, **kwargs)
        return cls.get(**kwargs)

    @classmethod
    def smart_create(cls, **kwargs):
        foreign_items = {key: value for key, value in kwargs.items() if
                         isinstance(cls.get_field(key), ForeignKeyField)}

        for foreign_key_name in foreign_items.keys():
            kwargs.pop(foreign_key_name)

        with db.atomic('IMMEDIATE'):
            instance = cls.create(**kwargs)

        for foreign_key_name, foreign_value in foreign_items.items():
            foreign_model = cls.get_field(foreign_key_name).rel_model
            foreign_instance = foreign_model.get(foreign_model.get_primary_field() == foreign_value)
            with db.atomic('IMMEDIATE'):
                setattr(instance, foreign_key_name, foreign_instance)
                instance.save()

        return instance

    def smart_update(self, **kwargs):
        with db.atomic():
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.save()
        upload_post_save_signal.send(self)


class Organisation(BaseModel):
    _primary_field = 'subdomain'
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
    target_name = CharField(default='')
    night_log = ForeignKeyField(NightLog, backref='observations', null=True)


class Calibration(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    night_log = ForeignKeyField(NightLog, backref='calibrations', null=True)


class Dataset(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    observation = ForeignKeyField(Observation, unique=True, null=True)
    calibration = ForeignKeyField(Calibration, unique=True, null=True)


class Status(Enum):
    NEW = 'New'
    PREPARING = 'Preparing'
    UPLOADING = 'Uploading'
    OK = 'OK'
    ERROR = 'Error'


class Substatus(Enum):
    PENDING = 'pending'
    ZIPPING = 'zipping...'
    CHECKING = 'checking remote file...'
    READY = 'ready'
    RESTART = 'restart'

    STARTING = 'starting...'
    SYNC_TELESCOPE = 'syncing telescope...'
    SYNC_NIGHTLOG = 'syncing night log...'
    SYNC_OBS_OR_CALIB = 'syncing obs or calib...'
    SYNC_DATASET = 'syncing dataset...'
    UPLOADING = 'uploading...'

    DONE = 'done'
    ERROR = 'error'
    ALREADY_SYNCED = 'already synced'
    IGNORED = 'ignored'
    # --- SKIPPED: MUST STARTED WITH THE SAME 'skipped' LOWERCASE WORD. See Context.py ---
    SKIPPED_NO_DATE_OBS = 'skipped (no date obs found)'
    SKIPPED_NOT_FITS_OR_XISF = 'skipped (not fits or xisf)'
    SKIPPED_NO_DATASET = 'skipped (no dataset)'
    SKIPPED_HIDDEN_FILE = 'skipped (hidden file)'
    SKIPPED_EMPTY_FILE = 'skipped (empty file)'
    # ---


FINISHED_SUBSTATUSES = [Substatus.DONE.value,
                        Substatus.ERROR.value,
                        Substatus.SKIPPED_NO_DATE_OBS.value,
                        Substatus.SKIPPED_NOT_FITS_OR_XISF.value,
                        Substatus.SKIPPED_NO_DATASET.value,
                        Substatus.ALREADY_SYNCED.value]

PREPARATION_DONE_SUBSTATUSES = [Substatus.CHECKING.value,
                                Substatus.READY.value,
                                Substatus.RESTART.value,
                                Substatus.STARTING.value,
                                Substatus.UPLOADING.value] + FINISHED_SUBSTATUSES


class Upload(BaseModel):
    created = DateTimeField(default=datetime.now)

    file_path = CharField(unique=True, null=True)
    file_date = DateTimeField(null=True)
    file_size = IntegerField(default=0)

    file_path_zipped = CharField(null=True)
    file_size_zipped = IntegerField(default=0)

    status = CharField(default=Status.NEW.value)
    substatus = CharField(default=Substatus.PENDING.value)
    progress = FloatField(default=0)

    started = DateTimeField(null=True)
    ended = DateTimeField(null=True)
    duration = FloatField(default=0)
    error = CharField(default='')

    dataset = ForeignKeyField(Dataset, null=True, backref='uploads')
    telescope = ForeignKeyField(Telescope, null=True, backref='uploads')

    astronomer = CharField(default='')
    organisation = ForeignKeyField(Organisation, backref='uploads', null=True)

    @classmethod
    def is_finished(cls, file_path):
        try:
            if pathlib.Path(file_path).suffix in ZIP_EXTENSIONS:
                u = cls.get(file_path_zipped=file_path)
            else:
                u = cls.get(file_path=file_path)
        except DoesNotExist:
            return False
        else:
            return u.status == Status.OK.value and u.substatus in FINISHED_SUBSTATUSES


db.connect()
db.create_tables([Organisation, Telescope, NightLog, Observation, Calibration, Dataset, Upload])
