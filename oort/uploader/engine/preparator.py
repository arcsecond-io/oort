from typing import Optional, Type

from arcsecond import ArcsecondAPI

from oort.shared.config import get_logger
from oort.shared.identity import Identity
from oort.shared.models import *
from .errors import *
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
    def night_log(self) -> Optional[dict]:
        return self._night_log

    @property
    def obs_or_calib(self) -> Optional[dict]:
        return self._obs_or_calib

    @property
    def dataset(self) -> Optional[dict]:
        return self._dataset

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_local_resource(self, db_class: Type[BaseModel], api: ArcsecondAPI, **kwargs):
        remote_resource, error = api.read(kwargs)
        if error:
            raise UploadPreparationAPIError(str(error))

        try:
            resource = db_class.get(**kwargs)
        except DoesNotExist:
            resource = self._create_local_resource(db_class, **kwargs)

        return resource

    def _sync_remote_resource(self, db_class: Type[BaseModel], api: ArcsecondAPI, **kwargs):
        try:
            resource = db_class.get(**kwargs)

        except DoesNotExist:
            resource = self._find_or_create_remote_resource(api, **kwargs)
            if resource is None:
                raise UploadPreparationError('cant create resource')

            self._create_local_resource(db_class, **resource)

        return resource

    def _find_or_create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        new_resource = None

        # One must use the list endpoint since we don't have the existing UUID.
        # We do not use name as filter argument for list API request, as it may changes, and
        # thus isn't reliable to filter existing remote resources.
        kwargs_name = kwargs.pop('name', None)
        response_list, error = api.list(**kwargs)

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        # An error occurred. Deal with it.
        if error is not None:
            raise UploadPreparationError(str(error))

        # The resource doesn't exist. Create it.
        elif len(response_list) == 0:
            # Reintroduce name into resource creation.
            if kwargs_name: kwargs.update(name=kwargs_name)
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

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        remote_resource, error = api.create(kwargs)
        if error is not None:
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            raise UploadPreparationError(msg)
        else:
            return remote_resource

    def _create_local_resource(self, db_class: Type[BaseModel], **kwargs):
        fields = {k: v for k, v in kwargs.items() if k in db_class._meta.sorted_field_names}

        # Deal with organisation!
        if self._identity.organisation and 'organisation' in db_class._meta.get_field_names():
            org = Organisation.get(subdomain=self._identity.organisation, debug=self._debug)
            fields.update(organisation=org)

        return db_class.create(**fields)

    # Legacy
    # def _check_resource_name(self, db_class: BaseModel, api: ArcsecondAPI, new_resource: dict, kwargs_name: str):
    #     if kwargs_name is None or len(kwargs_name) == 0:
    #         return new_resource
    #     if 'name' in new_resource.keys():
    #         current_name = new_resource.get('name', '').strip()
    #         if len(current_name) == 0:
    #             updated_new_resource, error = api.update(new_resource['uuid'], {'name': kwargs_name})

    # ------ CHECKS ----------------------------------------------------------------------------------------------------

    def _sync_telescope(self):
        if not self._identity.telescope:
            return

        self._logger.info(f'Syncing telescope {self._identity.telescope}...')
        api = ArcsecondAPI.telescopes(**self.api_kwargs)

        try:
            # Telescope is supposed to exist already. Don't create new ones from here.
            self._telescope = self._sync_local_resource(Telescope, api, uuid=self._identity.telescope)
        except UploadPreparationAPIError as e:
            # Raising a FATAL error: we can't continue without an unknown telescope
            raise UploadPreparationFatalError(str(e))

    def _sync_night_log(self):
        self._logger.info(f'Syncing nightlog {self._pack.night_log_date_string}...')
        kwargs = {'date': self._pack.night_log_date_string}
        if self._identity.telescope is not None:
            kwargs.update(telescope=self._identity.telescope)

        api = ArcsecondAPI.nightlogs(**self.api_kwargs)
        self._night_log = self._sync_remote_resource(NightLog, api, **kwargs)

    # observations or calibrations
    def _sync_observation_or_calibration(self):
        self._logger.info(f'Syncing {self._pack.remote_resources_name}...')
        resources_api = getattr(ArcsecondAPI, self._pack.remote_resources_name)(**self.api_kwargs)

        # Using dataset name for Obs/Calib name too.
        self._obs_or_calib = self._sync_remote_resource(self._pack.resource_db_class,
                                                        resources_api,
                                                        night_log=self._night_log.get('uuid'),
                                                        name=self._pack.dataset_name)

    def _sync_dataset(self):
        self._logger.info(f'Syncing {self._pack.dataset_name}...')
        kwargs = {'name': self._pack.dataset_name, self._pack.resource_type: self._obs_or_calib.get('uuid')}
        datasets_api = ArcsecondAPI.datasets(**self.api_kwargs)
        self._dataset = self._sync_remote_resource(Dataset, datasets_api, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------

    async def prepare(self):
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
            self._logger.error(str(e))
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = False
        except UploadPreparationError as e:
            self._logger.error(str(e))
            self._preparation_succeeded = False
            self._preparation_can_be_restarted = True
        else:
            self._preparation_succeeded = True
