from .glue_helper import _create_glue_job  # create_glue_workflow,
import os
import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_lambda as _lambda,
    aws_iam as iam,
    # aws_lambda_python_alpha as lpa,
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
        for data_source in data_sources:

            # lambda definition
            layer_name = generateResourceName(f"lambda-layer-{data_source}")

            # lambda_layer = lpa.PythonLayerVersion(
            #     self,
            #     layer_name,
            #     layer_version_name=layer_name,
            #     entry=f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_layer/'
            # )
            lambdaLayer = _lambda.LayerVersion(
                self,
                layer_name,
                code=_lambda.AssetCode(
                    f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_layer/'),
                compatible_runtimes=[
                    _lambda.Runtime.PYTHON_3_9],
            )
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
                            "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                        ],
                    ),
                ),
                # role=lambda_role,
                layers=[lambdaLayer],
                environment={}
            )            # lambda_function_name = generateResourceName(
        #     f"ingest-{data_source}")

        # lambda_function = lpa.PythonFunction(
        #     self,
        #     lambda_function_name,
        #     runtime=_lambda.Runtime.PYTHON_3_7,
        #     timeout=Duration.seconds(900),
        #     memory_size=256,
        #     # environment = {},
        #     entry=f'../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/',
        #     index='lambda_function.py',
        #     handler='lambda_handler',
        #     layers=[lambda_layer]
        # )

        lambdas.append(cdk_lambda)
        parallel_execution = sfn.Parallel(self, 'ParallelIngest')
        for lambda_function in lambdas:
            parallel_execution.branch(sfn_tasks.LambdaInvoke(
                self,
                f'Invoke{lambda_function.function_name}',
                lambda_function=lambda_function)
            )

        # state machine
        # definition = parallel_execution.build()
        state_machine_name = generateResourceName('state-machine')

        # state_machine = sfn.StateMachine(
        sfn.StateMachine(
            self,
            state_machine_name,

            definition=parallel_execution,

            state_machine_name=state_machine_name
        )

        # Glue Workflows
