import datetime
import os
import random
import string


def find_first_in_list(objects, **kwargs):
    return next((obj for obj in objects if
                 len(set(obj.keys()).intersection(kwargs.keys())) > 0 and
                 all([obj[k] == v for k, v in kwargs.items() if k in obj.keys()])),
                None)


class SafeDict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return None

    def append(self, key, *items):
        if key not in self.keys():
            self[key] = []
        for item in items:
            if item not in self[key]:
                self[key].append(item)


def get_current_date(self):
    before_noon = datetime.datetime.now().hour < 12
    if before_noon:
        return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    else:
        return datetime.datetime.now().date().isoformat()


def get_random_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def tail(f, lines=10, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]


def get_username():
    import pwd

    return pwd.getpwuid(os.getuid())[0]
