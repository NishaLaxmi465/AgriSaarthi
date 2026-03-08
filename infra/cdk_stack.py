"""
AgriSaarthi - AWS Infrastructure (CDK)
Provisions: Lambda, API Gateway, DynamoDB, ElastiCache, S3, Bedrock IAM
"""

from aws_cdk import (
    Stack, Duration, RemovalPolicy,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
)
from constructs import Construct


class AgriSaarthiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ─── S3: Crop Image Storage ───────────────────────────────────────
        image_bucket = s3.Bucket(
            self, "CropImages",
            bucket_name="agrisaarthi-crop-images",
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(7),  # Auto-delete after 7 days
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ─── DynamoDB Tables ──────────────────────────────────────────────
        users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="agrisaarthi-users",
            partition_key=dynamodb.Attribute(
                name="phone_hash", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        conversations_table = dynamodb.Table(
            self, "ConversationsTable",
            table_name="agrisaarthi-conversations",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
        )

        pest_detections_table = dynamodb.Table(
            self, "PestDetectionsTable",
            table_name="agrisaarthi-pest-detections",
            partition_key=dynamodb.Attribute(
                name="detection_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ─── IAM Role for Lambda ──────────────────────────────────────────
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Bedrock access
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            resources=["arn:aws:bedrock:ap-south-1::foundation-model/*"],
        ))

        # DynamoDB access
        for table in [users_table, conversations_table, pest_detections_table]:
            table.grant_read_write_data(lambda_role)

        # S3 access
        image_bucket.grant_read_write(lambda_role)

        # ─── Lambda Function ───────────────────────────────────────────────
        api_lambda = lambda_.DockerImageFunction(
            self, "AgriSaarthiLambda",
            function_name="agrisaarthi-api",
            code=lambda_.DockerImageCode.from_image_asset("."),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "AWS_REGION_NAME": "ap-south-1",
                "DYNAMODB_TABLE_USERS": "agrisaarthi-users",
                "DYNAMODB_TABLE_CONVERSATIONS": "agrisaarthi-conversations",
                "S3_BUCKET_IMAGES": "agrisaarthi-crop-images",
            },
        )

        # ─── API Gateway ──────────────────────────────────────────────────
        api = apigw.RestApi(
            self, "AgriSaarthiAPI",
            rest_api_name="agrisaarthi-api",
            description="AgriSaarthi WhatsApp Bot API",
        )

        proxy = api.root.add_proxy(
            any_method=True,
            default_integration=apigw.LambdaIntegration(api_lambda),
        )
