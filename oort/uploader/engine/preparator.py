import os
import socket
from typing import Optional

from arcsecond import ArcsecondAPI
from arcsecond.api.error import ArcsecondRequestTimeoutError
from peewee import DoesNotExist

from oort import __version__
from oort.shared.config import get_oort_logger
from oort.shared.models import (Dataset, Organisation, Status, Substatus, Telescope)
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

        self._pack.upload.smart_update(astronomer=self._identity.username)
        if self._identity.subdomain:
            try:
                self._organisation = Organisation.get(subdomain=self._identity.subdomain)
            except DoesNotExist:
                self._organisation = Organisation.create(subdomain=self._identity.subdomain)
            self._pack.upload.smart_update(organisation=self._organisation)

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
        try:
            response_list, error = api.list(**kwargs)
        except ArcsecondRequestTimeoutError:
            # Retrying request in the case of first one timing out.
            response_list, error = api.list(**kwargs)

        # An error occurred. Deal with it.
        if error is not None:
            raise errors.UploadPreparationError(str(error))

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        if len(response_list) == 0:
            self._logger.info(f'{self.log_prefix} No existing remote resource in {str(api).upper()}. Will create one.')
            new_resource = None  # The resource doesn't exist.
        elif len(response_list) == 1:
            self._logger.info(f'{self.log_prefix} One existing remote resource in {str(api).upper()}. Using it.')
            new_resource = response_list[0]  # The resource exists.
        else:  # Multiple resources found ??? Filter is not good, or something fishy is happening.
            print(f'\n\n{response_list}\n\n')
            msg = f'Multiple resources found for API {str(api).upper()}? Choosing first.'
            raise errors.UploadPreparationError(msg)

        return new_resource

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        self._logger.info(f'{self.log_prefix} Creating remote resource...')

        try:
            remote_resource, error = api.create(kwargs)
        except ArcsecondRequestTimeoutError:
            # Retrying request in the case of first one timing out.
            remote_resource, error = api.create(kwargs)

        if error is not None:
            msg = f'Failed to create resource in {api} endpoint: {str(error)}'
            raise errors.UploadPreparationError(msg)
        else:
            self._logger.info(f'{self.log_prefix} Remote resource created.')
            return remote_resource

    def _update_remote_resource(self, api: ArcsecondAPI, uuid, **kwargs) -> None:
        self._logger.info(f'{self.log_prefix} Updating remote resource...')
        try:
            _, error = api.update(uuid, kwargs)
        except ArcsecondRequestTimeoutError:
            # Retrying request in the case of first one timing out.
            _, error = api.create(kwargs)

        if error is not None:
            self._logger.warn(f'{self.log_prefix} Failed to update remote resource. Ignoring, and moving on.')
        else:
            self._logger.info(f'{self.log_prefix} Remote resource updated.')

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_dataset(self):
        self._logger.info(f'{self.log_prefix} Opening sync DATASET sequence...')
        self._pack.upload.smart_update(substatus=Substatus.SYNC_DATASET.value)

        # Definition of meaningful tags
        tag_telescope = f'oort|telescope|{self._identity.telescope}'
        tag_folder = f'oort|folder|{self._pack.clean_folder_name}'
        tag_root = f'oort|root|{self._pack.root_folder_name}'
        tag_origin = f'oort|origin|{socket.gethostname()}'
        tag_uploader = f'oort|uploader|{ArcsecondAPI.username()}'
        tag_oort = f'oort|version|{__version__}'

        search_tags = [tag_folder, tag_root]
        create_tags = [tag_folder, tag_root, tag_origin, tag_uploader, tag_oort]
        if self._identity.telescope:
            search_tags.append(tag_telescope)
            create_tags.append(tag_telescope)

        # Kwargs used only for search, then kwargs for create.
        search_kwargs = {'tags': ','.join(search_tags)}
        create_kwargs = {'name': self._pack.dataset_name, 'tags': create_tags}

        # Search for remote resource. If none found, create one.
        datasets_api = ArcsecondAPI.datasets(**self._api_kwargs)
        dataset_dict = self._find_remote_resource(datasets_api, **search_kwargs)
        if dataset_dict is None:
            dataset_dict = self._create_remote_resource(datasets_api, **create_kwargs)
        else:
            self._update_remote_resource(datasets_api, dataset_dict['uuid'], **create_kwargs)

        # Create local resource. But avoids pointing to (possibly) non-existing ForeignKeys for which
        # we have only the uuid for now, not the local Database ID.
        if 'observation' in dataset_dict.keys():
            dataset_dict.pop('observation')
        if 'calibration' in dataset_dict.keys():
            dataset_dict.pop('calibration')
        try:
            self._dataset = Dataset.get(uuid=dataset_dict['uuid'])
        except DoesNotExist:
            self._dataset = Dataset.create(**dataset_dict)
        else:
            self._dataset.smart_update(**dataset_dict)
        # Update Upload model data.
        self._pack.upload.smart_update(dataset=self._dataset)
        self._logger.info(f'{self.log_prefix} Closing sync DATASET sequence.')

    def _sync_telescope(self):
        try:
            self._telescope = Telescope.get(uuid=self._identity.telescope)
        except DoesNotExist:
            self._logger.info(f'{self.log_prefix} Reading telescope {self._identity.telescope}...')
            self._pack.upload.smart_update(substatus=Substatus.SYNC_TELESCOPE.value)
            telescopes_api = ArcsecondAPI.telescopes(**self._api_kwargs)
            telescope_dict, error = telescopes_api.read(self._identity.telescope)
            if error is not None:
                raise errors.UploadPreparationAPIError(str(error))
            self._telescope = Telescope.create(**telescope_dict)
        else:
            self._pack.upload.smart_update(telescope=self._telescope)

    def prepare(self):
        self._logger.info(f'{self.log_prefix} Preparation started for {self._pack.final_file_name}')
        self._pack.upload.smart_update(status=Status.PREPARING.value)

        try:
            # Start by syncing Dataset. This is key: it MUST work by itself, without any dependency
            # on NightLog, Observation, Calibration, Telescope...
            self._sync_dataset()

            # It has no impact on the upload to actually get the telescope details.
            # It is only used to display the telescope name in the web page.
            if self._identity.telescope:
                self._sync_telescope()

        except (errors.UploadPreparationFatalError, errors.UploadPreparationError) as e:
            self._logger.error(f'{self.log_prefix} Preparation failed for {self._pack.final_file_name}: {str(e)}')
            self._pack.upload.smart_update(status=Status.ERROR.value, substatus=Substatus.ERROR.value, error=str(e))
            preparation_succeeded = False

        else:
            self._logger.info(f'{self.log_prefix} Preparation succeeded for {self._pack.final_file_name}')
            self._pack.upload.smart_update(status=Status.UPLOADING.value, substatus=Substatus.READY.value)
            preparation_succeeded = True

        return preparation_succeeded
