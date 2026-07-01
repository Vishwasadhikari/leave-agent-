import boto3
from app.config import AWS_REGION

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION
)