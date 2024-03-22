import math


def is_hidden(path):
    return any([part for part in path.parts if len(part) > 0 and part[0] == '.'])
