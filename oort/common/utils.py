def is_file_hidden(path):
    return any([part for part in path.parts if len(part) > 0 and part[0] == '.'])
