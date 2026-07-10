import asyncio

from src.aws.client import s3_client
from src.aws.constants import S3Constants
from src.config import settings


class S3Bucket:
    def __init__(self):
        self.__client = s3_client

    async def upload_file(self, file_type: str, file: str, key: str) -> str:
        await asyncio.to_thread(
            self.__client.upload_fileobj,
            Fileobj=file,
            Bucket=settings.BUCKET_NAME,
            Key=key,
            ExtraArgs={"ContentType": file_type},
        )
        return key

    async def delete_file(self, key: str):
        await asyncio.to_thread(
            self.__client.delete_object, Bucket=settings.BUCKET_NAME, Key=key
        )
        
    def presigned_url(self, key: str) -> str:
        url = self.__client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.BUCKET_NAME, "Key": key},
            ExpiresIn=S3Constants.PRESIGNED_URL_EXPIRE.value
        )
        return url


bucket_manager = S3Bucket()
