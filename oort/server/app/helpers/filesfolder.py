import os


class FilesFolder:
    # A folder files

    def __init__(self, context, astronomer, folderpath, prefix=''):
        self.context = context
        self.astronomer = astronomer
        self.folderpath = folderpath
        self.prefix = prefix
        self.files = []

    @property
    def name(self):
        return f'{self.prefix.strip()} {os.path.basename(self.folderpath)}'.strip()

    @property
    def api_kwargs(self):
        kwargs = {'debug': self.context.debug}
        if isinstance(self.astronomer, tuple) and len(self.astronomer) == 2:
            kwargs.update(api_key=self.astronomer[1])
        elif self.context.organisation is not None and len(self.context.organisation) > 0:
            kwargs.update(organisation=self.context.organisation)
        return kwargs

    def _walk_folder(self):
        if not os.path.exists(self.folderpath) or not os.path.isdir(self.folderpath):
            return zip([], [])
        names = os.listdir(self.folderpath)
        return [(name, os.path.join(self.folderpath, name)) for name in names if name[0] != '.']
