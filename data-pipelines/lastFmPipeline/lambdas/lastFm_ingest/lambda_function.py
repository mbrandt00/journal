import json
import datetime as dt
import calendar
from datetime import timedelta
from layer.api import network
from layer.track import Track

lastfm_user = network.get_user("mballa000")


def lambda_handler(event, context):
    if event["time_to"] == "today":
        time_to = dt.datetime.today()
    else:
        time_to = dt.datetime.strptime(event["time_to"], "%m-%d-%Y")

    if event["time_from"] == "yesterday":
        time_from = dt.datetime.today() - timedelta(days=1)
    else:
        time_from = dt.datetime.strptime(event["time_from"], "%m-%d-%Y")
    utc_end = calendar.timegm(time_to.utctimetuple())
    utc_start = calendar.timegm(time_from.utctimetuple())
    tracks = lastfm_user.get_recent_tracks(
        time_from=utc_start, time_to=utc_end, limit=None
    )

    new = []
    for track in tracks:
        new.append(
            Track(
                track=track.track, album=track.album, timestamp=track.timestamp
            ).serialize_track()
        )
    tracks = json.dumps(new)
    return tracks
