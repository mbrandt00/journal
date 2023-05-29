import os
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_lambda as _lambda,
    aws_iam as iam, 
    aws_lambda_python_alpha as lpa, 
    aws_events as events, 
    aws_events_targets as targets, 
    aws_glue_alpha as alpha_glue,
    Duration,
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
    
        # lambda definition 
        DATA_SOURCE = 'lastFm'
        lastfm_layer_name = generateResourceName('lambda-layer-lastFm')

        lambda_layer = lpa.PythonLayerVersion(
            self, 
            lastfm_layer_name,
            layer_version_name=lastfm_layer_name,
            entry =f'../data-pipelines/{DATA_SOURCE}Pipeline/lambdas/{DATA_SOURCE}_layer/'
        )

        lambda_function_name = generateResourceName('ingest-lastFm')
        
        lambda_function = lpa.PythonFunction(
            self, 
            lambda_function_name, 
            runtime=_lambda.Runtime.PYTHON_3_7, 
            timeout= Duration.seconds(900),
            memory_size=256,
            # environment = {}, 
            entry=f'../data-pipelines/{DATA_SOURCE}Pipeline/lambdas/{DATA_SOURCE}_ingest/',
            index='lambda_function.py',
            handler = 'lambda_handler', 
            layers=[lambda_layer]
        )

        
