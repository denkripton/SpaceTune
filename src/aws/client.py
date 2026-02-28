import boto3

from src.aws.config import AWS_ACCESS, AWS_REGION, AWS_SECRET

s3_client = boto3.client("s3", aws_access_key_id=AWS_ACCESS, aws_secret_access_key=AWS_SECRET, region_name=AWS_REGION)