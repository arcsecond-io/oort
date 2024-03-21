import socket
from typing import Optional

from arcsecond import ArcsecondAPI
from arcsecond.api.error import ArcsecondRequestTimeoutError
from peewee import DoesNotExist

from oort import __version__
from .config import get_oort_logger
from .errors import *
from .helpers import build_endpoint_kwargs
from .identity import Identity


class UploadPreparator(object):
    """Sync remote Telescope, Night Log, Observation or Calibration and Dataset."""

    def __init__(self, pack, debug=False):
        self._pack = pack
        self._identity: Identity = self._pack.identity
        self._logger = get_oort_logger('uploader', debug=debug)

        self._organisation = None
        self._telescope = None
        self._night_log = None
        self._obs_or_calib = None
        self._dataset = None

        # Do NOT mix debug and self._identity.debug

    # ------ PROPERTIES ------------------------------------------------------------------------------------------------

    @property
    def _api_kwargs(self) -> dict:
        return build_endpoint_kwargs(self._identity.api, self._identity.subdomain)

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
            raise UploadPreparationError(str(error))

        api_name = str(api).upper()
        # Dealing with paginated results
        if isinstance(response_list, dict) and 'results' in response_list.keys():
            response_list = response_list['results']

        if len(response_list) == 0:
            self._logger.info(f'{self.log_prefix} No existing remote resource in {api_name}. Will create one.')
            new_resource = None  # The resource doesn't exist.
        elif len(response_list) == 1:
            self._logger.info(f'{self.log_prefix} One existing remote resource in {api_name}. Using it.')
            new_resource = response_list[0]  # The resource exists.
        else:  # Multiple resources found ??? Filter is not good, or something fishy is happening.
            print(f'\n\n{response_list}\n\n')
            msg = f'Multiple resources found for API {api_name}? Choosing first.'
            raise UploadPreparationError(msg)

        return new_resource

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs) -> Optional[dict]:
        api_name = str(api).upper()
        self._logger.info(f'{self.log_prefix} Creating remote resource in {api_name}...')

        try:
            remote_resource, error = api.create(kwargs)
        except ArcsecondRequestTimeoutError:
            # Retrying request in the case of first one timing out.
            remote_resource, error = api.create(kwargs)

        if error is not None:
            msg = f'Failed to create resource in {api_name} endpoint: {str(error)}'
            raise UploadPreparationError(msg)
        else:
            msg = f"{self.log_prefix} Remote resource {remote_resource['uuid']} in {api_name} created."
            self._logger.info(msg)
            return remote_resource

    def _update_remote_resource(self, api: ArcsecondAPI, uuid, **kwargs) -> None:
        api_name = str(api).upper()
        self._logger.info(f'{self.log_prefix} Updating remote resource {uuid} in {api_name}...')
        try:
            _, error = api.update(uuid, kwargs)
        except ArcsecondRequestTimeoutError:
            # Retrying request in the case of first one timing out.
            _, error = api.create(kwargs)

        if error is not None:
            msg = f'{self.log_prefix} Failed to update remote resource {uuid} in {api_name}. '
            msg += 'Ignoring, and moving on.'
            self._logger.warning(msg)
        else:
            self._logger.info(f'{self.log_prefix} Remote resource {uuid} in {api_name} updated.')

    # ------ SYNC ------------------------------------------------------------------------------------------------------

    def _sync_dataset(self):
        self._logger.info(f'{self.log_prefix} Opening sync DATASET sequence...')

        # Definition of meaningful tags
        tag_root = f'oort|root|{self._pack.root_folder_name}'
        tag_origin = f'oort|origin|{socket.gethostname()}'
        tag_uploader = f'oort|uploader|{ArcsecondAPI.username(api=self._pack.identity.api)}'
        tag_oort = f'oort|version|{__version__}'

        # Unique combination for a given organisation, it should returns one dataset...
        if self._identity.has_dataset and self._identity.is_dataset_uuid:
            pass
        elif self._identity.has_dataset and not self._identity.is_dataset_uuid:
            search_tags = [tag_root]
            create_tags = [tag_root, tag_origin, tag_uploader, tag_oort]
        else:
            tag_folder = f'oort|folder|{self._pack.clean_folder_name}'
            search_tags = [tag_folder, tag_root]
            create_tags = [tag_folder, tag_root, tag_origin, tag_uploader, tag_oort]

        if self._identity.telescope_uuid:
            tag_telescope = f'oort|telescope|{self._identity.telescope_uuid}'
            search_tags.append(tag_telescope)
            create_tags.append(tag_telescope)

        if len(self._identity.dataset_name) > 0:
            search_kwargs = {'name': self._identity.dataset_name, 'tags': ','.join(search_tags)}
            create_kwargs = {'name': self._identity.dataset_name, 'tags': create_tags}
        else:
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
        # we have only the uuid for now, and not the local Database ID.
        if 'observation' in dataset_dict.keys():
            dataset_dict.pop('observation')
        if 'calibration' in dataset_dict.keys():
            dataset_dict.pop('calibration')

        # Update Upload model data.
        self._pack.upload.smart_update(dataset=self._dataset)
        self._logger.info(f'{self.log_prefix} Closing sync DATASET sequence.')

    def _sync_telescope(self):
        try:
            self._telescope = Telescope.get(uuid=self._identity.telescope_uuid)
        except DoesNotExist:
            self._logger.info(f'{self.log_prefix} Reading telescope {self._identity.telescope_uuid}...')
            telescopes_api = ArcsecondAPI.telescopes(**self._api_kwargs)
            telescope_dict, error = telescopes_api.read(self._identity.telescope_uuid)
            if error is not None:
                raise UploadPreparationAPIError(str(error))
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
            if self._identity.telescope_uuid:
                self._sync_telescope()

        except (UploadPreparationFatalError, UploadPreparationError) as e:
            self._logger.error(f'{self.log_prefix} Preparation failed for {self._pack.final_file_name}: {str(e)}')
            preparation_succeeded = False

        else:
            self._logger.info(f'{self.log_prefix} Preparation succeeded for {self._pack.final_file_name}')
            preparation_succeeded = True

        return preparation_succeeded