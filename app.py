#!/usr/bin/env python3
import os
import sys
import aws_cdk as cdk

# from dataPipelines.lastFmPipeline import test
from dataPipelines.data_stack import DataStack
from journal_stack import JournalStack

# github ci variables
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
AWS_REGION = os.getenv("AWS_REGION")
ENVIRONMENT = os.getenv("ENVIRONMENT")
PROJECT_NAME = os.getenv("PROJECT_NAME")
REGION_PREFIX = os.getenv("REGION_PREFIX")


def generateResourceName(resource):
    cf_name = resource.replace("_", "-")
    application_prefix = f"{REGION_PREFIX}-{ENVIRONMENT}-{PROJECT_NAME}"
    return f"{application_prefix}-{cf_name}"


DATA_STACK_NAME = generateResourceName("data-stack")
APP_STACK_NAME = generateResourceName("app-stack")
env = cdk.Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION)
stack_inputs = {"env": env}
app = cdk.App()
# Stacks
JournalStack(app, APP_STACK_NAME, **stack_inputs)
DataStack(app, DATA_STACK_NAME, **stack_inputs),


app.synth()
