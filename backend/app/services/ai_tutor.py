import os
from openai import OpenAI


class AITutor:
    """AI Tutor service for quantum computing education."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(api_key=self.api_key)

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

        response = self.client.responses.create(
            model="gpt-5.6-luna",
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

        response = self.client.responses.create(
            model="gpt-5.6-luna",
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
