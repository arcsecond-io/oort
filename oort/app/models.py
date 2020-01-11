from pony.orm import Database, Required, Optional
from datetime import datetime

db = Database()


class Upload(db.Entity):
    filepath = Required(str, unique=True)
    started = Optional(datetime)
    ended = Optional(datetime)
    status = Required(str)
