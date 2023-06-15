import os
import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_glue as glue,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    Duration,
)
from constructs import Construct

sys.path += ["./glue_helper.py"]


def generateResourceName(resource):
    application_prefix = "-".join(
        [
            x.lower()
            for x in [
                os.getenv("REGION_PREFIX"),
                os.getenv("ENVIRONMENT"),
                os.getenv("PROJECT_NAME"),
            ]
        ]
    )
    return application_prefix + "-" + resource


class JournalStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
