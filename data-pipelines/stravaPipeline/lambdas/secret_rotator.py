import json
import boto3
import sys
from botocore.exceptions import ClientError
import urllib3
from urllib.parse import urlencode

http = urllib3.PoolManager()


def lambda_handler(event, context):
    arn = event["SecretId"]
    token = event["ClientRequestToken"]
    step = event["Step"]
    client = boto3.client("secretsmanager")
    metadata = client.describe_secret(SecretId=arn)
    if not metadata["RotationEnabled"]:
        raise ValueError(f"Secret {arn} is not enabled for rotation")

    print(f"step: {step}")
    try:
        if step == "createSecret":
            createSecret(client, arn, token)
        elif step == "setSecret":
            setSecret(client, arn, token)
        elif step == "testSecret":
            testSecret(client, arn, token)
        elif step == "finishSecret":
            finishSecret(client, arn, token)
        else:
            raise ValueError("Invalid step parameter")
    except Exception as e:
        print(f"Error occurred: {e} in step {step}")
        # Reset the secret stage to base level (AWSCURRENT)
        # client.update_secret_version_stage(
        #     SecretId=arn,
        #     VersionStage="AWSCURRENT",
        #     RemoveFromVersionId=token
        # )
        sys.exit(1)


def createSecret(client, arn, token):
    secret_value = client.get_secret_value(SecretId=arn, VersionStage="AWSCURRENT")
    try:
        client.get_secret_value(
            SecretId=arn, VersionId=token, VersionStage="AWSPENDING"
        )
        print("found AWS PENDING Value")
    except client.exceptions.ResourceNotFoundException:
        if "SecretString" in secret_value:
            # maybe just pass in the raw string?
            secret_value = secret_value["SecretString"]
            secret_dict = json.loads(secret_value)
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
            client.put_secret_value(
                SecretId=arn,
                SecretString=updated_secret_string,
                VersionStages=["AWSPENDING"],
            )
        else:
            raise ValueError("No Secret String found!")


def setSecret(client, arn, token):
    print("No DB to update...")


def testSecret(client, arn, token):
    new_secret = client.get_secret_value(
        SecretId=arn, VersionId=token, VersionStage="AWSPENDING"
    )["SecretString"]
    json_secret = json.loads(new_secret)
    access_token = json_secret["access_token"]
    url = "https://www.strava.com/api/v3/athlete"
    resp = http.request("GET", url, headers={"Authorization": f"Bearer {access_token}"})
    # test instead of print...
    print(resp.data)


def finishSecret(client, arn, token):
    metadata = client.describe_secret(SecretId=arn)
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # already marked as current
                return
            client.update_secret_version_stage(
                SecretId=arn,
                VersionStage="AWSCURRENT",
                MoveToVersionId=token,
                RemoveFromVersionId=version,
            )
            break
