import datetime
import math
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


def get_formatted_time(seconds):
    if seconds > 86400:
        return f"{seconds / 86400:.1f}d"
    elif seconds > 3600:
        return f"{seconds / 3600:.1f}h"
    elif seconds > 60:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds:.1f}s"


def get_formatted_size_times(size):
    total = f"{get_formatted_time(size / pow(10, 4))} on 10 kB/s, "
    total += f"{get_formatted_time(size / pow(10, 5))} on 100 kB/s, "
    total += f"{get_formatted_time(size / pow(10, 6))} on 1 MB/s, "
    total += f"{get_formatted_time(size / pow(10, 7))} on 10 MB/s"
    return total


def get_formatted_bytes_size(size):
    if size == 0:
        return '0 Bytes'
    k = 1024
    units = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    i = math.floor(math.log10(1.0 * size) / math.log10(k))
    return f"{(size / math.pow(k, i)):.2f} {units[i]}"


def is_hidden(path):
    return any([part for part in path.parts if len(part) > 0 and part[0] == '.'])
