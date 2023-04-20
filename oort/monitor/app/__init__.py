from flask import Flask
from .views import main


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='{$',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='$}',
    ))


app = CustomFlask(__name__)
app.register_blueprint(main, url_prefix='/')
