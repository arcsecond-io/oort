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

    def upload_filters(self, group_key, payload_key, **kwargs):
        resources = self.context.get_group_payload(group_key, payload_key)
        resources_datasets = self.context.get_group_payload(group_key, payload_key + '_datasets')

        for filter_folder in self.filter_folders:
            filter_resource = find(resources, name=filter_folder.name, **kwargs)
            if filter_resource:
                filter_resource_dataset = find(resources_datasets, calibration=filter_resource['uuid'])
                if filter_resource_dataset:
                    if self.context.debug: print(f'Uploading {filter_folder.name}...')
                    filter_folder.upload_files(filter_resource_dataset)
