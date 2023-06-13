import json
import logging

LOGGER = logging.getLogger(__name__)
import json
import logging


def dicts_to_jsonl(list_of_dicts):
    list_of_json_strings = [json.dumps(_dict) for _dict in list_of_dicts]
    jsonl_string = "\n".join(list_of_json_strings)
    return jsonl_string
