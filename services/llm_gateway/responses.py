from dataclasses import dataclass

from django.conf import settings
from openai import OpenAI


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model_name: str
    token_count: int | None = None


class LocalLLMProvider:
    def generate(self, *, instructions: str, prompt: str) -> LLMResponse:
        first_label = ""
        for line in prompt.splitlines():
            if line.startswith("[D") and "]" in line:
                first_label = line.split("]", 1)[0] + "]"
                break

        if first_label:
            content = (
                "I found relevant context in the uploaded documents. "
                f"Use the cited source passage to verify the answer. {first_label}"
            )
        else:
            content = "I don't know based on the available documents."

        return LLMResponse(content=content, model_name="local-llm")


class OpenAIResponsesProvider:
    def __init__(self, *, api_key: str, model: str, max_output_tokens: int):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens

    def generate(self, *, instructions: str, prompt: str) -> LLMResponse:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
            max_output_tokens=self.max_output_tokens,
        )
        usage = getattr(response, "usage", None)
        token_count = getattr(usage, "total_tokens", None) if usage else None
        return LLMResponse(
            content=response.output_text,
            model_name=self.model,
            token_count=token_count,
        )


def get_llm_provider():
    provider = settings.LLM_PROVIDER.lower()
    if provider == "local":
        return LocalLLMProvider()
    if provider == "openai":
        return OpenAIResponsesProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
