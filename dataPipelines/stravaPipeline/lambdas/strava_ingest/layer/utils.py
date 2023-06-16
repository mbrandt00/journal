import json
import logging

LOGGER = logging.getLogger(__name__)
import json
import logging
import datetime as dt


def dicts_to_jsonl(list_of_dicts):
    list_of_json_strings = [json.dumps(_dict) for _dict in list_of_dicts]
    jsonl_string = "\n".join(list_of_json_strings)
    return jsonl_string


def date_decider(time_from, time_to):
    if time_from == "yesterday":
        after = dt.datetime.today() - dt.timedelta(days=1)
    else:
        after = dt.datetime.strptime(time_from, "%m-%d-%Y")
    if time_to == "today":
        before = dt.datetime.today()
    else:
        before = dt.datetime.strptime(time_to, "%m-%d-%Y")
    return before, after
