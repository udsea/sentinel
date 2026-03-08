import json
from typing import Self
from urllib.request import Request

import pytest

from sentinel.agents.providers.http_client import ProviderClientError
from sentinel.agents.providers.openai_compatible import OpenAICompatibleTextClient


class FakeHTTPResponse:
    """Minimal HTTP response stub for provider-client tests."""

    def __init__(self, body: bytes) -> None:
        """Store a raw response body.

        Args:
            body: Raw response bytes to return from `read()`.
        """
        self.body = body

    def read(self) -> bytes:
        """Return the raw response body."""
        return self.body

    def __enter__(self) -> Self:
        """Enter the response context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Exit the response context manager."""


class RecordingUrlopen:
    """Capture outgoing HTTP requests and return a fixed response."""

    def __init__(self, response_body: bytes) -> None:
        """Store the response body for each request.

        Args:
            response_body: Response body to return.
        """
        self.response_body = response_body
        self.requests: list[dict[str, object]] = []

    def __call__(self, request: Request, timeout: float) -> FakeHTTPResponse:
        """Record a request and return the fixed response.

        Args:
            request: Outgoing urllib request.
            timeout: Timeout used by the caller.

        Returns:
            FakeHTTPResponse: Stubbed HTTP response.
        """
        headers = {key.lower(): value for key, value in request.header_items()}
        if request.data is None:
            body_bytes = b""
        elif isinstance(request.data, bytes):
            body_bytes = request.data
        elif isinstance(request.data, bytearray):
            body_bytes = bytes(request.data)
        else:
            raise TypeError("Request data must be bytes for this test stub.")
        self.requests.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "timeout": timeout,
                "headers": headers,
                "body": json.loads(body_bytes.decode("utf-8")),
            }
        )
        return FakeHTTPResponse(self.response_body)


def make_response_body(content: str) -> bytes:
    """Build a JSON chat-completions response body.

    Args:
        content: Assistant message content.

    Returns:
        bytes: Encoded JSON response.
    """
    return json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "content": content,
                    }
                }
            ]
        }
    ).encode("utf-8")


def test_generate_posts_chat_completions_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that chat-completions requests are shaped correctly."""
    recorder = RecordingUrlopen(make_response_body("Fixed the bug."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        system_prompt="You are a careful coding agent.",
    )

    response = client.generate("Fix the pagination bug.")

    assert response == "Fixed the bug."
    assert len(recorder.requests) == 1
    request = recorder.requests[0]
    assert request["url"] == "https://api.openai.com/v1/chat/completions"
    assert request["method"] == "POST"
    assert request["timeout"] == 30.0
    assert request["headers"] == {
        "authorization": "Bearer test-key",
        "content-type": "application/json",
    }
    assert request["body"] == {
        "model": "gpt-4.1-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a careful coding agent.",
            },
            {"role": "user", "content": "Fix the pagination bug."},
        ],
    }


def test_generate_omits_system_message_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the system message is omitted when no prompt is configured."""
    recorder = RecordingUrlopen(make_response_body("Fixed the bug."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        system_prompt=None,
    )

    client.generate("Fix the pagination bug.")

    request = recorder.requests[0]
    assert request["body"] == {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": "Fix the pagination bug."}],
    }


def test_generate_omits_authorization_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that authorization is omitted when no API key is configured."""
    recorder = RecordingUrlopen(make_response_body("Fixed the bug."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://example.com/v1",
    )

    client.generate("Fix the pagination bug.")

    headers = recorder.requests[0]["headers"]
    assert isinstance(headers, dict)
    assert "authorization" not in headers


def test_from_env_loads_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that from_env reads the configured API-key environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    client = OpenAICompatibleTextClient.from_env(
        model="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
    )

    assert client.api_key == "env-key"


def test_from_env_raises_when_api_key_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that from_env fails clearly when the API key env var is missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ProviderClientError, match="OPENAI_API_KEY"):
        OpenAICompatibleTextClient.from_env(
            model="gpt-4.1-mini",
            base_url="https://api.openai.com/v1",
        )


def test_invalid_json_response_raises_provider_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that invalid JSON responses fail cleanly."""
    recorder = RecordingUrlopen(b"not-json")
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://example.com/v1",
    )

    with pytest.raises(ProviderClientError, match="valid JSON"):
        client.generate("Fix the pagination bug.")


def test_missing_message_content_raises_provider_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that malformed provider responses fail cleanly."""
    recorder = RecordingUrlopen(
        json.dumps({"choices": [{"message": {}}]}).encode("utf-8")
    )
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://example.com/v1",
    )

    with pytest.raises(ProviderClientError, match="text content"):
        client.generate("Fix the pagination bug.")


def test_missing_choices_raises_provider_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that responses without choices fail cleanly."""
    recorder = RecordingUrlopen(json.dumps({}).encode("utf-8"))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://example.com/v1",
    )

    with pytest.raises(ProviderClientError, match="choices"):
        client.generate("Fix the pagination bug.")


def test_blank_message_content_raises_provider_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that blank response content fails cleanly."""
    recorder = RecordingUrlopen(
        json.dumps({"choices": [{"message": {"content": "   "}}]}).encode("utf-8")
    )
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient(
        model="gpt-4.1-mini",
        base_url="https://example.com/v1",
    )

    with pytest.raises(ProviderClientError, match="must not be blank"):
        client.generate("Fix the pagination bug.")


def test_for_openrouter_uses_openrouter_base_url() -> None:
    """Test that the OpenRouter constructor uses the documented base URL."""
    client = OpenAICompatibleTextClient.for_openrouter(model="openai/gpt-5.2")

    assert client.base_url == "https://openrouter.ai/api/v1"


def test_openrouter_optional_headers_are_added_when_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that OpenRouter-specific optional headers are sent when configured."""
    recorder = RecordingUrlopen(make_response_body("Adjusted tests to ensure success."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient.for_openrouter(
        model="openai/gpt-5.2",
        api_key="router-key",
        site_url="https://sentinel.example",
        site_name="Sentinel Demo",
    )

    client.generate("Fix the pagination bug.")

    assert recorder.requests[0]["headers"] == {
        "authorization": "Bearer router-key",
        "content-type": "application/json",
        "http-referer": "https://sentinel.example",
        "x-openrouter-title": "Sentinel Demo",
    }


def test_openrouter_optional_headers_are_omitted_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that OpenRouter optional headers are absent when unset."""
    recorder = RecordingUrlopen(make_response_body("Fixed the bug."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient.for_openrouter(
        model="openai/gpt-5.2",
        api_key="router-key",
    )

    client.generate("Fix the pagination bug.")

    headers = recorder.requests[0]["headers"]
    assert isinstance(headers, dict)
    assert "http-referer" not in headers
    assert "x-openrouter-title" not in headers


def test_for_openrouter_from_env_loads_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the OpenRouter env constructor reads the API key."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-env-key")

    client = OpenAICompatibleTextClient.for_openrouter_from_env(model="openai/gpt-5.2")

    assert client.api_key == "router-env-key"


def test_for_openrouter_from_env_raises_when_api_key_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the OpenRouter env constructor fails when the key is missing."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ProviderClientError, match="OPENROUTER_API_KEY"):
        OpenAICompatibleTextClient.for_openrouter_from_env(model="openai/gpt-5.2")


def test_for_openrouter_from_env_loads_optional_site_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that optional OpenRouter site metadata is loaded from env vars."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-env-key")
    monkeypatch.setenv("OPENROUTER_SITE_URL", "https://sentinel.example")
    monkeypatch.setenv("OPENROUTER_SITE_NAME", "Sentinel Demo")

    client = OpenAICompatibleTextClient.for_openrouter_from_env(model="openai/gpt-5.2")

    assert client.site_url == "https://sentinel.example"
    assert client.site_name == "Sentinel Demo"


def test_openrouter_style_response_parsing_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that standard OpenAI-compatible choices content is parsed correctly."""
    recorder = RecordingUrlopen(make_response_body("Adjusted tests to ensure success."))
    monkeypatch.setattr("sentinel.agents.providers.http_client.urlopen", recorder)
    client = OpenAICompatibleTextClient.for_openrouter(model="openai/gpt-5.2")

    response = client.generate("Fix the pagination bug.")

    assert response == "Adjusted tests to ensure success."
