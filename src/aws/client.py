import boto3

from src.aws.config import AWS_ACCESS, AWS_REGION, AWS_SECRET

def s3_client():
    return boto3.client("s3", aws_access_key=AWS_ACCESS, aws_secret_access_key=AWS_SECRET, region_name=AWS_REGION)