import boto3
import json

client = boto3.client(
    "bedrock-runtime",
    region_name="eu-north-1"   # Change if you're using another region
)

response = client.converse(
    modelId="amazon.nova-lite-v1:0",  # Change if you're using another model
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