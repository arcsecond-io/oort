def find_first_in_list(items, **kwargs):
    return next((item for item in items if all([item[k] == v for k, v in kwargs.items()])), None)


# class Config:
#     def __init__(self, config):
#         self.context = Context(config)
#
#     @property
#     def _section(self):
#         raw_section = 'debug' if self.context.debug else 'main'
#         return 'organisation:' + self.context.organisation + ':' + raw_section if self.context.organisation else raw_section
#
#     def _get_config(self):
#         _config = ConfigParser()
#         try:
#             _config.read(self.context.config_filepath)
#         except DuplicateOptionError:
#             os.remove(self.context.config_filepath)
#             _config.read(self.context.config_filepath)
#         return _config
#
#     def _save_config(self, config):
#         with open(self.context.config_filepath, 'w') as f:
#             config.write(f)
#
#     def read(self, key):
#         config = self._get_config()
#         if self._section not in config.keys():
#             return None
#         return config[self._section].get(key)
#
#     def save(self, **kwargs):
#         config = self._get_config()
#         if self._section not in config.keys():
#             config.add_section(self._section)
#         for k, v in kwargs.items():
#             config.set(self._section, k, v)
#         self._save_config(config)
#
#     def get_yield_string(self):
#         return self.context.get_yield_string()
