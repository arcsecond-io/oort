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
        night_logs = self.context.get_group_payload(telescope_key, 'night_logs')

        resources_datasets_key = f'{resources_key}_datasets'
        resources_datasets = self.context.get_group_payload(telescope_key, resources_datasets_key)
        resources = self.context.get_group_payload(telescope_key, resources_key)
        resource_key = resources_key[:-1] if resources_key[-1] == 's' else resources_key

        api_resources = getattr(Arcsecond, 'build_' + resources_key + '_api')(**self.api_kwargs)

        for filepath, filedate in self.files:
            date_string = filedate.date().isoformat()

            night_log = find_first_in_list(night_logs, date=date_string)
            if not night_log:
                night_log = self._find_or_create_remote_resource(self.api_nightlogs,
                                                                 date=date_string,
                                                                 telescope=telescope_uuid)

            if night_log:
                self.context.payload_group_append(telescope_key, night_logs=night_log)
                resource_kwargs.update(night_log=night_log['uuid'])

                resource = find_first_in_list(resources, **resource_kwargs)
                if not resource:
                    resource = self._find_or_create_remote_resource(api_resources, **resource_kwargs)

                if resource:
                    self.context.payload_group_append(telescope_key, resources_key=resource)

                    resource_dataset = find_first_in_list(resources_datasets, **{resource_key: resource['uuid']})
                    if not resource_dataset:
                        dataset_kwargs = {resource_key: resource['uuid'],
                                          'name': resource.get('name') or resource_kwargs.get('name')}
                        if self.context.organisation and not self.astronomer:
                            dataset_kwargs.update(organisation=self.context.organisation)

                        resource_dataset = self._find_or_create_remote_resource(self.api_datasets, **dataset_kwargs)
                        if resource_dataset:
                            self.context.payload_group_append(telescope_key, resources_datasets_key=resource_dataset)
                            self._process_file_upload(filepath, resource_dataset)

                # Todo: Remove this debug line
                # print(date_string, night_log, self.astronomer, resource, resource_dataset)

            self._update_context()

    def _update_context(self):
        current_uploads = [fw.to_dict() for fw in self.context._uploads.values() if fw.is_finished() is False]
        finished_uploads = [fw.to_dict() for fw in self.context._uploads.values() if fw.is_finished() is True]
        self.context.payload_update(current_uploads=current_uploads)
        self.context.payload_update(finished_uploads=finished_uploads)

    def _process_file_upload(self, filepath, dataset):
        upload_key = f"dataset_{dataset['uuid']}:{filepath}"
        fw = self.context._uploads.get(upload_key)
        if fw is None:
            fw = FileWrapper(filepath, dataset['uuid'], dataset['name'], self.context, self.astronomer)
            self.context._uploads[upload_key] = fw

        started_count = len([u for u in self.context._uploads.values() if u.is_started()])
        if self.context._autostart and started_count < MAX_SIMULTANEOUS_UPLOADS:
            fw.start()

        if fw.will_finish():
            fw.finish()

    def _create_remote_resource(self, api: ArcsecondAPI, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            self.context.payload_group_update('messages', warning=msg)
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
            self.context.payload_group_update('messages', warning=str(error))
        elif len(response_list) == 0:
            new_resource = self._create_remote_resource(api, **kwargs)
        elif len(response_list) == 1:
            new_resource = response_list[0]
        else:
            msg = f'Multiple resources found for API {api}? Choosing first.'
            if self.context.debug: print(msg)
            self.context.payload_group_update('messages', warning=msg)

        return new_resource

    def _check_existing_remote_resource(self, api: ArcsecondAPI, uuid):
        response_detail, error = api.read(uuid)
        if error:
            if self.context.debug: print(str(error))
            self.context.payload_group_update('messages', warning=str(error))
        elif response_detail:
            self.context.payload_group_update('messages', warning='')
        else:
            msg = f"Unknown resource in {api} endpoint with UUID {uuid}"
            if self.context.debug: print(msg)
            self.context.payload_group_update('messages', warning=msg)
        return response_detail
