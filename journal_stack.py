import os
import sys
import json
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_cloudfront as cloudfront,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_ssm as ssm,
    aws_s3_deployment as s3_deployment,
    aws_secretsmanager as secretsmanager,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secrets_manager,
    RemovalPolicy,
    SecretValue,
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

        # ----------frontend---------------

        apex_domain = os.getenv("JOURNAL_DOMAIN")
        hosted_zone = route53.HostedZone.from_lookup(
            self,
            generateResourceName("chronolog-hosted-zone"),
            domain_name=f"{apex_domain}.",
        )

        react_certificate = acm.Certificate(
            self,
            generateResourceName("react-certificate"),
            domain_name=apex_domain,
            certificate_name=generateResourceName("react-certificate"),
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Origin Access Identity
        react_bucket = s3.Bucket(
            self,
            generateResourceName("react-bucket"),
            bucket_name=generateResourceName("react-bucket"),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            website_index_document="index.html",
        )

        react_oai = cloudfront.OriginAccessIdentity(
            self,
            generateResourceName("react-oai"),
            comment=f"Connects {generateResourceName('react-bucket')} to {generateResourceName('react-cf-distribution')}",
        )
        react_bucket.grant_read(react_oai)

        react_distribution = cloudfront.CloudFrontWebDistribution(
            self,
            generateResourceName("react-cf-distribution"),
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=react_bucket, origin_access_identity=react_oai
                    ),
                    behaviors=[
                        cloudfront.Behavior(is_default_behavior=True),
                        cloudfront.Behavior(
                            path_pattern="/*",
                            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                            forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                                query_string=True,
                                headers=[
                                    "Origin",
                                    "Access-Control-Request-Method",
                                    "Access-Control-Request-Headers",
                                ],
                            ),
                        ),
                    ],
                )
            ],
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=404,
                    response_code=200,
                    error_caching_min_ttl=10,
                    response_page_path="/index.html",
                ),
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=403,
                    response_code=200,
                    error_caching_min_ttl=10,
                    response_page_path="/index.html",
                ),
            ],
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                certificate=react_certificate,
                aliases=[apex_domain],
            ),
        )

        # deploy react front end
        s3_deployment.BucketDeployment(
            self,
            generateResourceName("react-s3-deployment"),
            sources=[s3_deployment.Source.asset("./front_end/build")],
            destination_bucket=react_bucket,
            distribution=react_distribution,
            distribution_paths=["/*"],
        )

        # Route53 alias record for CloudFront Distribution
        route53.ARecord(
            self,
            generateResourceName("react-alias-record"),
            record_name=apex_domain,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(react_distribution)
            ),
            zone=hosted_zone,
        )

        # Create the Route53 record to alias www.chronolog.us to the CloudFront distribution
        # route53.ARecord(
        #     self,
        #     "react-www-record",
        #     zone=hosted_zone,
        #     target=route53.RecordTarget.from_alias(
        #         route53_targets.CloudFrontTarget(react_distribution)
        #     ),
        #     record_name="www.chronolog.us",
        # )

        # ----------backend---------------

        vpc = ec2.Vpc(
            self,
            generateResourceName("journal-vpc"),
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=1,
        )
        # RDS Master Credentials
        rds_credentials = secrets_manager.Secret(
            self,
            generateResourceName("rds-secret"),
            secret_name=generateResourceName("rds-secret"),
            generate_secret_string=secrets_manager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {"username": os.getenv("DATABASE_USERNAME")}
                ),
                exclude_punctuation=True,
                include_space=False,
                generate_string_key="password",
            ),
        )

        # rds DB
        rds_instance = rds.DatabaseInstance(
            self,
            generateResourceName("rds"),
            credentials=rds.Credentials.from_secret(rds_credentials),
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            database_name=os.getenv("DATABASE_NAME"),
            vpc=vpc,
            publicly_accessible=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        repo = ecr.Repository.from_repository_name(
            self, generateResourceName("ecr"), repository_name=os.getenv("ECR_REPO")
        )
        apex_domain = os.getenv("RAILS_DOMAIN")

        # Rails API IAM User
        rails_iam_user_name = generateResourceName("rails-iam-user")
        rails_iam_user = iam.User(
            self, rails_iam_user_name, user_name=rails_iam_user_name
        )

        # Create Access Key and store in Secrets Manager
        rails_iam_user_access_key = iam.AccessKey(
            self, f"{rails_iam_user_name}-access-key", user=rails_iam_user
        )
        rails_iam_user_access_key_secret = secretsmanager.Secret(
            self,
            f"{rails_iam_user_name}-secret",
            secret_name=f"{rails_iam_user_name}-secret",
            secret_object_value={
                "AccessKey": SecretValue.unsafe_plain_text(
                    rails_iam_user_access_key.access_key_id
                ),
                "SecretAccessKey": rails_iam_user_access_key.secret_access_key,
            },
        )

        # fargate service

        task_definition = ecs.FargateTaskDefinition(
            self,
            generateResourceName("Task-Definition"),
            cpu=256,
            memory_limit_mib=512,
        )
        image_tag = os.getenv("RAILS_IMAGE_TAG")
        task_definition.add_container(
            "web",
            image=ecs.EcrImage(repo, image_tag),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="web_container"),
            entry_point=["./docker-scripts/docker-entrypoint.sh"],
            container_name="web",
            cpu=256,
            memory_limit_mib=512,
            port_mappings=[ecs.PortMapping(container_port=80)],
            environment={
                "RAILS_ENV": os.getenv("RAILS_ENV"),
                "AWS_REGION": os.getenv("AWS_REGION"),
                "RAILS_DOMAIN": os.getenv("RAILS_DOMAIN"),
                "REACT_DOMAIN": os.getenv("JOURNAL_DOMAIN"),
                "DATABASE_HOST": rds_instance.db_instance_endpoint_address,
                "DATABASE_NAME": os.getenv("DATABASE_NAME"),
                "DATABASE_USERNAME": SecretValue.unsafe_unwrap(
                    rds_credentials.secret_value_from_json("username")
                ),
                "DATABASE_PASSWORD": SecretValue.unsafe_unwrap(
                    rds_credentials.secret_value_from_json("password")
                ),
                "RAILS_AWS_ACCESS_KEY": SecretValue.unsafe_unwrap(
                    rails_iam_user_access_key_secret.secret_value_from_json("AccessKey")
                ),
                "RAILS_AWS_SECRET_KEY": SecretValue.unsafe_unwrap(
                    rails_iam_user_access_key_secret.secret_value_from_json(
                        "SecretAccessKey"
                    )
                ),
                "REGION": os.getenv("AWS_REGION"),
            },
        )

        rails_certificate = acm.Certificate(
            self,
            generateResourceName("rails-certificate"),
            domain_name=apex_domain,
            certificate_name=generateResourceName("rails-certificate"),
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        fargate = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            generateResourceName("ecs-fargateService"),
            vpc=vpc,
            domain_name=apex_domain,
            domain_zone=hosted_zone,
            certificate=rails_certificate,
            health_check_grace_period=Duration.seconds(150),
            enable_execute_command=True,
            cpu=256,
            memory_limit_mib=512,
            task_definition=task_definition,
        )

        rds_instance.connections.allow_from(
            fargate.service,
            ec2.Port.tcp(5432),
            "Ingress rule for Fargate containers to access RDS",
        )

        # Configure healthcheck
        fargate.target_group.configure_health_check(
            path="/healthcheck",
            interval=Duration.seconds(100),
            timeout=Duration.seconds(10),
        )
