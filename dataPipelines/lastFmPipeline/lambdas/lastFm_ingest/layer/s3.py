import boto3
import json
import sys
import logging

logger = logging.getLogger(__name__)


def upload_object(bucket_name, s3_loc, object, is_string=False):
    try:
        if not is_string:
            object = json.dumps(object)
        S3 = boto3.resource("s3")
        S3.Bucket(bucket_name).put_object(Key=s3_loc, Body=object)
        logger.info(f"Finished upload to {bucket_name}/{s3_loc}")
    except Exception as e:
        logger.error(e)
        sys.exit(1)
