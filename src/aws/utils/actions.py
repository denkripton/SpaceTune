from src.aws.client import s3_client
from src.aws.config import BUCKET_NAME, PRESIGNED_URL_EXP


class S3Bucket:
    def __init__(self):
        self.client = s3_client

    def upload_file(self, file_type: str, file: str, key: str) -> str:
        self.client.upload_fileobj(
            Fileobj=file,
            Bucket=BUCKET_NAME,
            Key=key,
            ExtraArgs={"ContentType": file_type},
        )
        return key

    def delete_file(self, key: str):
        self.client.delete_object(Bucket=BUCKET_NAME, Key=key)

    def presigned_url(self, key: str) -> str:
        url = self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXP,
        )
        return url

bucket_manager = S3Bucket()