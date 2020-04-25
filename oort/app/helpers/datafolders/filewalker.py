import os
import dateparser

from datetime import datetime, timedelta
from astropy.io import fits as pyfits

class FilesWalker:
    # A folder files

    def __init__(self, context, astronomer, folderpath, prefix=''):
        self.context = context
        self.astronomer = astronomer
        self.folderpath = folderpath
        self.prefix = prefix
        self.files = []
        self.reset()

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
    def api_kwargs(self):
        kwargs = {'debug': self.context.debug}
        if self.astronomer:
            kwargs.update(api_key=self.astronomer[1])
        elif self.context.organisation:
            kwargs.update(organisation=self.context.organisation)
        return kwargs

    def reset(self):
        pass

    def _get_fits_filedate(self, path):
        file_date = None
        try:
            hdulist = pyfits.open(path)
        except Exception as error:
            if self.context.debug: print(str(error))
        else:
            for hdu in hdulist:
                date_header = hdu.header['DATE'] or hdu.header['DATE-OBS']
                file_date = dateparser.parse(date_header)
                if file_date:
                    break
            hdulist.close()
        return file_date

    def _walk_folder(self):
        if not os.path.exists(self.folderpath) or not os.path.isdir(self.folderpath):
            return zip([], [])
        names = os.listdir(self.folderpath)
        return [(name, os.path.join(self.folderpath, name)) for name in names if name[0] != '.']
