import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sentinel.traces.events import validate_non_empty_text


class ProviderClientError(RuntimeError):
    """Raised when a provider request or response cannot be handled."""


class HttpTextGenerationClient:
    """Minimal JSON-over-HTTP transport for model-facing provider clients."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize the HTTP transport client.

        Args:
            base_url: Provider base URL.
            timeout_seconds: Request timeout in seconds.
        """
        self.base_url = _normalize_base_url(base_url)
        self.timeout_seconds = _validate_timeout_seconds(timeout_seconds)

    def post_json(
        self,
        *,
        path: str,
        payload: dict[str, object],
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Send a JSON POST request and decode a JSON-object response.

        Args:
            path: Relative API path.
            payload: JSON-serializable payload.
            headers: Optional HTTP headers.

        Returns:
            dict[str, object]: Decoded JSON response object.

        Raises:
            ProviderClientError: If the request fails or the response is invalid.
        """
        request = Request(
            url=_join_url(self.base_url, path),
            data=json.dumps(payload).encode("utf-8"),
            headers={} if headers is None else dict(headers),
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except HTTPError as error:
            details = _decode_error_body(error)
            message = f"Provider request failed with status {error.code}"
            if details:
                message = f"{message}: {details}"
            raise ProviderClientError(message) from error
        except URLError as error:
            raise ProviderClientError(
                f"Provider request failed: {error.reason}"
            ) from error
        except OSError as error:
            raise ProviderClientError(f"Provider request failed: {error}") from error

        return _decode_json_object(body)


def _normalize_base_url(base_url: str) -> str:
    """Normalize and validate a provider base URL.

    Args:
        base_url: Base URL to normalize.

    Returns:
        str: Normalized base URL without a trailing slash.
    """
    return validate_non_empty_text(base_url).rstrip("/")


def _validate_timeout_seconds(timeout_seconds: float) -> float:
    """Validate a request timeout value.

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


def _join_url(base_url: str, path: str) -> str:
    """Join a base URL and relative path.

    Args:
        base_url: Base URL.
        path: Relative API path.

    Returns:
        str: Joined URL.
    """
    normalized_path = validate_non_empty_text(path)
    return f"{base_url}/{normalized_path.lstrip('/')}"


def _decode_json_object(body: bytes) -> dict[str, object]:
    """Decode a JSON-object response body.

    Args:
        body: Raw response bytes.

    Returns:
        dict[str, object]: Decoded JSON object.

    Raises:
        ProviderClientError: If the response is not valid JSON or not an object.
    """
    try:
        payload = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ProviderClientError("Provider response was not valid UTF-8.") from error
    except json.JSONDecodeError as error:
        raise ProviderClientError("Provider response was not valid JSON.") from error

    if not isinstance(payload, dict):
        raise ProviderClientError("Provider response must be a JSON object.")

    return payload


def _decode_error_body(error: HTTPError) -> str:
    """Read and normalize an HTTP error body.

    Args:
        error: HTTP error raised by the request layer.

    Returns:
        str: Decoded error details if available.
    """
    try:
        raw_body = error.read()
    except OSError:
        return ""

    try:
        return raw_body.decode("utf-8").strip()
    except UnicodeDecodeError:
        return ""
