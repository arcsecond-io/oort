import os

from .filewalkers import FilesWalker


class FiltersFolder(FilesWalker):
    # A folder of Filters folders (no files)
    def reset(self):
        self.filter_folders = []

    def walk(self):
        for name, path in self._walk_folder():
            if not os.path.isdir(path):
                continue
            self.filter_folders.append(FilesWalker(self.context, path, self.prefix))
        for filter in self.filter_folders:
            filter.walk()

    def sync_filters(self, resource_key, api, **kwargs):
        resources_list = []
        datasets_list = []

        for filter_folder in self.filter_folders:
            kwargs.update(name=filter_folder.name)
            resource, resource_dataset = filter_folder.sync_resource_pair(filter_folder.name,
                                                                          resource_key,
                                                                          api,
                                                                          **kwargs)
            if resource:
                resources_list.append(resource)
            if resource_dataset:
                datasets_list.append(resource_dataset)

        return resources_list, datasets_list
