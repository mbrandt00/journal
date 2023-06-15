import os
import sys
from .cdk_helpers.glue_helper import (
    _create_glue_job,
)  # create_glue_workflow,
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
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    Duration,
)
from constructs import Construct

sys.path += ["./cdk_helpers/glue_helper.py"]


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


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # secrets
        strava_secret = secretsmanager.Secret.from_secret_attributes(
            self,
            "strava-secret",
            secret_complete_arn="arn:aws:secretsmanager:us-east-1:211076628958:secret:strava-secret-A8v6xb",
        )

        lastFm_secret = secretsmanager.Secret.from_secret_attributes(
            self,
            "lastFm-secret",
            secret_complete_arn="arn:aws:secretsmanager:us-east-1:211076628958:secret:lastFm-secret-6jyCjo",
        )

        raw_bucket = s3.Bucket(
            self,
            generateResourceName("s3-raw"),
            bucket_name=generateResourceName("s3-raw"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        secrets = [strava_secret, lastFm_secret]

        # ------------ingest lambdas-------------------------------------

        data_sources = ["lastFm", "strava"]
        lambdas = []

        for data_source in data_sources:
            lambda_function_name = generateResourceName(f"ingest-{data_source}")
            lambda_layer = _lambda.LayerVersion(
                self,
                generateResourceName(
                    f"{data_source}-layer",
                ),
                code=_lambda.AssetCode.from_asset(
                    f"./dataPipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/layer"
                ),
            )
            cdk_lambda = _lambda.Function(
                self,
                lambda_function_name,
                runtime=_lambda.Runtime.PYTHON_3_9,
                handler="lambda_function.lambda_handler",
                function_name=lambda_function_name,
                timeout=Duration.seconds(900),
                code=_lambda.Code.from_asset(
                    f"./dataPipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/",
                    # bundling=bo(
                    #     image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                    #     command=[
                    #         "bash",
                    #         "-c",
                    #         "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    #     ],
                    # ),
                ),
                layers=[lambda_layer],
                environment={"RAW_BUCKET": raw_bucket.bucket_name},
            )
            cdk_lambda.add_to_role_policy(
                iam.PolicyStatement(actions=["s3:*"], resources=["*"])
            )

            for secret in secrets:
                if secret.secret_name.split("-")[0] == data_source:
                    secret.grant_read(cdk_lambda)
            lambdas.append(cdk_lambda)

        parallel_execution = sfn.Parallel(self, "Parallel Ingest")
        for lambda_function in lambdas:
            parallel_execution.branch(
                sfn_tasks.LambdaInvoke(
                    self, lambda_function.function_name, lambda_function=lambda_function
                )
            )

        # state machine
        state_machine_name = generateResourceName("state-machine")
        sfn.StateMachine(
            self,
            state_machine_name,
            definition=parallel_execution,
            state_machine_name=state_machine_name,
        )

        # Glue Workflows
