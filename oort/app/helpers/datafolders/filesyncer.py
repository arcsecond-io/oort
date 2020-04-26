import os

from arcsecond import Arcsecond
from arcsecond.api.main import ArcsecondAPI

from .filewalker import FilesWalker
from .filewrapper import FileWrapper
from .utils import find_first_in_list

MAX_SIMULTANEOUS_UPLOADS = 3


class FilesSyncer(FilesWalker):
    def __init__(self, context, astronomer, folderpath, prefix=''):
        super().__init__(context, astronomer, folderpath, prefix='')
        self.api_nightlogs = Arcsecond.build_nightlogs_api(**self.api_kwargs)
        self.api_datasets = Arcsecond.build_datasets_api(**self.api_kwargs)
        self.walk()

    def walk(self):
        """Default implementation: look for files only."""
        for name, path in self._walk_folder():
            if not os.path.exists(path) or os.path.isdir(path):
                continue
            file_date = self._get_fits_filedate(path)
            if file_date:
                self.files.append((path, file_date))

    def upload_files(self, telescope_key, resources_key, **resource_kwargs):
        telescope_uuid = telescope_key.split('_')[1]
        telescope = find_first_in_list(self.context.payload.get('telescopes'), uuid=telescope_uuid)
        night_logs = self.context.payload.group_get(telescope_key, 'night_logs') or []

        resources = self.context.payload.group_get(telescope_key, resources_key) or []
        resources_datasets_key = f'{resources_key}_datasets'
        resources_datasets = self.context.payload.group_get(telescope_key, resources_datasets_key) or []

        # Getting singular of 'calibrations' or 'observations'
        resource_key = resources_key[:-1] if resources_key[-1] == 's' else resources_key

        # print(f'Uploading {len(self.files)} files {resources_key} ...')
        api_resources = getattr(Arcsecond, 'build_' + resources_key + '_api')(**self.api_kwargs)

        for filepath, filedate in self.files:
            # --- night log ---
            date_string = filedate.date().isoformat()

            night_log = self._sync_resource(self.api_nightlogs, night_logs, date=date_string, telescope=telescope_uuid)
            if not night_log:
                if self.context.debug: print('>>> No night log', filedate, filepath, date_string, telescope_uuid)
                continue

            self.context.payload.group_append(telescope_key, night_logs=night_log)

            # --- resource (calibration or observation) ---
            resource_kwargs.update(night_log=night_log['uuid'])
            resource = self._sync_resource(api_resources, resources, **resource_kwargs)
            if not resource:
                if self.context.debug: print('>>> No ' + resource_key, filedate, filepath, resource_kwargs)
                continue

            self.context.payload.group_append(telescope_key, **{resources_key: resource})

            # --- resource dataset ---
            dataset_kwargs = {resource_key: resource['uuid'],
                              'name': resource.get('name') or resource_kwargs.get('name')}
            if self.context.organisation and not self.astronomer:
                dataset_kwargs.update(organisation=self.context.organisation)

            resource_dataset = self._sync_resource(self.api_datasets, resources_datasets, **dataset_kwargs)
            if not resource_dataset:
                print(f'>>> No {resource_key} dataset', filedate, filepath, dataset_kwargs)
                continue

            self.context.payload.group_append(telescope_key, **{resources_datasets_key: resource_dataset})

            # --- resource upload ---
            self._process_file_upload(filepath, resource_dataset, night_log, telescope)
            self._update_context()

    def _sync_resource(self, api, local_list, **kwargs):
        local_resource = find_first_in_list(local_list, **kwargs)
        if not local_resource:
            local_resource = self._find_or_create_remote_resource(api, **kwargs)
        return local_resource

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            self.context.payload.group_update('messages', warning=msg)
        else:
            return response_resource

    def _find_or_create_remote_resource(self, api: ArcsecondAPI, **kwargs):
        new_resource = None
        response_list, error = api.list(**kwargs)

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'count' in response_list.keys() and 'results' in response_list.keys():
            response_list = response_list['results']

        if error:
            if self.context.debug: print(str(error))
            self.context.payload.group_update('messages', warning=str(error))
        elif len(response_list) == 0:
            new_resource = self._create_remote_resource(api, **kwargs)
        elif len(response_list) == 1:
            new_resource = response_list[0]
        else:
            msg = f'Multiple resources found for API {api}? Choosing first.'
            if self.context.debug: print(msg)
            self.context.payload.group_update('messages', warning=msg)

        return new_resource

    def _check_existing_remote_resource(self, api: ArcsecondAPI, uuid):
        response_detail, error = api.read(uuid)
        if error:
            if self.context.debug: print(str(error))
            self.context.payload.group_update('messages', warning=str(error))
        elif response_detail:
            self.context.payload.group_update('messages', warning='')
        else:
            msg = f"Unknown resource in {api} endpoint with UUID {uuid}"
            if self.context.debug: print(msg)
            self.context.payload.group_update('messages', warning=msg)
        return response_detail

    def _update_context(self):
        current_uploads = [fw.to_dict() for fw in self.context._uploads.values() if fw.is_finished() is False]
        finished_uploads = [fw.to_dict() for fw in self.context._uploads.values() if fw.is_finished() is True]
        self.context.payload.update(current_uploads=current_uploads)
        self.context.payload.update(finished_uploads=finished_uploads)

    def _process_file_upload(self, filepath, dataset, night_log, telescope):
        upload_key = f"dataset_{dataset['uuid']}:{filepath}"
        fw = self.context._uploads.get(upload_key)
        if fw is None:
            fw = FileWrapper(self.context, self.astronomer, filepath, dataset, night_log, telescope)
            self.context._uploads[upload_key] = fw

        started_count = len([u for u in self.context._uploads.values() if u.is_started()])
        if self.context._autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            fw.start()

        if fw.will_finish():
            fw.finish()
