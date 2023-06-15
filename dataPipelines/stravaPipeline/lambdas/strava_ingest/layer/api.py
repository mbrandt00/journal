import boto3
import json

client = boto3.client("secretsmanager")

access_token = json.loads(
    client.get_secret_value(SecretId="strava-secret")["SecretString"]
)["access_token"]
