import os
import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_glue as glue,
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
        )  # set cidr range?

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
            image=ecs.ContainerImage.from_ecr_repository(
                repo.repository_uri_for_image_tag(image_tag)
            ),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="web_container"),
            entry_point=["./docker-scripts/docker-entrypoint.sh"],
            container_name="web",
            cpu=256,
            memory_limit_mib=512,
            port_mappings=[ecs.PortMapping(container_port=80)],
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
