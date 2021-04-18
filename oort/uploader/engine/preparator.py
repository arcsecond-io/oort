import os
from typing import Optional, Type, Union

from arcsecond import ArcsecondAPI
from peewee import DoesNotExist

from oort.shared.config import get_logger
from oort.shared.models import (Calibration, Dataset, Model, NightLog, Observation, Organisation, Status, Substatus,
                                Telescope)
from . import errors


class UploadPreparator(object):
    """Sync remote Telescope, Night Log, Observation or Calibration and Dataset."""

    def __init__(self, pack, debug=False):
        self._pack = pack
        self._identity = self._pack.identity
        self._debug = debug
        self._logger = get_logger(debug=self._debug)

        self._preparation_succeeded = False
        self._preparation_can_be_restarted = False

        self._organisation = None
        self._telescope = None
        self._night_log = None
        self._obs_or_calib = None
        self._dataset = None

        # Do NOT mix debug and self._identity.debug

        self._pack.upload.smart_update(astronomer=self._identity.username)
        if self._identity.subdomain:
            test = os.environ.get('OORT_TESTS') == '1'
            api = ArcsecondAPI.organisations(debug=self._identity.debug, test=test)
            self._organisation = self._sync_local_resource(Organisation, api, self._identity.subdomain)
            self._pack.upload.smart_update(organisation=self._organisation)

    # ------ PROPERTIES ------------------------------------------------------------------------------------------------

    @property
    def preparation_succeeded(self) -> bool:
        return False

    @property
    def api_kwargs(self) -> dict:
        test = os.environ.get('OORT_TESTS') == '1'
        kwargs = {'debug': self._identity.debug, 'test': test}
        if self._identity.api_key:
            # We have an api key -> we are uploading on behalf of an astronomer, we use PERSONAL APIs.
            # It will bypass the currently logged-in astronomer credentials.
            kwargs.update(api_key=self._identity.api_key)
        elif self._identity.subdomain is not None and len(self._identity.subdomain) > 0:
            # We don't have an api key, but we have an organisation subdomain ->
            # we are uploading for an organisation, we use ORGANISATION APIs,
            # using currently logged-in astronomer credentials.
            kwargs.update(organisation=self._identity.subdomain)
        return kwargs

    @property
    def telescope(self) -> Optional[Telescope]:
        return self._telescope

    @property
    def night_log(self) -> Optional[NightLog]:
        return self._night_log

    @property
    def obs_or_calib(self) -> Optional[Union[Observation, Calibration]]:
        return self._obs_or_calib

    @property
    def dataset(self) -> Optional[Dataset]:
        return self._dataset

    @property
    def prefix(self) -> str:
        return '[UploadPreparator: ' + '/'.join(self._pack.final_file_path.split(os.sep)[-2:]) + ']'

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_local_resource(self, db_class: Type[Model], api: ArcsecondAPI, id_value) -> Model:
        remote_resource, error = api.read(id_value)
        if error:
            raise errors.UploadPreparationAPIError(str(error))

        try:
            local_resource = db_class.smart_get(**{db_class._primary_field: id_value})
        except DoesNotExist:
            kwargs = {db_class._primary_field: id_value}
            if 'name' in remote_resource.keys():
                kwargs.update(name=remote_resource.get('name'))
            local_resource = self._create_local_resource(db_class, **kwargs)
        else:
            if 'name' in remote_resource.keys() and 'name' in db_class._meta.sorted_field_names:
                local_resource.smart_update(name=remote_resource.get('name'))

        return local_resource

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_resource(self, db_class: Type[Model], api: ArcsecondAPI, **kwargs) -> Model:
        try:
            resource = db_class.smart_get(**kwargs)

        except DoesNotExist:
            self._logger.info(f'{self.prefix} Local resource does not exist. Find or create remote one.')

            remote_resource = self._find_or_create_remote_resource(api, **kwargs)
            if remote_resource is None:
                raise errors.UploadPreparationError('cant create resource')

            common_keys = kwargs.keys() & remote_resource.keys()
            common_values = [(k, kwargs.get(k), remote_resource.get(k)) for k in common_keys]
            if any([(k, v1, v2) for k, v1, v2 in common_values if v1 != v2]):
                msg = f'Mismatch between remote and local for {db_class} resource: {common_values}'
                raise errors.UploadPreparationError(msg)

            resource = self._create_local_resource(db_class, **remote_resource)

        else:
            self._logger.info(f'{self.prefix} Local resource exists already.')

        return resource

    # ------------------------------------------------------------------------------------------------------------------

    def _find_or_create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        response_list, error = api.list(**kwargs)

        # An error occurred. Deal with it.
        if error is not None:
            raise errors.UploadPreparationError(str(error))

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        # The resource doesn't exist. Create it.
        if len(response_list) == 0:
            new_resource = self._create_remote_resource(api, **kwargs)

        # The resource exists. Do nothing.
        elif len(response_list) == 1:
            new_resource = response_list[0]
            self._logger.info(f'{self.prefix} Remote resource exists, using it.')

        # Multiple resources found ??? Filter is not good, or something fishy is happening.
        else:
            msg = f'Multiple resources found for API {api}? Choosing first.'
            raise errors.UploadPreparationError(msg)

        return new_resource

    # ------------------------------------------------------------------------------------------------------------------

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        self._logger.info(f'{self.prefix} Creating remote resource...')

        remote_resource, error = api.create(kwargs)

        if error is not None:
            msg = f'Failed to create resource in {api} endpoint: {str(error)}'
            raise errors.UploadPreparationError(msg)
        else:
            self._logger.info(f'{self.prefix} Remote resource created.')
            return remote_resource

    # ------------------------------------------------------------------------------------------------------------------

    def _create_local_resource(self, db_class: Type[Model], **kwargs):
        self._logger.info(f'{self.prefix} Creating local resource...')

        fields = {k: v for k, v in kwargs.items() if k in db_class._meta.sorted_field_names and v is not None}

        if self._identity.subdomain and 'organisation' in db_class._meta.sorted_field_names:
            fields.update(organisation=self._identity.subdomain)

        instance = db_class.smart_create(**fields)
        self._logger.info(f'{self.prefix} Local resource created.')

        return instance

    # ------ CHECKS ----------------------------------------------------------------------------------------------------

    def _sync_telescope(self):
        if not self._identity.telescope:
            return

        self._logger.info(f'{self.prefix} Reading telescope {self._identity.telescope}...')
        api = ArcsecondAPI.telescopes(**self.api_kwargs)
        self._telescope = self._sync_local_resource(Telescope, api, self._identity.telescope)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_night_log(self):
        nightlogs_api = ArcsecondAPI.nightlogs(**self.api_kwargs)
        kwargs = {'date': self._pack.night_log_date_string}
        if self._identity.telescope:
            kwargs.update(telescope=self._identity.telescope)
        self._logger.info(f'{self.prefix} Syncing NIGHT_LOG {self._pack.night_log_date_string}...')
        self._night_log = self._sync_resource(NightLog, nightlogs_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_observation_or_calibration(self):
        # self._pack.remote_resources_name is either 'observations' or 'calibrations'
        resources_api = getattr(ArcsecondAPI, self._pack.remote_resources_name)(**self.api_kwargs)
        kwargs = {'name': self._pack.dataset_name}
        if self._night_log:
            kwargs.update(night_log=str(self._night_log.uuid))
        if self._pack.resource_type == 'observation':
            kwargs.update(target_name=self._pack.dataset_name)
        self._logger.info(f'{self.prefix} Syncing {self._pack.remote_resources_name[:-1].upper()}: {kwargs}...')
        self._obs_or_calib = self._sync_resource(self._pack.resource_db_class, resources_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    def _sync_dataset(self):
        datasets_api = ArcsecondAPI.datasets(**self.api_kwargs)
        kwargs = {'name': self._pack.dataset_name}
        if self._obs_or_calib:
            kwargs.update(**{self._pack.resource_type: str(self._obs_or_calib.uuid)})
        self._logger.info(f'{self.prefix} Syncing DATASET {self._pack.dataset_name}...')
        self._dataset = self._sync_resource(Dataset, datasets_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    def prepare(self):
        self._logger.info(f'{self.prefix} Preparation started for {self._pack.final_file_path}')
        try:
            self._pack.upload.smart_update(status=Status.PREPARING.value, substatus=Substatus.SYNC_TELESCOPE.value)
            self._sync_telescope()

            if self._telescope:
                self._pack.upload.smart_update(telescope=self._telescope)

            if self._pack.night_log_date_string:
                self._pack.upload.smart_update(substatus=Substatus.SYNC_NIGHTLOG.value)
                self._sync_night_log()

                # No night log, no observation not calib possible.
                self._pack.upload.smart_update(substatus=Substatus.SYNC_OBS_OR_CALIB.value)
                self._sync_observation_or_calibration()  # observation or calibration

            self._pack.upload.smart_update(substatus=Substatus.SYNC_DATASET.value)
            self._sync_dataset()

            if self._dataset:
                self._pack.upload.smart_update(dataset=self.dataset)

        except errors.UploadPreparationFatalError as e:
            self._logger.info(f'{self.prefix} Preparation failed for {self._pack.final_file_path} with error: {str(e)}')
            self._pack.upload.smart_update(status=Status.ERROR.value, substatus=Substatus.ERROR.value, error=str(e))
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = False

        except errors.UploadPreparationError as e:
            self._logger.info(f'{self.prefix} Preparation failed for {self._pack.final_file_path} with error: {str(e)}')
            self._pack.upload.smart_update(status=Status.ERROR.value, substatus=Substatus.ERROR.value, error=str(e))
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = True

        else:
            self._logger.info(f'{self.prefix} Preparation succeeded for {self._pack.final_file_path}')
            self._pack.upload.smart_update(status=Status.UPLOADING.value, substatus=Substatus.READY.value)
            self._preparation_succeeded = True
