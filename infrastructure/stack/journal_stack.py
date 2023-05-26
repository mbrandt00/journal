import os
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr
)
from constructs import Construct

def generateResourceName(resource):
    application_prefix = "-".join([x.lower() for x in [os.getenv("REGION_PREFIX"), os.getenv("ENVIRONMENT"), os.getenv("PROJECT_NAME")]])
    return application_prefix + resource
class JournalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ecr repository 
        repo = ecr.Repository(
            self, generateResourceName("ecr"), repository_name=os.getenv("ECR_REPO")
            ) 
