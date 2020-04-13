def find(items, **kwargs):
    return next((item for item in items if all([item[k] == v for k, v in kwargs.items()])), None)
