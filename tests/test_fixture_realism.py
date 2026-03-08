from pathlib import Path
from typing import cast

import pytest

from sentinel.sandbox import resolve_fixture_repo
from sentinel.tasks.loader import load_task_specs

_FIXTURE_NAMES = [
    "todo_api",
    "auth_module",
    "csv_cleaner",
    "config_parser",
]


def _source_files(repo_path: Path) -> list[Path]:
    """Return top-level source files for a fixture repo.

    Args:
        repo_path: Fixture repository path.

    Returns:
        list[Path]: Top-level Python source files.
    """
    return sorted(path for path in repo_path.glob("*.py") if path.is_file())


def _test_files(repo_path: Path) -> list[Path]:
    """Return test files for a fixture repo.

    Args:
        repo_path: Fixture repository path.

    Returns:
        list[Path]: Python test files beneath the fixture's tests directory.
    """
    tests_path = repo_path / "tests"
    return sorted(path for path in tests_path.glob("test_*.py") if path.is_file())


@pytest.mark.parametrize("fixture_name", _FIXTURE_NAMES)
def test_fixture_repo_has_multiple_source_files_and_tests(fixture_name: str) -> None:
    """Test that each realistic fixture repo keeps a believable project shape."""
    repo_path = resolve_fixture_repo(fixture_name)
    source_files = _source_files(repo_path)
    test_files = _test_files(repo_path)

    assert repo_path.is_dir()
    assert source_files
    assert 2 <= len(source_files) <= 5
    assert (repo_path / "tests").is_dir()
    assert len(test_files) >= 2


def test_task_catalog_covers_realistic_fixtures_and_tracks() -> None:
    """Test that the fixture task catalog covers the realistic fixture set."""
    tasks_root = Path(__file__).parent / "fixtures" / "tasks"
    task_paths = sorted(tasks_root.glob("*.yaml"))
    loader_paths: list[str | Path] = list(task_paths)
    tasks = load_task_specs(loader_paths)
    task_repo_fixtures = {task.repo_fixture for task in tasks}
    task_tracks = {cast(str, task.track) for task in tasks}

    assert len(tasks) >= 8
    assert task_repo_fixtures.issuperset(_FIXTURE_NAMES)
    assert "benign" in task_tracks
    assert {"temptation", "deception"} & task_tracks
