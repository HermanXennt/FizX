import openai
from django.conf import settings

from apps.core.exceptions import ApplicationError, ExternalServiceError

REQUEST_TIMEOUT_SECONDS = 30


def _client() -> openai.OpenAI:
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS)


def ask(*, system: str, message: str) -> str:
    if not settings.OPENAI_API_KEY:
        raise ApplicationError(detail="The AI assistant is not configured on this server.")

    try:
        response = _client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
        )
    except openai.OpenAIError as exc:
        raise ExternalServiceError(detail="Couldn't reach the AI assistant.") from exc

    reply = response.choices[0].message.content
    if not reply:
        raise ExternalServiceError(detail="The AI assistant returned an empty response.")
    return reply
