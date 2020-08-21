import os
from typing import Optional, Type

from arcsecond import ArcsecondAPI
from peewee import DoesNotExist

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import BaseModel, Dataset, NightLog, Organisation, Telescope
from .errors import UploadPreparationAPIError, UploadPreparationError, UploadPreparationFatalError
from .packer import UploadPack


class UploadPreparator(object):
    """Sync remote Telescope, Night Log, Observation or Calibration and Dataset."""

    def __init__(self, pack: UploadPack, identity: Identity, debug=False):
        self._pack = pack
        self._identity = identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)

        self._preparation_succeeded = False
        self._preparation_can_be_restarted = False

        self._telescope = None
        self._night_log = None
        self._obs_or_calib = None
        self._dataset = None

        # Do NOT mix debug and self._identity.debug

        if self._identity.organisation:
            api = ArcsecondAPI.organisations(debug=self._identity.debug)
            self._sync_local_resource(Organisation, api, subdomain=self._identity.organisation)

    # ------ PROPERTIES ------------------------------------------------------------------------------------------------

    @property
    def pack(self) -> UploadPack:
        return self._pack

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def preparation_succeeded(self) -> bool:
        return False

    @property
    def api_kwargs(self) -> dict:
        kwargs = {'debug': self._identity.debug}
        if self._identity.organisation is not None and len(self._identity.organisation) > 0:
            kwargs.update(organisation=self._identity.organisation)
        else:
            kwargs.update(api_key=self._identity.api_key)
        return kwargs

    @property
    def telescope(self) -> Optional[dict]:
        return self._telescope

    @property
    def night_log(self) -> Optional[BaseModel]:
        return self._night_log

    @property
    def obs_or_calib(self) -> Optional[BaseModel]:
        return self._obs_or_calib

    @property
    def dataset(self) -> Optional[BaseModel]:
        return self._dataset

    @property
    def prefix(self) -> str:
        return '[' + '/'.join(self._pack.file_path.split(os.sep)[-2:]) + ']'

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_local_resource(self, db_class: Type[BaseModel], api: ArcsecondAPI, **kwargs) -> BaseModel:
        remote_resource, error = api.read(kwargs)
        if error:
            raise UploadPreparationAPIError(str(error))

        try:
            resource = db_class.smart_get(**kwargs)
        except DoesNotExist:
            resource = self._create_local_resource(db_class, **kwargs)

        return resource

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_resource(self, db_class: Type[BaseModel], api: ArcsecondAPI, **kwargs) -> BaseModel:
        try:
            resource = db_class.smart_get(**kwargs)

        except DoesNotExist:
            self._logger.info(f'{self.prefix} Local resource does not exists. Find or create remote one.')

            remote_resource = self._find_or_create_remote_resource(api, **kwargs)
            if remote_resource is None:
                raise UploadPreparationError('cant create resource')

            self._logger.info(f'{self.prefix} Remote resource ok.')
            resource = self._create_local_resource(db_class, **remote_resource)

        else:
            self._logger.info(f'{self.prefix} Local resource exists already.')

        return resource

    # ------------------------------------------------------------------------------------------------------------------

    def _find_or_create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        response_list, error = api.list(**kwargs)

        # An error occurred. Deal with it.
        if error is not None:
            raise UploadPreparationError(str(error))

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        # The resource doesn't exist. Create it.
        if len(response_list) == 0:
            new_resource = self._create_remote_resource(api, **kwargs)

        # The resource exists. Do nothing.
        elif len(response_list) == 1:
            new_resource = response_list[0]
            # new_resource = self._check_resource_name(api, response_list[0], kwargs_name)

        # Multiple resources found ??? Filter is not good, or something fishy is happening.
        else:
            msg = f'Multiple resources found for API {api}? Choosing first.'
            raise UploadPreparationError(msg)

        return new_resource

    # ------------------------------------------------------------------------------------------------------------------

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        self._logger.info(f'{self.prefix} Creating remote resource.')

        remote_resource, error = api.create(kwargs)

        if error is not None:
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            raise UploadPreparationError(msg)
        else:
            return remote_resource

    # ------------------------------------------------------------------------------------------------------------------

    def _create_local_resource(self, db_class: Type[BaseModel], **kwargs):
        self._logger.info('Creating local resource.')

        fields = {k: v for k, v in kwargs.items() if k in db_class._meta.sorted_field_names and v is not None}

        if self._identity.organisation and 'organisation' in db_class._meta.get_field_names():
            fields.update(organisation=self._identity.organisation)

        return db_class.smart_create(**fields)

    # ------ CHECKS ----------------------------------------------------------------------------------------------------

    def _sync_telescope(self):
        if not self._identity.telescope:
            return

        self._logger.info(f'{self.prefix} Reading telescope {self._identity.telescope}...')
        api = ArcsecondAPI.telescopes(**self.api_kwargs)
        self._telescope = self._sync_local_resource(Telescope, api, uuid=self._identity.telescope)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_night_log(self):
        self._logger.info(f'{self.prefix} Syncing nightlog {self._pack.night_log_date_string}...')

        kwargs = {'date': self._pack.night_log_date_string}
        if self._identity.telescope:
            kwargs.update(telescope=self._identity.telescope)

        api = ArcsecondAPI.nightlogs(**self.api_kwargs)
        self._night_log = self._sync_resource(NightLog, api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_observation_or_calibration(self):
        self._logger.info(f'{self.prefix} Syncing {self._pack.remote_resources_name}...')
        resources_api = getattr(ArcsecondAPI, self._pack.remote_resources_name)(**self.api_kwargs)
        kwargs = {'night_log': str(self._night_log.uuid), 'name': self._pack.dataset_name}
        self._obs_or_calib = self._sync_resource(self._pack.resource_db_class, resources_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_dataset(self):
        self._logger.info(f'{self.prefix} Syncing Dataset {self._pack.dataset_name}...')
        datasets_api = ArcsecondAPI.datasets(**self.api_kwargs)
        kwargs = {'name': self._pack.dataset_name, self._pack.resource_type: str(self._obs_or_calib.uuid)}
        self._dataset = self._sync_resource(Dataset, datasets_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    async def prepare(self):
        self._logger.info(f'Preparation started for {self._pack.file_path}')
        try:
            self._pack.save(status='Preparing', substatus='Syncing Telescope...')
            self._sync_telescope()
            self._pack.save(status='Preparing', substatus='Syncing Night Log...')
            self._sync_night_log()
            self._pack.save(status='Preparing', substatus='Syncing Observation/Calibration...')
            self._sync_observation_or_calibration()  # observation or calibration
            self._pack.save(status='Preparing', substatus='Syncing Dataset...')
            self._sync_dataset()
            self._pack.save(dataset=self.dataset)
        except UploadPreparationFatalError as e:
            self._logger.info(f'Preparation failed for {self._pack.file_path} with error: {str(e)}')
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = False
        except UploadPreparationError as e:
            self._logger.info(f'Preparation failed for {self._pack.file_path} with error: {str(e)}')
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = True
        else:
            self._logger.info(f'Preparation succeeded for {self._pack.file_path}')
            self._pack.save(status='Ready', substatus='')
            self._preparation_succeeded = True
