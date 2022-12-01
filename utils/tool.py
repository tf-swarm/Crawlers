
from datetime import datetime, timedelta

def formatGMTime(timestamp):
    gmt_format = '%a, %d %b %Y %H:%M:%S GMT'
    gmt_date = datetime.strptime(timestamp, gmt_format) + timedelta(hours=8)
    return gmt_date

def formatUTCtime(timestamp):
    utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    utc_date = datetime.strptime(timestamp, utc_format) + timedelta(hours=8)
    return utc_date