import boto3
import json
from urllib.parse import urlencode
from stravalib.client import Client
from stravalib.exc import AccessUnauthorized
import urllib3
from urllib.parse import urlencode

http = urllib3.PoolManager()

sm_client = boto3.client("secretsmanager")


def get_current_access_token():
    secret_string = json.loads(
        sm_client.get_secret_value(SecretId="strava-secret")["SecretString"]
    )
    client = Client(access_token=secret_string["access_token"])
    try:
        client.get_athlete()
        return secret_string["access_token"]
    except AccessUnauthorized:
        return refresh_token(secret_string)


def refresh_token(secret_dict):
    client_secret = secret_dict["client_secret"]
    client_id = secret_dict["client_id"]
    refresh_token = secret_dict["refresh_token"]
    grant_type = secret_dict["grant_type"]
    args = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type,
        "refresh_token": refresh_token,
    }
    encoded_args = urlencode(args)
    url = "https://www.strava.com/api/v3/oauth/token?" + encoded_args
    resp = http.request("POST", url)
    data = json.loads(resp.data)
    args["refresh_token"] = data["refresh_token"]
    args["access_token"] = data["access_token"]
    updated_secret_string = json.dumps(args)
    sm_client.update_secret(
        SecretId="strava-secret",
        SecretString=updated_secret_string,
    )
    return args["access_token"]
