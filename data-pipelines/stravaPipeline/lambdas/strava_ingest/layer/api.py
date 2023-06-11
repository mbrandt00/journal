import boto3
import json

client = boto3.client("secretsmanager")

access_token = json.loads(
    client.get_secret_value(SecretId="dev/strava_api")["SecretString"]
)["access_token"]
