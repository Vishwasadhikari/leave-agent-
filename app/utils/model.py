from strands.models import BedrockModel

from app.config import (
    AWS_REGION,
    BEDROCK_MODEL_ID
)

# Shared Nova Lite model used by all agents
nova_model = BedrockModel(
    region_name=AWS_REGION,
    model_id=BEDROCK_MODEL_ID,
)