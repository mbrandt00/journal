import os
import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ecr as ecr,
    aws_glue as glue,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_cloudfront as cloudfront,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_ssm as ssm,
    aws_s3_deployment as s3_deployment,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
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

        apex_domain = os.getenv("JOURNAL_DOMAIN")
        # react resources
        react_domain = apex_domain  # config for dev here
        zone = route53.HostedZone.from_lookup(
            self, generateResourceName("hosted-zone"), domain_name=apex_domain
        )
        react_bucket = s3.bucket(
            self,
            generateResourceName("react-bucket"),
            bucket_name=generateResourceName("react-bucket"),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            website_index_document="index.html",
        )

        # Origin Access Identity
        react_oai = cloudfront.OriginAccessIdentity(
            self,
            generateResourceName("react-oai"),
            comment=f"Connects {generateResourceName('react-bucket')} to {generateResourceName('react-cf-distribution')}",
        )
        react_bucket.grant_read(react_oai)

        react_cert_arn_param = generateResourceName("react-certificate-arn")
        react_cert_arn = str(
            ssm.StringParameter.value_from_lookup(self, react_cert_arn_param)
        )
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
                certificate=acm.Certificate.from_certificate_arn(
                    self, generateResourceName("react-cert"), react_cert_arn
                ),
                aliases=[react_domain],
            ),
        )

        # Route53 alias record for CloudFront Distribution
        route53.ARecord(
            self,
            generateResourceName("react-alias-record"),
            record_name=react_domain,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(react_distribution)
            ),
            zone=zone,
        )
        # deploy react front end
        react_deploy = s3_deployment.BucketDeployment(
            self,
            generateResourceName("react-s3-deployment"),
            sources=[s3_deployment.Source.asset("./front_end/build")],
            destination_bucket=react_bucket,
            distribution=react_distribution,
            distribution_paths=["/*"],
        )
