import datetime


def get_current_date(self):
    before_noon = datetime.datetime.now().hour < 12
    if before_noon:
        return (datetime.datetime.now() - datetime.timedelta(days=1)).date().isoformat()
    else:
        return datetime.datetime.now().date().isoformat()

