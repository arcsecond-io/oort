import os
from datetime import datetime, timedelta

from arcsecond import Arcsecond
from arcsecond.api.main import ArcsecondAPI


class FilesWalker:
    # A folder files

    def __init__(self, context, folderpath):
        self.context = context
        self.folderpath = folderpath
        self.files = []
        self.api = Arcsecond.build_datafiles_api()
        self.reset()

    @property
    def name(self):
        return os.path.basename(self.folderpath)

    @property
    def datetime_start(self):
        year, month, day = self.context.current_date.split('-')
        return datetime(year=year, month=month, day=day, hour=12, minute=0, second=0)

    @property
    def datetime_end(self):
        year, month, day = self.context.current_date.split('-')
        return datetime(year=year, month=month, day=day, hour=11, minute=59, second=59) + timedelta(days=1)

    def reset(self):
        pass

    def walk(self):
        """Default implementation: look for files only."""
        for name, path in self._walk_folder():
            if not os.path.exists(path) or os.path.isdir(path):
                continue
            # Todo: deal with timezones and filename formats!
            if self.context.current_date in name:
                self.files.append(path)

    def _walk_folder(self):
        if not os.path.exists(self.folderpath) or not os.path.isdir(self.folderpath):
            return zip([], [])
        names = os.listdir(self.folderpath)
        return [(name, os.path.join(self.folderpath, name)) for name in names if name[0] != '.']

    def _create_remote_resource(self, resource_name, api, **kwargs):
        response_resource, error = api.create(kwargs)
        if error:
            if self.context.debug: print(str(error))
            msg = f'Failed to create {resource_name} for date {self.context.current_date}. Retry is automatic.'
            self.context.payload_group_update('messages', warning=msg)
        else:
            return response_resource

    def _find_or_create_remote_resource(self, resource_name, api, **kwargs):
        new_resource = None
        response_list, error = api.list(**kwargs)

        # Dealing with paginated results
        if isinstance(response_list, dict) and 'count' in response_list.keys() and 'results' in response_list.keys():
            response_list = response_list['results']

        if error:
            if self.context.debug: print(str(error))
            self.context.payload_group_update('messages', warning=str(error))
        elif len(response_list) == 0:
            new_resource = self._create_remote_resource(resource_name, api, **kwargs)
        elif len(response_list) == 1:
            new_resource = response_list[0]
        else:
            msg = f'Multiple {resource_name} found for date {self.context.current_date}? Choosing first.'
            if self.context.debug: print(msg)
            self.context.payload_group_update('messages', warning=msg)

        return new_resource

    def _check_existing_remote_resource(self, resource_name, api, uuid):
        response_detail, error = api.read(uuid)
        if error:
            if self.context.debug: print(str(error))
            self.context.payload_group_update('messages', warning=str(error))
        elif response_detail:
            self.context.payload_group_update('messages', warning='')
        else:
            msg = f"Unknown {resource_name} with UUID {uuid}"
            if self.context.debug: print(msg)
            self.context.payload_group_update('messages', warning=msg)
        return response_detail

    def fetch_resource(self, name: str, api: ArcsecondAPI, uuid):
        assert name is not None and len(name) > 0
        assert api is not None
        assert uuid is not None and len(uuid) > 0
        return self._check_existing_remote_resource(name, api, uuid)

    def sync_resource(self, name: str, api: ArcsecondAPI, **kwargs):
        assert name is not None and len(name) > 0
        assert api is not None
        assert len(kwargs.keys()) > 0
        return self._find_or_create_remote_resource(name, api, **kwargs)
