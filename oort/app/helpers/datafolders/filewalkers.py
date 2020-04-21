import os
import pyfits
import dateparser

from datetime import datetime, timedelta

from arcsecond import Arcsecond
from arcsecond.api.main import ArcsecondAPI

from .filewrapper import FileWrapper
from .utils import find

MAX_SIMULTANEOUS_UPLOADS = 3


class FilesWalker:
    # A folder files

    def __init__(self, context, astronomer, folderpath, prefix='', auto_walk=True):
        self.context = context
        self.astronomer = astronomer
        self.folderpath = folderpath
        self.prefix = prefix
        self.auto_walk = auto_walk
        self.files = []
        self.reset()
        if self.auto_walk is True:
            self.walk()

    @property
    def name(self):
        return f'{self.prefix} {os.path.basename(self.folderpath)}'.strip()

    @property
    def datetime_start(self):
        year, month, day = self.context.current_date.split('-')
        return datetime(year=int(year), month=int(month), day=int(day), hour=12, minute=0, second=0)

    @property
    def datetime_end(self):
        year, month, day = self.context.current_date.split('-')
        return datetime(year=int(year), month=int(month), day=int(day), hour=11, minute=59, second=59) + timedelta(
            days=1)

    @property
    def api_datasets(self):
        # This will work for organisation only, overriding user inside organisation,
        # and no organisation without api_key either.
        if self.astronomer:
            return Arcsecond.build_datasets_api(debug=self.context.debug,
                                                api_key=self.astronomer[1])
        else:
            return Arcsecond.build_datasets_api(debug=self.context.debug,
                                                organisation=self.context.organisation)

    @property
    def api_calibrations(self):
        # This will work for organisation only, overriding user inside organisation,
        # and no organisation without api_key either.
        if self.astronomer:
            return Arcsecond.build_calibrations_api(debug=self.context.debug,
                                                    api_key=self.astronomer[1])
        else:
            return Arcsecond.build_calibrations_api(debug=self.context.debug,
                                                    organisation=self.context.organisation)

    @property
    def api_observations(self):
        # This will work for organisation only, overriding user inside organisation,
        # and no organisation without api_key either.
        if self.astronomer:
            return Arcsecond.build_observations_api(debug=self.context.debug,
                                                    api_key=self.astronomer[1])
        else:
            return Arcsecond.build_observations_api(debug=self.context.debug,
                                                    organisation=self.context.organisation)

    @property
    def api_nightlogs(self):
        # This will work for organisation only, overriding user inside organisation,
        # and no organisation without api_key either.
        if self.astronomer:
            return Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                 api_key=self.astronomer[1])
        else:
            return Arcsecond.build_nightlogs_api(debug=self.context.debug,
                                                 organisation=self.context.organisation)

    def reset(self):
        pass

    def walk(self):
        """Default implementation: look for files only."""
        for name, path in self._walk_folder():
            if not os.path.exists(path) or os.path.isdir(path):
                continue

            try:
                hdulist = pyfits.open(path)
            except Exception as error:
                if self.context.debug: print(str(error))
            else:
                file_date = None
                for hdu in hdulist:
                    date_header = hdu.header['DATE'] or hdu.header['DATE-OBS']
                    file_date = dateparser.parse(date_header)
                    if file_date:
                        break
                if file_date:
                    self.files.append((path, file_date))
                hdulist.close()

            # pattern = r'.*(20[0-9]{4}_[0-9]{6}_[0-9]{3}).*'
            # m = re.search(pattern, name)
            # if m:
            #     sub = '20' + m.group(1)
            #     year, month, day = sub[:4], sub[4:6], sub[6:8]
            #     hour, minute, second = sub[9:11], sub[11:13], sub[13:15]
            #     file_date = datetime(year=int(year),
            #                          month=int(month),
            #                          day=int(day),
            #                          hour=int(hour),
            #                          minute=int(minute),
            #                          second=int(second))
            # TIMEZONE ???
            #     if file_date >= self.datetime_start and file_date < self.datetime_end:
            #         self.files.append(path)

    def _walk_folder(self):
        if not os.path.exists(self.folderpath) or not os.path.isdir(self.folderpath):
            return zip([], [])
        names = os.listdir(self.folderpath)
        return [(name, os.path.join(self.folderpath, name)) for name in names if name[0] != '.']

    def _create_remote_resource(self, api, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create resource in {api} endpoint. Retry is automatic.'
            self.context.payload_group_update('messages', warning=msg)
        else:
            return response_resource

    def _find_or_create_remote_resource(self, api, **kwargs):
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

    def _check_existing_remote_resource(self, api, uuid):
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

    def fetch_resource(self, api: ArcsecondAPI, uuid):
        assert api is not None
        assert uuid is not None and len(uuid) > 0
        return self._check_existing_remote_resource(api, uuid)

    def sync_resource(self, api: ArcsecondAPI, **kwargs):
        assert api is not None
        assert len(kwargs.keys()) > 0
        return self._find_or_create_remote_resource(api, **kwargs)

    def sync_resource_pair(self, resource_key: str, api: ArcsecondAPI, **kwargs):
        assert resource_key is not None and len(resource_key) > 0
        assert api is not None
        assert len(kwargs.keys()) > 0

        resource_dataset = None
        resource = self._find_or_create_remote_resource(api, **kwargs)

        if resource:
            # Using same name as in kwargs for observations, as it will have the filter name inside it
            # and not only the target name, since the Observation has no 'name' field.
            dataset_kwargs = {resource_key: resource['uuid'],
                              'name': resource.get('name') or kwargs.get('name')}

            if self.context.organisation and not self.astronomer:
                dataset_kwargs.update(organisation=self.context.organisation)

            resource_dataset = self._find_or_create_remote_resource(self.api_datasets, **dataset_kwargs)

        return resource, resource_dataset

    def upload_files(self, telescope_key, resources_key, **kwargs):
        night_logs = self.context.get_group_payload(telescope_key, 'night_logs')
        resources = self.context.get_group_payload(telescope_key, resources_key)

        resources_datasets_key = f'{resources_key}_datasets'
        resources_datasets = self.context.get_group_payload(telescope_key, resources_datasets_key)

        for filepath, filedate in self.files:
            date_string = filedate.date().isoformat()
            telescope_uuid = telescope_key.split('_')[1]

            night_log = find(night_logs, date=date_string)
            if not night_log:
                night_log = self.sync_resource(self.api_nightlogs,
                                               date=date_string,
                                               telescope=telescope_uuid)

            if night_log:
                self.context.payload_group_append(telescope_key, night_logs=night_log)

                kwargs.update(night_log=night_log['uuid'])
                resource_key = resources_key[:-1] if resources_key[-1] == 's' else resources_key

                resource_dataset = None
                resource = find(resources, **kwargs)
                if resource:
                    resource_dataset = find(resources_datasets, **{resource_key: resource['uuid']})

                if not resource or not resource_dataset:
                    api = getattr(self, 'api_' + resource_key)
                    resource, resource_dataset = self.sync_resource_pair(resource_key, api, **kwargs)
                    self.context.payload_group_append(telescope_key, resources_key=resource)
                    self.context.payload_group_append(telescope_key, resources_datasets_key=resource_dataset)

                if resource_dataset:
                    self._process_file_upload(filepath, resource_dataset)

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
