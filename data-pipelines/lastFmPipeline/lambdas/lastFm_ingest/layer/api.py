import pylast
import boto3
import logging

LOGGER = logging.getLogger(__name__)


def get_secret():
    secret_name = "lastFm-secret"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except client.exceptions.ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    return get_secret_value_response["SecretString"]


API_KEY = "b34300d047409a302d40c726a9cf9928"  # this is a sample key
network = pylast.LastFMNetwork(
    api_key=API_KEY,
    api_secret=get_secret(),
)
