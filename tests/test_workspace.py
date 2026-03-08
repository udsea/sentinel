from pathlib import Path

import pytest

from sentinel.sandbox import (
    create_workspace_from_fixture,
    fixture_workspace,
    get_default_fixtures_root,
    resolve_fixture_repo,
)


def list_relative_files(root: Path) -> list[str]:
    """List all files beneath a directory as relative POSIX paths.

    Args:
        root: Directory to scan.

    Returns:
        list[str]: Sorted relative file paths.
    """
    return sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    )


def test_resolve_fixture_repo_returns_existing_fixture_path() -> None:
    """Test that a known fixture resolves to an existing directory."""
    fixture_path = resolve_fixture_repo("todo_api")
    expected_path = get_default_fixtures_root() / "todo_api"

    assert fixture_path == expected_path
    assert fixture_path.is_absolute()
    assert fixture_path.is_dir()


def test_resolve_fixture_repo_missing_fixture_raises_file_not_found(
    tmp_path: Path,
) -> None:
    """Test that resolving a missing fixture raises FileNotFoundError.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    with pytest.raises(
        FileNotFoundError,
        match="Fixture repo 'missing_repo' not found",
    ):
        resolve_fixture_repo("missing_repo", fixtures_root=tmp_path)


def test_resolve_fixture_repo_non_directory_raises_not_a_directory(
    tmp_path: Path,
) -> None:
    """Test that a non-directory fixture path raises NotADirectoryError.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    file_path = tmp_path / "todo_api"
    file_path.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(
        NotADirectoryError,
        match="Fixture path exists but is not a directory",
    ):
        resolve_fixture_repo("todo_api", fixtures_root=tmp_path)


@pytest.mark.parametrize("invalid_name", ["TodoApi", "123repo", "repo-name", "", " "])
def test_resolve_fixture_repo_invalid_name_raises_value_error(
    invalid_name: str,
) -> None:
    """Test that invalid fixture names are rejected.

    Args:
        invalid_name: Invalid fixture repository name.

    Returns:
        None.
    """
    with pytest.raises(ValueError, match="Fixture repo name must"):
        resolve_fixture_repo(invalid_name)


def test_create_workspace_from_fixture_copies_fixture_contents(
    tmp_path: Path,
) -> None:
    """Test that workspace creation copies all fixture files.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    fixture_path = resolve_fixture_repo("todo_api")
    workspace_path = create_workspace_from_fixture(
        "todo_api",
        workspace_root=tmp_path,
    )

    assert workspace_path.is_dir()
    assert list_relative_files(workspace_path) == list_relative_files(fixture_path)
    assert (workspace_path / "tests" / "test_app.py").read_text(encoding="utf-8") == (
        fixture_path / "tests" / "test_app.py"
    ).read_text(encoding="utf-8")


def test_repeated_workspace_creation_returns_unique_directories(
    tmp_path: Path,
) -> None:
    """Test that repeated workspace creation returns unique directories.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    workspace_one = create_workspace_from_fixture(
        "auth_module",
        workspace_root=tmp_path,
    )
    workspace_two = create_workspace_from_fixture(
        "auth_module",
        workspace_root=tmp_path,
    )

    assert workspace_one != workspace_two
    assert workspace_one.name.startswith("sentinel_auth_module_")
    assert workspace_two.name.startswith("sentinel_auth_module_")


def test_workspace_modifications_do_not_mutate_source_fixture(
    tmp_path: Path,
) -> None:
    """Test that editing a workspace does not change the source fixture.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    fixture_path = resolve_fixture_repo("auth_module")
    source_file = fixture_path / "auth.py"
    original_source = source_file.read_text(encoding="utf-8")

    workspace_path = create_workspace_from_fixture(
        "auth_module",
        workspace_root=tmp_path,
    )
    workspace_file = workspace_path / "auth.py"
    workspace_file.write_text(
        "def authorize(user_role: str) -> bool:\n    return False\n",
        encoding="utf-8",
    )

    assert workspace_file.read_text(encoding="utf-8") != original_source
    assert source_file.read_text(encoding="utf-8") == original_source


def test_fixture_workspace_cleans_up_after_exit(tmp_path: Path) -> None:
    """Test that the workspace context manager removes the workspace on exit.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    workspace_path: Path | None = None

    with fixture_workspace("todo_api", workspace_root=tmp_path) as workspace:
        workspace_path = workspace
        assert workspace.exists()
        assert (workspace / "app.py").exists()

    assert workspace_path is not None
    assert not workspace_path.exists()
