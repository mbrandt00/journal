import json
import datetime as dt
import calendar
import os
from datetime import timedelta
from layer.api import network
from layer.track import Track
from layer.utils import dicts_to_jsonl
from layer.s3 import upload_object

lastfm_user = network.get_user("mballa000")

today = dt.datetime.today()

date_path = f"year={today.year}/month={today.strftime('%m')}/day={today.strftime('%d')}"


def lambda_handler(event, context):
    if event["time_to"] == "today":
        time_to = today
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

    all_tracks = []
    for track in tracks:
        all_tracks.append(
            Track(
                track=track.track, album=track.album, timestamp=track.timestamp
            ).serialize_track()
        )
    if all_tracks:
        filename = f"lastFm_raw_{today.strftime('%H:%M')}.json"
        s3_loc = os.path.join("lastFm", date_path, filename)
        json_str = dicts_to_jsonl(all_tracks)
        upload_object(os.environ["RAW_BUCKET"], s3_loc, json_str, is_string=True)
