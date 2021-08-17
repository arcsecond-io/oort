import os
import socket
from typing import Optional

from arcsecond import ArcsecondAPI

from oort import __version__
from oort.shared.config import get_oort_logger
from oort.shared.models import (Dataset, NightLog, Organisation, Status, Substatus,
                                Telescope)
from . import errors


class UploadPreparator(object):
    """Sync remote Telescope, Night Log, Observation or Calibration and Dataset."""

    def __init__(self, pack, debug=False):
        self._pack = pack
        self._identity = self._pack.identity
        self._debug = debug
        self._logger = get_oort_logger('uploader', debug=self._debug)

        self._organisation = None
        self._telescope = None
        self._night_log = None
        self._obs_or_calib = None
        self._dataset = None

        # Do NOT mix debug and self._identity.debug

        self._pack.update_upload(astronomer=self._identity.username)
        if self._identity.subdomain:
            self._organisation = Organisation.smart_create(subdomain=self._identity.subdomain)
            self._pack.update_upload(organisation=self._organisation)

    # ------ PROPERTIES ------------------------------------------------------------------------------------------------

    @property
    def _api_kwargs(self) -> dict:
        test = os.environ.get('OORT_TESTS') == '1'
        kwargs = {'debug': self._identity.debug, 'test': test, 'upload_key': self._identity.upload_key}
        if self._identity.subdomain is not None and len(self._identity.subdomain) > 0:
            # We have an organisation subdomain.
            # We are uploading for an organisation, using ORGANISATION APIs,
            # If no upload_key or api_key is provided, it will be using the current
            # logged-in astronomer credentials.
            kwargs.update(organisation=self._identity.subdomain)
        return kwargs

    @property
    def log_prefix(self) -> str:
        return f'[UploadPreparator: {self._pack.final_file_path}]'

    # ------ REMOTE ----------------------------------------------------------------------------------------------------

    def _find_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        response_list, error = api.list(**kwargs)

        # An error occurred. Deal with it.
        if error is not None:
            raise errors.UploadPreparationError(str(error))

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        if len(response_list) == 0:
            self._logger.info(f'{self.log_prefix} No existing remote resource. Will create one.')
            new_resource = None  # The resource doesn't exist.
        elif len(response_list) == 1:
            self._logger.info(f'{self.log_prefix} One existing remote resource. Using it.')
            new_resource = response_list[0]  # The resource exists.
        else:  # Multiple resources found ??? Filter is not good, or something fishy is happening.
            msg = f'Multiple resources found for API {api}? Choosing first.'
            raise errors.UploadPreparationError(msg)

        return new_resource

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        self._logger.info(f'{self.log_prefix} Creating remote resource...')

        remote_resource, error = api.create(kwargs)

        if error is not None:
            msg = f'Failed to create resource in {api} endpoint: {str(error)}'
            raise errors.UploadPreparationError(msg)
        else:
            self._logger.info(f'{self.log_prefix} Remote resource created.')
            return remote_resource

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_dataset(self):
        self._logger.info(f'{self.log_prefix} Syncing DATASET...')
        self._pack.update_upload(substatus=Substatus.SYNC_DATASET.value)

        # Definition of meaningful tags
        tag_folder = f'folder|{self._pack.clean_folder_name}'
        tag_root = f'root|{self._pack.root_folder_name}'
        tag_origin = f'origin|{socket.gethostname()}|'
        tag_uploader = f'uploader|{ArcsecondAPI.username()}'
        tag_oort = f'oort|{__version__}'

        # Kwargs used only for search, then kwargs for create.
        search_kwargs = {'tags': tag_folder}
        create_kwargs = {'name': self._pack.dataset_name,
                         'tags': ','.join([tag_folder, tag_root, tag_origin, tag_uploader, tag_oort])}

        # Search for remote resource. If none found, create one.
        datasets_api = ArcsecondAPI.datasets(**self._api_kwargs)
        dataset_dict = self._find_remote_resource(datasets_api, **search_kwargs)
        if dataset_dict is None:
            dataset_dict = self._create_remote_resource(datasets_api, **create_kwargs)

        # Create local resource.
        self._dataset = Dataset.smart_create(**dataset_dict)
        # Update Upload model data.
        self._pack.update_upload(dataset=self._dataset)

    def _sync_telescope(self):
        self._logger.info(f'{self.log_prefix} Reading telescope {self._identity.telescope}...')
        self._pack.update_upload(substatus=Substatus.SYNC_TELESCOPE.value)

        telescopes_api = ArcsecondAPI.telescopes(**self._api_kwargs)
        telescope_dict, error = telescopes_api.read(self._identity.telescope)
        if error:
            raise errors.UploadPreparationAPIError(str(error))

        self._telescope = Telescope.smart_create(**telescope_dict)
        self._pack.update_upload(telescope=self._telescope)

    def _sync_night_log(self):
        self._logger.info(f'{self.log_prefix} Syncing NIGHT_LOG...')
        self._pack.update_upload(substatus=Substatus.SYNC_NIGHTLOG.value)

        # NightLogs are completely determined if they have a date and a telescope.
        # Since a telescope is required for organisation uploads, NightLogs are completely determined
        # for organisations. There will be an ambiguity for personal upload without telescope.
        kwargs = {'date': self._pack.night_log_date_string}
        if self._identity.telescope:
            kwargs.update(telescope=self._identity.telescope)
        else:
            msg = f'{self.log_prefix} No Telescope provided for NightLog {self._pack.night_log_date_string}.'
            self._logger.warn(msg)

        night_log_api = ArcsecondAPI.nightlogs(**self._api_kwargs)
        night_log_dict = self._find_remote_resource(night_log_api, **kwargs)
        if night_log_dict is None:
            night_log_dict = self._create_remote_resource(night_log_api, **kwargs)

        self._night_log = NightLog.smart_create(**night_log_dict)

    def _sync_observation_or_calibration(self):
        # self._pack.remote_resources_name is either 'observations' or 'calibrations'
        self._logger.info(f'{self.log_prefix} Syncing {self._pack.remote_resources_name[:-1].upper()}...')
        self._pack.update_upload(substatus=Substatus.SYNC_OBS_OR_CALIB.value)

        search_kwargs = {'night_log': str(self._night_log.uuid),
                         'dataset': str(self._dataset.uuid)}

        create_kwargs = {'night_log': str(self._night_log.uuid),
                         'dataset': str(self._dataset.uuid),
                         'name': self._pack.clean_folder_name}

        if self._pack.resource_type == 'observation':
            create_kwargs.update(target_name=self._pack.target_name)

        resources_api = getattr(ArcsecondAPI, self._pack.remote_resources_name)(**self._api_kwargs)
        resource_dict = self._find_remote_resource(resources_api, **search_kwargs)
        if resource_dict is None:
            resource_dict = self._create_remote_resource(resources_api, **create_kwargs)

        # It will attach to NightLog automatically
        self._obs_or_calib, = self._pack.resource_db_class.smart_create(**resource_dict)
        # Attach Datasets and Observation/Calibration
        self._dataset.smart_update(**{self._pack.resource_type: self._obs_or_calib})

    def prepare(self):
        self._logger.info(f'{self.log_prefix} Preparation started for {self._pack.final_file_name}')
        self._pack.update_upload(status=Status.PREPARING.value)

        preparation_succeeded = False
        preparation_can_be_restarted = False

        try:
            # Start by syncing Dataset. This is key: it MUST work by itself, without any dependency
            # on NightLog, Observation, Calibration, Telescope...
            self._sync_dataset()

            # It has no impact on the upload to actually get the telescope details.
            # It is only used to display the telescope name in the web page.
            if self._identity.telescope:
                self._sync_telescope()

            if self._pack.night_log_date_string:
                self._sync_night_log()
                # No night log, no observation nor calibration possible.
                self._sync_observation_or_calibration()  # observation or calibration

        except errors.UploadPreparationFatalError as e:
            self._logger.error(f'{self.log_prefix} Preparation failed for {self._pack.final_file_name} with error:')
            self._logger.error(f'{str(e)}')
            self._pack.update_upload(status=Status.ERROR.value, substatus=Substatus.ERROR.value, error=str(e))
            preparation_succeeded = False
            preparation_can_be_restarted = False

        except errors.UploadPreparationError as e:
            self._logger.error(f'{self.log_prefix} Preparation failed for {self._pack.final_file_name} with error:')
            self._logger.error(f'{str(e)}')
            self._pack.update_upload(status=Status.ERROR.value, substatus=Substatus.ERROR.value, error=str(e))
            preparation_succeeded = False
            preparation_can_be_restarted = True

        else:
            self._logger.info(f'{self.log_prefix} Preparation succeeded for {self._pack.final_file_name}')
            self._pack.update_upload(status=Status.UPLOADING.value, substatus=Substatus.READY.value)
            preparation_succeeded = True

        return preparation_succeeded, preparation_can_be_restarted
