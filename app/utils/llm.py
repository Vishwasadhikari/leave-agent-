from app.utils.bedrock import bedrock_client
from app.config import BEDROCK_MODEL_ID


def ask_llm(prompt: str):

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 100,
            "temperature": 0
        }
    )

    return response["output"]["message"]["content"][0]["text"]