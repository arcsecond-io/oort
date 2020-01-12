from flask import Flask
from pony.flask import Pony
from .config import config


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='{$',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='$}',
    ))


app = CustomFlask(__name__)
app.config.update(config)

Pony(app)
