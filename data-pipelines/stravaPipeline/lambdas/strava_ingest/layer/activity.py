import pint
from stravalib import unithelper

ureg = pint.UnitRegistry()
# TODO make datetime and time delta better serialized


class Activity:
    def __init__(
        self,
        average_heartrate=None,
        average_speed=None,
        name=None,
        start_date_local=None,
        start_latlng=None,
        end_latlng=None,
        pr_count=None,
        description=None,
        commute=False,
        distance=None,
        elapsed_time=None,
    ):
        self.average_heartrate = average_heartrate
        self.average_speed_meters = average_speed
        self.name = name
        self.start_date_local = start_date_local
        self.start_latlng = start_latlng
        self.end_latlng = end_latlng
        self.pr_count = pr_count
        self.description = description
        self.commute = commute
        self.meter_distance = distance
        self.elapsed_time = elapsed_time

    def average_speed(self):
        return self.average_speed_meters.to(ureg.miles / ureg.hour).magnitude

    def distance(self):
        return float(unithelper.miles(self.meter_distance))

    def end_time(self):
        return self.start_date_local + self.elapsed_time

    def serialize_activity(self):
        dict = {
            "average_heartrate": self.average_heartrate,
            "average_speed_mph": self.average_speed(),
            "name": self.name,
            "start_date_local": str(self.start_date_local),
            "end_date_local": str(self.end_time()),
            "start_latlng": self.start_latlng,
            "end_latlng": self.end_latlng,
            "pr_count": self.pr_count,
            "description": self.description,
            "commute": self.commute,
            "distance_miles": self.distance(),
            "elapsed_time": str(self.elapsed_time),
        }
        return dict


"""
current output
[
    {
        "average_heartrate": 117.2,
        "average_speed_mph": 3.0534180386542586,
        "name": "Afternoon Walk",
        "start_date_local": "2023-06-08 16:37:18",
        "end_date_local": "2023-06-08 17:28:27",
        "start_latlng": LatLon(lat=39.73709042184055, lon=-104.96100607328117),
        "end_latlng": LatLon(lat=39.73730877041817, lon=-104.96125400997698),
        "pr_count": 0,
        "description": None,
        "commute": False,
        "distance_miles": 2.447394714865187,
        "elapsed_time": "0:51:09",
    },
    {
        "average_heartrate": 152.0,
        "average_speed_mph": 1.796259842519685,
        "name": "Evening Tennis",
        "start_date_local": "2023-06-06 19:01:38",
        "end_date_local": "2023-06-06 20:03:16",
        "start_latlng": None,
        "end_latlng": None,
        "pr_count": 0,
        "description": None,
        "commute": False,
        "distance_miles": 0.031938479280998966,
        "elapsed_time": "1:01:38",
    },
    {
        "average_heartrate": 104.2,
        "average_speed_mph": 2.9840730136005726,
        "name": "Afternoon Walk",
        "start_date_local": "2023-06-06 17:41:26",
        "end_date_local": "2023-06-06 18:19:30",
        "start_latlng": LatLon(lat=39.73689705133438, lon=-104.9611168820411),
        "end_latlng": LatLon(lat=39.73728161305189, lon=-104.96137965470552),
        "pr_count": 0,
        "description": None,
        "commute": False,
        "distance_miles": 1.8744283385031415,
        "elapsed_time": "0:38:04",
    },
]

"""
