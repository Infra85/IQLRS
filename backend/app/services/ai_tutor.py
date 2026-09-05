"""AI Tutor service — handles communication with LLM API."""


class AITutor:
    """Quantum computing AI tutor powered by Claude or OpenAI."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, message: str, context: dict | None = None) -> str:
        """Send a message with optional circuit/code context."""
        # TODO: Call LLM API with quantum-specialized system prompt
        raise NotImplementedError

    async def debug_code(self, code: str, error: str) -> dict:
        """Analyze code errors and suggest fixes."""
        # TODO: Send code + error to LLM for analysis
        raise NotImplementedError
