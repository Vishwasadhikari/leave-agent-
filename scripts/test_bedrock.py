import boto3
import json

client = boto3.client(
    "bedrock-runtime",
    region_name="eu-north-1"   # Change if you're using another region
)

response = client.converse(
    modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": "Say Hello"
                }
            ]
        }
    ]
)

print(response["output"]["message"]["content"][0]["text"])