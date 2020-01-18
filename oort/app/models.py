from pony.orm import Database, Required, Optional, perm
from datetime import datetime

db = Database()


class Upload(db.Entity):
    filepath = Required(str, unique=True)
    filesize = Required(int)
    started = Optional(datetime)
    ended = Optional(datetime)
    status = Required(str)
    progress = Required(float, default=0)


with db.set_perms_for(Upload):
    perm('view edit create delete', group='anybody')
