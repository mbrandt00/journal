from .glue_helper import _create_glue_job  # create_glue_workflow,
import os
import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_lambda as _lambda,
    aws_iam as iam,
    BundlingOptions as bo,
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

        data_sources = ['lastFm', 'strava']
        lambdas = []

        # ingest lambdas
        for data_source in data_sources:

            lambda_function_name = generateResourceName(
                f"ingest-{data_source}")

            cdk_lambda = _lambda.Function(
                self,
                lambda_function_name,
                runtime=_lambda.Runtime.PYTHON_3_9,
                handler='lambda_function.lambda_handler',
                function_name=lambda_function_name,
                code=_lambda.Code.from_asset(
                    f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/',
                    bundling=bo(
                        image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                        command=[
                            "bash", "-c",
                            "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
                            # "cp -au "
                        ],
                    ),
                ),
                # role=lambda_role,
                environment={}
            )
            lambdas.append(cdk_lambda)

        parallel_execution = sfn.Parallel(self, 'Parallel Ingest')
        for lambda_function in lambdas:
            parallel_execution.branch(sfn_tasks.LambdaInvoke(
                self,
                lambda_function.function_name,
                lambda_function=lambda_function)
            )

        # state machine
        state_machine_name = generateResourceName('state-machine')
        sfn.StateMachine(
            self,
            state_machine_name,
            definition=parallel_execution,
            state_machine_name=state_machine_name
        )

        # Glue Workflows
