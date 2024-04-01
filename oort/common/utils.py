import os
from typing import Optional

from arcsecond import ArcsecondAPI


def is_file_hidden(path):
    return any([part for part in path.parts if len(part) > 0 and part[0] == '.'])


def build_endpoint_kwargs(api: str = 'main', subdomain: Optional[str] = None):
    test = os.environ.get('OORT_TESTS') == '1'
    upload_key = ArcsecondAPI.upload_key(api=api)
    kwargs = {'test': test, 'api': api, 'upload_key': upload_key}
    if subdomain is not None:
        kwargs.update(organisation=subdomain)
    return kwargs
