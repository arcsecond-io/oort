import copy
import os
from datetime import datetime, timedelta

from arcsecond import Arcsecond
from arcsecond.api.main import ArcsecondAPI

from .constants import OORT_FILENAME
from .filesfolder import FilesFolder
from .fileuploader import FileUploader
from .utils import find_first_in_list, find_fits_filedate, find_xisf_filedate

MAX_SIMULTANEOUS_UPLOADS = 3


class FilesFolderSyncer(FilesFolder):
    def __init__(self, context, astronomer, folderpath, prefix=''):
        super().__init__(context, astronomer, folderpath, prefix=prefix)
        self.api_nightlogs = Arcsecond.build_nightlogs_api(**self.api_kwargs)
        self.api_datasets = Arcsecond.build_datasets_api(**self.api_kwargs)
        self.night_logs = []
        self.resources = []
        self.resources_datasets = []

    def reset(self):
        self.files = []

    def walk(self):
        """Default implementation: look for files only."""
        for filename, filepath in self._walk_folder():
            if not os.path.exists(filepath) or os.path.isdir(filepath):
                continue
            if os.path.isfile(filepath) and filename != OORT_FILENAME:
                filedate = find_fits_filedate(filepath, self.context.debug)
                if filedate is None:
                    filedate = find_xisf_filedate(filepath, self.context.debug)
                if filedate:
                    self.files.append((filepath, filedate))

    def upload_files(self, telescope_key, resources_key, **raw_resource_kwargs):
        if len(self.files) == 0:
            return

        print(f'Syncing {len(self.files)} files')
        telescope_uuid = telescope_key.split('_')[1]
        telescope = find_first_in_list(self.context.telescopes, uuid=telescope_uuid)

        # Getting singular of 'calibrations' or 'observations'
        resource_key = resources_key[:-1] if resources_key[-1] == 's' else resources_key
        api_resources = getattr(Arcsecond, 'build_' + resources_key + '_api')(**self.api_kwargs)

        for filepath, filedate in self.files:
            # --- night log ---
            # Night Logs starts on local noon and lasts 24 hours!
            x = 0 if filedate.hour >= 12 else 1
            date_string = (filedate - timedelta(days=x)).date().isoformat()

            # Organisation automatically attached to night log...
            night_log = self._sync_resource(self.api_nightlogs,
                                            self.night_logs,
                                            date=date_string,
                                            telescope=telescope_uuid)

            if not night_log:
                if self.context.debug:
                    print('>>> No night log', filedate, filepath, date_string, telescope_uuid)
                continue

            # --- resource (calibration or observation) ---
            resource_kwargs = copy.deepcopy(raw_resource_kwargs)
            resource_kwargs.update(night_log=night_log['uuid'])
            resource = self._sync_resource(api_resources, self.resources, **resource_kwargs)
            if not resource:
                if self.context.debug:
                    print('*** No ' + resource_key, filedate, filepath, resource_kwargs)
                continue

            # --- resource dataset ---
            # Organisation automatically attached to dataset...
            ### warning : changing the way we build datasets kwargs values may end up with an error: ###
            ### "Target Calibration is already linked to a dataset." ###
            dataset_name = resource.get('name') or resource_kwargs.get('name')
            if 'type' in resource_kwargs:
                dataset_name = f"{resource_kwargs.get('type')} {dataset_name}"
            dataset_kwargs = {resource_key: resource['uuid'], 'name': dataset_name}
            ### end warning ###

            resource_dataset = self._sync_resource(self.api_datasets, self.resources_datasets, **dataset_kwargs)
            if not resource_dataset:
                if self.context.debug:
                    print(f'*** No {resource_key} dataset', filedate, filepath, dataset_kwargs)
                continue

            # # --- resource upload ---
            self._process_file_upload(filepath, filedate, resource_dataset, night_log, telescope)

    def _sync_resource(self, api, local_list, **kwargs):
        local_resource = find_first_in_list(local_list, **kwargs)
        if not local_resource:
            local_resource = self._find_or_create_remote_resource(api, **kwargs)
            if local_resource:
                local_list.append(local_resource)
        return local_resource

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug or self.context.verbose: print(str(error))
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            self.context.messages['warning'] = msg
        else:
            return response_resource

    def _find_or_create_remote_resource(self, api: ArcsecondAPI, **kwargs):
        new_resource = None

        # Do not use name as filter argument for list API request.
        kwargs_name = kwargs.pop('name', None)
        response_list, error = api.list(**kwargs)

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'count' in response_list.keys() and 'results' in response_list.keys():
            response_list = response_list['results']

        if error:
            if self.context.debug or self.context.verbose: print(str(error))
            self.context.messages['warning'] = str(error)
        elif len(response_list) == 0:
            # Reintroduce name into resource creation.
            if kwargs_name: kwargs.update(name=kwargs_name)
            new_resource = self._create_remote_resource(api, **kwargs)
        elif len(response_list) == 1:
            new_resource = response_list[0]
        else:
            msg = f'Multiple resources found for API {api}? Choosing first.'
            if self.context.debug or self.context.verbose: print(msg)
            self.context.messages['warning'] = msg

        return new_resource

    def _check_existing_remote_resource(self, api: ArcsecondAPI, uuid: str):
        response_detail, error = api.read(uuid)
        if error:
            if self.context.debug or self.context.verbose: print(str(error))
            self.context.messages['warning'] = str(error)
        elif response_detail:
            self.context.messages['warning'] = ''
        else:
            msg = f"Unknown resource in {api} endpoint with UUID {uuid}"
            if self.context.debug or self.context.verbose: print(msg)
            self.context.messages['warning'] = msg
            return response_detail

    def _process_file_upload(self, filepath: str, filedate: datetime, dataset: dict, night_log: dict, telescope: dict):
        upload_key = f"dataset_{dataset['uuid']}:{filepath}"
        fu = self.context.uploads.get(upload_key)
        if fu is None:
            fu = FileUploader(filepath,
                              filedate,
                              dataset,
                              night_log,
                              telescope,
                              self.astronomer,
                              self.context.organisation,
                              self.context.debug,
                              self.context.verbose)

            self.context.uploads[upload_key] = fu

        started_count = len([u for u in self.context.uploads.values() if u.is_started()])
        if self.context._autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            fu.start()
            if self.context.verbose:
                print(f'Uploading {filepath}...')

        if fu.will_finish():
            fu.finish()
            if self.context.verbose:
                print(f'Finished upload of {filepath}...')

        self.context.current_uploads = [fw.to_dict() for fw in self.context.uploads.values() if not fw.is_finished()]
        self.context.finished_uploads = [fw.to_dict() for fw in self.context.uploads.values() if fw.is_finished()]
