from stravalib.client import Client
from layer.api import access_token
import datetime as dt
from datetime import timedelta


def lambda_handler(event, context):
    before = (
        dt.datetime.today()
        if event["time_to"] == "today"
        else dt.datetime.strptime(event["time_to"], "%m-%d-%Y")
    )
    after = (
        (dt.datetime.today() - timedelta(days=1))
        if event["time_from"] == "yesterday"
        else dt.datetime.strptime(event["time_to"], "%m-%d-%Y")
    )
    client = Client(access_token=access_token)
    activities = client.get_activities(
        after=after,
        before=before,
    )
    for activity in activities:
        print(f" average_heartrate {activity.average_heartrate}")
        print(f" average_speed {activity.average_speed}")
        print(f" name {activity.name}")
        print(f" start_date_local {activity.start_date_local}")
        print(f" start_latlng {activity.start_latlng}")
        print(f" end_latlng {activity.end_latlng}")
