import atexit
import pathlib
from datetime import datetime
from enum import Enum

from peewee import (
    CharField,
    DateTimeField,
    DoesNotExist,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    UUIDField
)
# from playhouse.migrate import SqliteMigrator, migrate
from playhouse.sqliteq import SqliteQueueDatabase

from oort.shared.config import get_oort_db_file_path
from oort.shared.constants import ZIP_EXTENSIONS
from oort.shared.utils import get_formatted_bytes_size

# Create global instance 'db'
db = SqliteQueueDatabase(str(get_oort_db_file_path()),
                         use_gevent=False,
                         autostart=True,
                         queue_max_size=64,
                         results_timeout=5.0,
                         pragmas={'journal_mode': 'wal',
                                  'cache_size': -1024 * 64,
                                  'foreign_keys': 1,
                                  'threadlocals': True})


# Make sure write thread is stopped upon exit.
@atexit.register
def _stop_worker_threads():
    db.stop()


class BaseModel(Model):
    class Meta:
        database = db

    _primary_field = 'uuid'

    def smart_update(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if k in self.__class__._meta.sorted_field_names:
                setattr(self, k, v)
        self.save()


class Organisation(BaseModel):
    _primary_field = 'subdomain'
    subdomain = CharField(unique=True)


class Telescope(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    organisation = ForeignKeyField(Organisation, backref='telescopes', null=True)


# class NightLog(BaseModel):
#     uuid = UUIDField(unique=True)
#     date = CharField(default='')
#     telescope = ForeignKeyField(Telescope, backref='night_logs', null=True)
#     organisation = ForeignKeyField(Organisation, backref='night_logs', null=True)
#
#
# class Observation(BaseModel):
#     uuid = UUIDField(unique=True)
#     name = CharField(default='')
#     target_name = CharField(default='')
#     night_log = ForeignKeyField(NightLog, backref='observations', null=True)
#
#
# class Calibration(BaseModel):
#     uuid = UUIDField(unique=True)
#     name = CharField(default='')
#     night_log = ForeignKeyField(NightLog, backref='calibrations', null=True)
#

class Dataset(BaseModel):
    uuid = UUIDField(unique=True)
    name = CharField(default='')
    # observation = ForeignKeyField(Observation, unique=True, null=True)
    # calibration = ForeignKeyField(Calibration, unique=True, null=True)


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
        return get_formatted_bytes_size(size)

    def archive(self, substatus) -> None:
        self.smart_update(status=Status.OK.value, substatus=substatus, ended=datetime.now())

    def reset_for_restart(self) -> None:
        self.smart_update(status=Status.NEW.value,
                          substatus=Substatus.RESTART.value,
                          progress=0,
                          started=None,
                          ended=None,
                          duration=0,
                          error='',
                          dataset=None,
                          file_date=None,
                          file_size=0,
                          file_size_zipped=0,
                          target_name='')


# db.connect(reuse_if_open=True)
db.create_tables([Organisation, Telescope, Dataset, Upload])

# _migrator = SqliteMigrator(db)
# migrate(
#     _migrator.add_column(Upload._meta.table_name, 'target_name', CharField(default='')),
# )
