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

        # secrets
        strava_secret = secretsmanager.Secret.from_secret_attributes(
            self,
            generateResourceName("strava-secret"),
            secret_complete_arn="arn:aws:secretsmanager:us-east-1:211076628958:secret:dev/strava_api-gy8ImV",
        )

        strava_secret_lambda = _lambda.Function(
            self,
            generateResourceName("rotate-secret-strava"),
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            # role=strava_secret_lambda_role,
            function_name=generateResourceName("rotate-secret-strava"),
            code=_lambda.Code.from_asset(
                "../data-pipelines/stravaPipeline/lambdas/secret_rotator"
            ),
        )
        strava_secret_lambda.add_permission(
            "lambda-invoke-for-secrets-manager",
            principal=iam.ServicePrincipal("secretsmanager.amazonaws.com"),
        )
        strava_secret_lambda.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:UpdateSecretVersionStage"],
                resources=[strava_secret.secret_arn],
            )
        )

        strava_secret.grant_read(strava_secret_lambda)
        strava_secret.grant_write(strava_secret_lambda)

        data_sources = ["lastFm", "strava"]
        lambdas = []

        # ingest lambdas
        for data_source in data_sources:
            lambda_function_name = generateResourceName(f"ingest-{data_source}")

            cdk_lambda = _lambda.Function(
                self,
                lambda_function_name,
                runtime=_lambda.Runtime.PYTHON_3_9,
                handler="lambda_function.lambda_handler",
                function_name=lambda_function_name,
                code=_lambda.Code.from_asset(
                    f"../data-pipelines/{data_source}Pipeline/lambdas/{data_source}_ingest/",
                    bundling=bo(
                        image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                        command=[
                            "bash",
                            "-c",
                            "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
                        ],
                    ),
                ),
                # role=lambda_role,
                environment={},
            )
            if cdk_lambda.function_name == generateResourceName("ingest-strava"):
                cdk_lambda["environment"]["secret"] = strava_secret
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
