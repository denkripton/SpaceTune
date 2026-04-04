import boto3
from src.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS,
    aws_secret_access_key=settings.AWS_SECRET,
    region_name=settings.AWS_REGION,
)
