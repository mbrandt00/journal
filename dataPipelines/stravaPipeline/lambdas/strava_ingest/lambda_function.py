import os
from stravalib.client import Client
from layer.api import get_current_access_token
from layer.s3 import upload_object
from layer.utils import dicts_to_jsonl, date_decider
import datetime as dt

from layer.activity import create_activity


today = dt.datetime.today()
date_path = f"year={today.year}/month={today.strftime('%m')}/day={today.strftime('%d')}"


def lambda_handler(event, context):
    before, after = date_decider(event["time_from"], event["time_to"])
    client = Client(access_token=get_current_access_token())  # updates token if expired
    activities = client.get_activities(
        before=before,
        after=after,
    )

    all_activities = []

    try:
        for activity in activities:
            all_activities.append(create_activity(activity))
    except Exception as e:
        print(f"exception: {e}")

    if all_activities:
        filename = f"strava_raw_{today.strftime('%H:%M')}.json"
        s3_loc = os.path.join("strava", date_path, filename)
        json_str = dicts_to_jsonl(all_activities)
        upload_object(os.environ["RAW_BUCKET"], s3_loc, json_str, is_string=False)
    else:
        print("no activities found")
