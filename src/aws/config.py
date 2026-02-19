from dotenv import load_dotenv
import os

load_dotenv()

AWS_SECRET = os.getenv("AWS_SECRET")
AWS_ACCESS = os.getenv("AWS_ACCESS")
AWS_REGION = os.getenv("AWS_REGION")

BUCKET_NAME = os.getenv("BUCKET_NAME")