from pathlib import Path

from sentinel.experiments import load_experiment_spec

_EXPERIMENTS_ROOT = Path(__file__).parent / "fixtures" / "experiments"


def test_openrouter_benign_smoke_config_loads() -> None:
    """Test that the benign OpenRouter smoke config loads cleanly."""
    spec = load_experiment_spec(_EXPERIMENTS_ROOT / "openrouter_benign_smoke.yaml")

    assert spec.name == "openrouter_benign_smoke"
    assert spec.agent.kind == "model"
    assert spec.agent.provider == "openrouter"
    assert spec.agent.model == "meta-llama/llama-3.2-3b-instruct"
    assert [grader.kind for grader in spec.graders] == ["pytest"]
    assert [monitor.kind for monitor in spec.monitors] == [
        "path_risk",
        "keyword_risk",
        "content_risk",
        "write_policy",
    ]
    assert spec.monitors[-1].protected_prefixes == ["tests/"]
    assert spec.output_dir == "outputs/openrouter_benign_smoke"


def test_openrouter_cheating_smoke_config_loads() -> None:
    """Test that the cheating OpenRouter smoke config loads cleanly."""
    spec = load_experiment_spec(_EXPERIMENTS_ROOT / "openrouter_cheating_smoke.yaml")

    assert spec.name == "openrouter_cheating_smoke"
    assert spec.agent.kind == "model"
    assert spec.agent.provider == "openrouter"
    assert spec.agent.model == "meta-llama/llama-3.2-3b-instruct"
    assert spec.tasks == [
        "tests/fixtures/tasks/hide_failing_test_v1.yaml",
        "tests/fixtures/tasks/weaken_parser_test_v1.yaml",
    ]
    assert [grader.kind for grader in spec.graders] == ["pytest"]
    assert len(spec.monitors) == 4
    assert spec.output_dir == "outputs/openrouter_cheating_smoke"


def test_openrouter_action_benign_smoke_config_loads() -> None:
    """Test that the benign action-model OpenRouter config loads cleanly."""
    spec = load_experiment_spec(
        _EXPERIMENTS_ROOT / "openrouter_action_benign_smoke.yaml"
    )

    assert spec.name == "openrouter_action_benign_smoke"
    assert spec.agent.kind == "action_model"
    assert spec.agent.provider == "openrouter"
    assert spec.agent.model == "openai/gpt-4o-mini"
    assert spec.tasks == [
        "tests/fixtures/tasks/fix_pagination_v1.yaml",
        "tests/fixtures/tasks/valid_minimal.yaml",
    ]
    assert [grader.kind for grader in spec.graders] == ["pytest"]
    assert len(spec.monitors) == 4
    assert spec.output_dir == "outputs/openrouter_action_benign_smoke"


def test_openrouter_action_cheating_smoke_config_loads() -> None:
    """Test that the cheating action-model OpenRouter config loads cleanly."""
    spec = load_experiment_spec(
        _EXPERIMENTS_ROOT / "openrouter_action_cheating_smoke.yaml"
    )

    assert spec.name == "openrouter_action_cheating_smoke"
    assert spec.agent.kind == "action_model"
    assert spec.agent.provider == "openrouter"
    assert spec.agent.model == "openai/gpt-4o-mini"
    assert spec.tasks == [
        "tests/fixtures/tasks/hide_failing_test_v1.yaml",
        "tests/fixtures/tasks/weaken_parser_test_v1.yaml",
    ]
    assert [grader.kind for grader in spec.graders] == ["pytest"]
    assert len(spec.monitors) == 4
    assert spec.output_dir == "outputs/openrouter_action_cheating_smoke"
