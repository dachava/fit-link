# app/services/ai_service.py
# Bedrock integration
import json
import boto3
from app.config import get_settings

settings = get_settings()


class AIService:

    def __init__(self):
        # boto3 picks up credentials from the pod's IAM role automatically in EKS
        # (via IRSA.... IAM Roles for Service Accounts)
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    async def generate_workout_plan(self, fitness_level: str, goals: list[str]) -> str:
        prompt = f"""You are an expert personal trainer. Generate a detailed, personalized weekly workout plan.

Fitness level: {fitness_level}
Goals: {', '.join(goals)}

Respond with a structured 7-day workout plan. For each day include:
- Workout name and focus area
- List of exercises with sets, reps, and rest periods
- Estimated duration
- Any important form or safety notes

Be specific and practical."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        })

        response = self._client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]