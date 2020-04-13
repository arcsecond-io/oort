import os

from .filewalkers import FilesWalker
from .utils import find


class FiltersFolder(FilesWalker):
    # A folder of Filters folders (no files)
    def reset(self):
        self.filter_folders = []

    def walk(self):
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                continue
            if self.context.debug: print(f' >  >  > Found a [{self.prefix}] {name} folder.')
            self.filter_folders.append(FilesWalker(self.context, path, self.prefix))

    def sync_filters(self, resource_name, resource_key, api, **kwargs):
        resources_list = []
        datasets_list = []

        for filter_folder in self.filter_folders:
            kwargs.update(name=filter_folder.name)
            resource, resource_dataset = filter_folder.sync_resource_pair(resource_name + filter_folder.name,
                                                                          resource_key,
                                                                          api,
                                                                          **kwargs)
            if resource:
                resources_list.append(resource)
            if resource_dataset:
                datasets_list.append(resource_dataset)

        return resources_list, datasets_list

    def upload_filters(self, payload_key, type_key):
        calibrations = self.context.get_group_payload(payload_key, 'calibrations')
        calibrations_datasets = self.context.get_group_payload(payload_key, 'calibrations_datasets')

        for filter_folder in self.filter_folders:
            flat_calib = find(calibrations, type=type_key, name=filter_folder.name)
            if flat_calib:
                flat_dataset = find(calibrations_datasets, calibration=flat_calib['uuid'])
                if flat_dataset:
                    if self.context.debug: print(f'Uploading {filter_folder.name}...')
                    filter_folder.upload_files(flat_dataset)
