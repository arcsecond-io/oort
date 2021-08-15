import atexit
import math
import pathlib
import time
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
    UUIDField
)
from playhouse.migrate import SqliteMigrator, migrate
from playhouse.sqliteq import SqliteQueueDatabase

from oort.shared.config import get_oort_db_file_path
from oort.shared.constants import ZIP_EXTENSIONS
from oort.uploader.engine.errors import MultipleDBInstanceError

# Create global instance 'db'
db = SqliteQueueDatabase(str(get_oort_db_file_path()),
                         use_gevent=False,
                         autostart=True,
                         queue_max_size=64,
                         results_timeout=5.0,
                         pragmas={'journal_mode': 'wal', 'cache_size': -1024 * 64})


# Make sure write thread is stopped upon exit.
@atexit.register
def _stop_worker_threads():
    db.stop()


class BaseModel(Model):
    class Meta:
        database = db

    _primary_field = 'uuid'

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
        # The following allows get queries with a ForeignKey inside kwargs.
        # One needs it for when creating Dataset related to Observation...
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

        # with db.atomic('IMMEDIATE'):
        try:
            instance = cls.get(**kwargs)
        except DoesNotExist:
            instance = cls.create(**kwargs)
        time.sleep(0.1)

        for foreign_key_name, foreign_value in foreign_items.items():
            foreign_model = cls.get_field(foreign_key_name).rel_model
            foreign_instance = foreign_model.get(foreign_model.get_primary_field() == foreign_value)
            setattr(instance, foreign_key_name, foreign_instance)
            instance.save()
            time.sleep(0.1)

        return instance

    def smart_update(self, **kwargs):
        # with db.atomic():
        id_field = getattr(self.__class__, self._primary_field)
        id_field_value = getattr(self, self._primary_field)
        # See https://docs.peewee-orm.com/en/latest/peewee/querying.html#atomic-updates
        query = self.__class__.update(**kwargs).where(id_field == id_field_value)
        query.execute()
        return self.__class__.get_by_id(id_field_value)


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
    SKIPPED_HIDDEN_FILE = 'skipped (hidden file)'
    SKIPPED_EMPTY_FILE = 'skipped (empty file)'
    # ---


FINISHED_SUBSTATUSES = [Substatus.DONE.value,
                        Substatus.ERROR.value,
                        Substatus.SKIPPED_NO_DATE_OBS.value,
                        Substatus.ALREADY_SYNCED.value]

PREPARATION_DONE_SUBSTATUSES = [Substatus.CHECKING.value,
                                Substatus.READY.value,
                                Substatus.RESTART.value,
                                Substatus.STARTING.value,
                                Substatus.UPLOADING.value] + FINISHED_SUBSTATUSES


class Upload(BaseModel):
    _primary_field = 'id'

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

    target_name = CharField(default='')
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

    def get_formatted_size(self) -> str:
        size = self.file_size or self.file_size_zipped or 0
        if size == 0:
            return '0 Bytes'
        k = 1024
        units = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        i = math.floor(math.log10(1.0 * size) / math.log10(k))
        return f"{(size / math.pow(k, i)):.2f} {units[i]}"


db.connect(reuse_if_open=True)
db.create_tables([Organisation, Telescope, NightLog, Observation, Calibration, Dataset, Upload])

_migrator = SqliteMigrator(db)
migrate(
    _migrator.add_column(Upload._meta.table_name, 'target_name', CharField(default='')),
)
