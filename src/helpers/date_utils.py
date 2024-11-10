import datetime


def timestamp_as_datatime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp=timestamp,tz=datetime.UTC)