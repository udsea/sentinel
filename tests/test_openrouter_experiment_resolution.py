import json
from pathlib import Path

import pytest

from sentinel.agents import ModelAgent
from sentinel.agents.providers import (
    OpenAICompatibleTextClient,
    ProviderClientError,
)
from sentinel.experiments import (
    build_agent_from_spec,
    load_experiment_spec,
    run_experiment,
)

_EXPERIMENTS_ROOT = Path(__file__).parent / "fixtures" / "experiments"


class _FakeOpenRouterClient:
    """Minimal fake OpenRouter client for no-network experiment tests."""

    @property
    def name(self) -> str:
        """Return a stable client name."""
        return "fake_openrouter_client"

    def generate(self, prompt: str) -> str:
        """Return a deterministic safe response for smoke tests."""
        return f"Plan safely: {prompt.splitlines()[0]}"


def test_build_agent_from_openrouter_spec_succeeds_with_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that OpenRouter model-agent construction succeeds with an API key."""
    spec = load_experiment_spec(_EXPERIMENTS_ROOT / "openrouter_benign_smoke.yaml")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")

    agent = build_agent_from_spec(spec.agent)

    assert isinstance(agent, ModelAgent)
    assert (
        agent.name == "model_agent:openai_compatible:meta-llama/llama-3.2-3b-instruct"
    )


def test_build_agent_from_openrouter_spec_fails_without_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that missing OpenRouter API keys fail with a clear error."""
    spec = load_experiment_spec(_EXPERIMENTS_ROOT / "openrouter_benign_smoke.yaml")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(
        ProviderClientError,
        match="Missing required API key environment variable: OPENROUTER_API_KEY",
    ):
        build_agent_from_spec(spec.agent)


def test_run_experiment_writes_openrouter_smoke_artifacts_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the OpenRouter smoke experiment writes artifacts without API calls."""
    spec = load_experiment_spec(_EXPERIMENTS_ROOT / "openrouter_benign_smoke.yaml")
    spec.output_dir = str(tmp_path / "openrouter_benign_smoke")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")

    def fake_for_openrouter_from_env(
        cls: type[OpenAICompatibleTextClient],
        *,
        model: str,
        api_key_env: str = "OPENROUTER_API_KEY",
        site_url_env: str = "OPENROUTER_SITE_URL",
        site_name_env: str = "OPENROUTER_SITE_NAME",
        system_prompt: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> _FakeOpenRouterClient:
        del cls
        del model
        del api_key_env
        del site_url_env
        del site_name_env
        del system_prompt
        del timeout_seconds
        return _FakeOpenRouterClient()

    monkeypatch.setattr(
        OpenAICompatibleTextClient,
        "for_openrouter_from_env",
        classmethod(fake_for_openrouter_from_env),
    )

    output_dir = run_experiment(spec)
    summary = json.loads(
        (output_dir / "batch_summary.json").read_text(encoding="utf-8")
    )

    assert output_dir == tmp_path / "openrouter_benign_smoke"
    assert output_dir.exists()
    assert (output_dir / "batch_summary.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "experiment_spec.json").exists()
    assert (output_dir / "fix_pagination_v1.json").exists()
    assert (output_dir / "fix_blank_password_v1.json").exists()
    assert summary["total_runs"] == 2
