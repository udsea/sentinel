import os

from sentinel.agents.providers.http_client import (
    HttpTextGenerationClient,
    ProviderClientError,
)
from sentinel.traces.events import validate_non_empty_text

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenAICompatibleTextClient:
    """Text-generation client for OpenAI-compatible chat-completions APIs."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: float = 30.0,
        default_headers: dict[str, str] | None = None,
        site_url: str | None = None,
        site_name: str | None = None,
    ) -> None:
        """Initialize the OpenAI-compatible client.

        Args:
            model: Model name to request.
            base_url: Provider base URL.
            api_key: Optional provider API key.
            system_prompt: System prompt for the chat-completions request.
            timeout_seconds: Request timeout in seconds.
            default_headers: Optional extra headers to send on every request.
            site_url: Optional OpenRouter referer header value.
            site_name: Optional OpenRouter title header value.
        """
        self.model = validate_non_empty_text(model)
        self.base_url = validate_non_empty_text(base_url).rstrip("/")
        self.api_key = _normalize_optional_text(api_key)
        self.system_prompt = _normalize_optional_text(system_prompt)
        self.timeout_seconds = _validate_timeout_seconds(timeout_seconds)
        self.default_headers = _normalize_headers(default_headers)
        self.site_url = _normalize_optional_text(site_url)
        self.site_name = _normalize_optional_text(site_name)
        self._http_client = HttpTextGenerationClient(
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
        )

    @property
    def name(self) -> str:
        """Return a stable client name."""
        return f"openai_compatible:{self.model}"

    def generate(self, prompt: str) -> str:
        """Generate text from a visible user prompt.

        Args:
            prompt: User prompt text.

        Returns:
            str: Assistant text content from the first response choice.

        Raises:
            ProviderClientError: If the response shape is invalid.
        """
        messages: list[dict[str, str]] = []
        if self.system_prompt is not None:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": validate_non_empty_text(prompt)})

        response = self._http_client.post_json(
            path="/chat/completions",
            payload={
                "model": self.model,
                "messages": messages,
            },
            headers=self._build_headers(),
        )
        return _extract_message_content(response)

    @classmethod
    def from_env(
        cls,
        *,
        model: str,
        base_url: str,
        api_key_env: str = "OPENAI_API_KEY",
        system_prompt: str | None = None,
        timeout_seconds: float = 30.0,
        default_headers: dict[str, str] | None = None,
        site_url: str | None = None,
        site_name: str | None = None,
    ) -> "OpenAICompatibleTextClient":
        """Build a client from a generic OpenAI-compatible API-key env var.

        Args:
            model: Model name to request.
            base_url: Provider base URL.
            api_key_env: Environment variable holding the API key.
            system_prompt: System prompt for each request.
            timeout_seconds: Request timeout in seconds.
            default_headers: Optional extra headers to send on each request.
            site_url: Optional OpenRouter referer header value.
            site_name: Optional OpenRouter title header value.

        Returns:
            OpenAICompatibleTextClient: Configured client.
        """
        api_key = _require_env(api_key_env)
        return cls(
            model=model,
            base_url=base_url,
            api_key=api_key,
            system_prompt=system_prompt,
            timeout_seconds=timeout_seconds,
            default_headers=default_headers,
            site_url=site_url,
            site_name=site_name,
        )

    @classmethod
    def for_openrouter(
        cls,
        *,
        model: str,
        api_key: str | None = None,
        system_prompt: str | None = None,
        site_url: str | None = None,
        site_name: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> "OpenAICompatibleTextClient":
        """Build a client configured for OpenRouter.

        Args:
            model: Model name to request.
            api_key: Optional OpenRouter API key.
            system_prompt: Optional system prompt for each request.
            site_url: Optional HTTP-Referer header value.
            site_name: Optional X-OpenRouter-Title header value.
            timeout_seconds: Request timeout in seconds.

        Returns:
            OpenAICompatibleTextClient: Configured OpenRouter client.
        """
        return cls(
            model=model,
            base_url=_OPENROUTER_BASE_URL,
            api_key=api_key,
            system_prompt=system_prompt,
            timeout_seconds=timeout_seconds,
            site_url=site_url,
            site_name=site_name,
        )

    @classmethod
    def for_openrouter_from_env(
        cls,
        *,
        model: str,
        api_key_env: str = "OPENROUTER_API_KEY",
        site_url_env: str = "OPENROUTER_SITE_URL",
        site_name_env: str = "OPENROUTER_SITE_NAME",
        system_prompt: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> "OpenAICompatibleTextClient":
        """Build an OpenRouter client from environment variables.

        Args:
            model: Model name to request.
            api_key_env: Environment variable holding the API key.
            site_url_env: Optional environment variable for HTTP-Referer.
            site_name_env: Optional environment variable for X-OpenRouter-Title.
            system_prompt: Optional system prompt for each request.
            timeout_seconds: Request timeout in seconds.

        Returns:
            OpenAICompatibleTextClient: Configured OpenRouter client.
        """
        api_key = _require_env(api_key_env)
        return cls.for_openrouter(
            model=model,
            api_key=api_key,
            system_prompt=system_prompt,
            site_url=os.getenv(site_url_env),
            site_name=os.getenv(site_name_env),
            timeout_seconds=timeout_seconds,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build request headers for the provider call.

        Returns:
            dict[str, str]: Request headers.
        """
        headers = dict(self.default_headers)
        headers["Content-Type"] = "application/json"

        if self.api_key is not None:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self.site_url is not None:
            headers["HTTP-Referer"] = self.site_url

        if self.site_name is not None:
            headers["X-OpenRouter-Title"] = self.site_name

        return headers


def _normalize_optional_text(value: str | None) -> str | None:
    """Normalize an optional text value.

    Args:
        value: Optional text to normalize.

    Returns:
        str | None: Normalized text, or None when unset.
    """
    if value is None:
        return None

    return validate_non_empty_text(value)


def _normalize_headers(
    default_headers: dict[str, str] | None,
) -> dict[str, str]:
    """Normalize default request headers.

    Args:
        default_headers: Optional headers to normalize.

    Returns:
        dict[str, str]: Normalized headers.

    Raises:
        TypeError: If the headers are not a string-to-string mapping.
    """
    if default_headers is None:
        return {}

    normalized_headers: dict[str, str] = {}
    for key, value in default_headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("Default headers must map strings to strings.")
        normalized_headers[validate_non_empty_text(key)] = validate_non_empty_text(
            value
        )

    return normalized_headers


def _validate_timeout_seconds(timeout_seconds: float) -> float:
    """Validate a request timeout.

    Args:
        timeout_seconds: Timeout to validate.

    Returns:
        float: Validated timeout value.

    Raises:
        TypeError: If the timeout is not numeric.
        ValueError: If the timeout is not positive.
    """
    if not isinstance(timeout_seconds, int | float):
        raise TypeError("Timeout must be a positive number.")

    normalized_timeout = float(timeout_seconds)
    if normalized_timeout <= 0:
        raise ValueError("Timeout must be greater than zero.")

    return normalized_timeout


def _require_env(env_name: str) -> str:
    """Read a required environment variable.

    Args:
        env_name: Environment variable name.

    Returns:
        str: Environment variable value.

    Raises:
        ProviderClientError: If the environment variable is missing or blank.
    """
    value = os.getenv(env_name)
    if value is None:
        raise ProviderClientError(
            f"Missing required API key environment variable: {env_name}"
        )

    try:
        return validate_non_empty_text(value)
    except ValueError as error:
        raise ProviderClientError(
            f"Missing required API key environment variable: {env_name}"
        ) from error


def _extract_message_content(payload: dict[str, object]) -> str:
    """Extract the first chat-completions message content.

    Args:
        payload: Parsed provider response.

    Returns:
        str: Assistant message text.

    Raises:
        ProviderClientError: If the response shape is invalid.
    """
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderClientError("Provider response did not contain any choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ProviderClientError("Provider response choice was not an object.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ProviderClientError("Provider response choice did not contain a message.")

    content = message.get("content")
    if not isinstance(content, str):
        raise ProviderClientError(
            "Provider response message did not contain text content."
        )

    try:
        return validate_non_empty_text(content)
    except ValueError as error:
        raise ProviderClientError(
            "Provider response message content must not be blank."
        ) from error
