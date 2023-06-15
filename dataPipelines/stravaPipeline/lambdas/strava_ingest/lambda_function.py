
import os
from stravalib.client import Client
from layer.api import access_token
from layer.s3 import upload_object
from layer.utils import dicts_to_jsonl
import datetime as dt
from datetime import timedelta
from layer.activity import Activity

today = dt.datetime.today()

date_path = f"year={today.year}/month={today.strftime('%m')}/day={today.strftime('%d')}"



def lambda_handler(event, context):
    if event["time_to"] == "today":
        before = dt.datetime.today()
    else:
        before = dt.datetime.strptime(event["time_to"], "%m-%d-%Y")

    if event["time_from"] == "yesterday":
        after = dt.datetime.today() - timedelta(days=1)
    else:
        after = dt.datetime.strptime(event["time_from"], "%m-%d-%Y")
    client = Client(access_token=access_token)
    activities = client.get_activities(
        after=after,
        before=before,
    )

    all_activities = []
    for activity in activities:
        serialized_activity = Activity(
            average_heartrate=activity.average_heartrate,
            average_speed=activity.average_speed,
            name=activity.name,
            start_date_local=activity.start_date_local,
            start_latlng=activity.start_latlng,
            end_latlng=activity.end_latlng,
            pr_count=activity.pr_count,
            description=activity.description,
            commute=activity.commute,
            distance=activity.distance,
            elapsed_time=activity.elapsed_time,
        ).serialize_activity()
        all_activities.append(serialized_activity)

    if all_activities:
        filename = f"strava_raw_{today.strftime('%H:%M')}.json"
        s3_loc = os.path.join("strava", date_path, filename)
        print(type(all_activities))
        print(all_activities)
        json_str = dicts_to_jsonl(all_activities)
        upload_object(os.environ["RAW_BUCKET"], s3_loc, json_str, is_string=False)
