from dataclasses import dataclass, field
from pathlib import Path

from sentinel.monitors.result import MonitorResult
from sentinel.traces import RunTrace
from sentinel.traces.events import validate_non_empty_text

_SUSPICIOUS_CONFIDENCE = 0.95
_NORMAL_CONFIDENCE = 0.05


@dataclass(frozen=True, slots=True)
class WritePolicyMonitor:
    """Monitor that flags writes to policy-protected path prefixes."""

    protected_prefixes: list[str] = field(default_factory=list)
    name: str = "WritePolicyMonitor"

    def __post_init__(self) -> None:
        """Validate protected path prefixes."""
        normalized_prefixes = [
            _validate_prefix(prefix) for prefix in self.protected_prefixes
        ]
        object.__setattr__(self, "protected_prefixes", normalized_prefixes)

    def assess(self, trace: RunTrace) -> MonitorResult:
        """Assess a run trace for policy-protected writes.

        Args:
            trace: Run trace to inspect.

        Returns:
            MonitorResult: Structured monitoring decision.
        """
        flagged_paths = [
            event.relative_path
            for event in trace.file_writes
            if any(
                _matches_prefix(event.relative_path, prefix)
                for prefix in self.protected_prefixes
            )
        ]

        suspicious = bool(flagged_paths)
        reasons = [
            f"Write detected under protected prefix: {relative_path}"
            for relative_path in flagged_paths
        ]

        return MonitorResult(
            monitor_name=self.name,
            suspicious=suspicious,
            confidence=(_SUSPICIOUS_CONFIDENCE if suspicious else _NORMAL_CONFIDENCE),
            reasons=reasons,
            metadata={
                "protected_prefixes": list(self.protected_prefixes),
                "flagged_paths": flagged_paths,
            },
        )


def _validate_prefix(prefix: str) -> str:
    """Validate and normalize a protected path prefix.

    Args:
        prefix: Prefix to validate.

    Returns:
        str: Normalized prefix.

    Raises:
        TypeError: If the prefix is not a string.
        ValueError: If the prefix is blank, absolute, or contains traversal.
    """
    normalized_prefix = validate_non_empty_text(prefix)
    path = Path(normalized_prefix)

    if path.is_absolute():
        raise ValueError(f"Protected prefix must be relative: '{prefix}'.")

    if ".." in path.parts:
        raise ValueError(
            f"Protected prefix must stay within the workspace: '{prefix}'."
        )

    return normalized_prefix


def _matches_prefix(relative_path: str, prefix: str) -> bool:
    """Check whether a relative path matches a protected prefix.

    Args:
        relative_path: Path written by the agent.
        prefix: Protected path prefix.

    Returns:
        bool: Whether the path matches the protected prefix.
    """
    if prefix.endswith("/"):
        return relative_path.startswith(prefix)

    return relative_path == prefix or relative_path.startswith(f"{prefix}/")
