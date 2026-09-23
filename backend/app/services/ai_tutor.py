from openai import AsyncOpenAI
from app.core.config import settings


class AITutor:
    """AI Tutor service for quantum computing education."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.openai_api_key

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(api_key=self.api_key, timeout=45, max_retries=1)

    async def chat(
        self,
        message: str,
        context: dict | None = None
    ) -> str:
        """Answer a student's quantum computing question."""

        context_text = ""

        if context:
            context_text = f"""
Student context:
{context}
"""

        instructions = """
You are an AI tutor for a quantum computing learning platform.

Your job is to teach quantum computing to students clearly and
accurately.

Rules:
- Explain concepts step by step.
- Adapt explanations to a beginner when no level is provided.
- Use simple examples before advanced mathematics.
- Use proper quantum notation such as |0⟩ and |1⟩ when useful.
- If the student asks about a quantum circuit, explain the gates
  in the order they occur.
- Do not pretend that an incorrect circuit is correct.
- Encourage understanding rather than simply giving an answer.
"""

        response = await self.client.responses.create(
            model=settings.ai_model,
            max_output_tokens=2000,
            store=False,
            instructions=instructions,
            input=f"""
{context_text}

Student question:
{message}
"""
        )

        return response.output_text

    async def debug_code(
        self,
        code: str,
        error: str
    ) -> dict:
        """Analyze quantum code and suggest a fix."""

        instructions = """
You are a quantum computing debugging assistant.

Analyze the student's code and error.

Return:
1. What the problem is.
2. Why it happens.
3. How to fix it.
4. Corrected code when appropriate.

Be beginner-friendly and do not invent errors that are not present.
"""

        response = await self.client.responses.create(
            model=settings.ai_model,
            max_output_tokens=2000,
            store=False,
            instructions=instructions,
            input=f"""
Student code:
{code}

Error:
{error}
"""
        )

        return {
            "explanation": response.output_text,
            "suggested_fix": "See the explanation above for the corrected approach."
        }
