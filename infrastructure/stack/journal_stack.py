from .glue_helper import _create_glue_job  # create_glue_workflow,
import os
import sys
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
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_glue as glue,
    Duration,
)
from constructs import Construct
sys.path += ['./glue_helper.py']


def generateResourceName(resource):
    application_prefix = "-".join([x.lower() for x in [os.getenv(
        "REGION_PREFIX"), os.getenv("ENVIRONMENT"), os.getenv("PROJECT_NAME")]])
    return application_prefix + '-' + resource


class JournalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        SEED_ENDPOINTS = [
            {
                "endpoint_name": "lastFm",
            },
        ]
        seed_node = sfn.Pass(
            self,
            "API Seed Values",
            result=sfn.Result.from_array(SEED_ENDPOINTS)
        )

        data_sources = ['lastFm']
        for data_source in data_sources:

            # lambda definition
            layer_name = generateResourceName(f"lambda-layer-{data_source}")

            lambda_layer = lpa.PythonLayerVersion(
                self,
                layer_name,
                layer_version_name=layer_name,
                entry=f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_layer/'
            )

            lambda_function_name = generateResourceName(
                f"ingest-{data_source}")

            lambda_function = lpa.PythonFunction(
                self,
                lambda_function_name,
                runtime=_lambda.Runtime.PYTHON_3_7,
                timeout=Duration.seconds(900),
                memory_size=256,
                # environment = {},
                entry=f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/',
                index='lambda_function.py',
                handler='lambda_handler',
                layers=[lambda_layer]
            )
            lambda_node = sfn_tasks.LambdaInvoke(
                self,
                f"{data_source} Ingest Lambda",
                lambda_function=lambda_function
            )
            map_node = sfn.Map(
                self,
                "Map State",
                items_path=sfn.JsonPath.string_at("$")
            )
            map_node.iterator(lambda_node)

        definition = (
            seed_node.next(map_node)
            # .next(glue raw node)
        )

        # state machine

        state_machine_name = generateResourceName('state-machine')

        # state_machine = sfn.StateMachine(
        sfn.StateMachine(
            self,
            state_machine_name,
            definition=definition,
            state_machine_name=state_machine_name
        )

        # Glue Workflows
