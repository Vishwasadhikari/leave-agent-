import boto3

dynamodb = boto3.client(
    "dynamodb",
    region_name="eu-north-1"
)

print(dynamodb.list_tables())