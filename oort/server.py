from .app import app
from .app.models import db
from .app.views import *

def run():
    db.bind(**app.config['PONY'])
    db.generate_mapping(create_tables=True)
    app.run()
