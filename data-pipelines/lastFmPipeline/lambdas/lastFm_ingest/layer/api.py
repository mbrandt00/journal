import pylast
import boto3
import json

client = boto3.client("secretsmanager")
api_secret = json.loads(
    client.get_secret_value(SecretId="lastFm-secret")["SecretString"]
)["secret"]


API_KEY = "b34300d047409a302d40c726a9cf9928"  # this is a sample key
network = pylast.LastFMNetwork(
    api_key=API_KEY,
    api_secret=api_secret,
)
