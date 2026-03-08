import re
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def get_default_fixtures_root() -> Path:
    """Return the default repository fixture root.

    Returns:
        Path: Absolute path to the default fixture repository root.
    """
    return (
        Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "repos"
    ).resolve()


def resolve_fixture_repo(name: str, fixtures_root: Path | None = None) -> Path:
    """Resolve a fixture repository name to an absolute path.

    Args:
        name: Fixture repository name.
        fixtures_root: Optional override for the fixture repository root.

    Returns:
        Path: Absolute path to the fixture repository directory.

    Raises:
        ValueError: If the fixture name is not a valid identifier.
        FileNotFoundError: If the fixture repository does not exist.
        NotADirectoryError: If the resolved fixture path exists but is not a
            directory.
    """
    fixture_name = _validate_fixture_name(name)
    root = _resolve_root(fixtures_root or get_default_fixtures_root())
    fixture_path = (root / fixture_name).resolve()

    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture repo '{fixture_name}' not found at '{fixture_path}'."
        )

    if not fixture_path.is_dir():
        raise NotADirectoryError(
            f"Fixture path exists but is not a directory: '{fixture_path}'."
        )

    return fixture_path


def create_workspace_from_fixture(
    fixture_name: str,
    fixtures_root: Path | None = None,
    workspace_root: Path | None = None,
) -> Path:
    """Copy a fixture repository into a unique temporary workspace.

    Args:
        fixture_name: Fixture repository name.
        fixtures_root: Optional override for the fixture repository root.
        workspace_root: Optional parent directory for temporary workspaces.

    Returns:
        Path: Absolute path to the created workspace directory.

    Raises:
        ValueError: If the fixture name is not a valid identifier.
        FileNotFoundError: If the fixture repository does not exist.
        NotADirectoryError: If the fixture repository or workspace root is not
            a directory.
    """
    source_path = resolve_fixture_repo(fixture_name, fixtures_root=fixtures_root)
    temp_root = _prepare_workspace_root(workspace_root)
    workspace_path = Path(
        tempfile.mkdtemp(
            prefix=f"sentinel_{fixture_name}_",
            dir=str(temp_root) if temp_root is not None else None,
        )
    ).resolve()

    shutil.copytree(source_path, workspace_path, dirs_exist_ok=True)
    return workspace_path


@contextmanager
def fixture_workspace(
    fixture_name: str,
    fixtures_root: Path | None = None,
    workspace_root: Path | None = None,
) -> Iterator[Path]:
    """Yield a temporary workspace for a fixture repository and clean it up.

    Args:
        fixture_name: Fixture repository name.
        fixtures_root: Optional override for the fixture repository root.
        workspace_root: Optional parent directory for temporary workspaces.

    Yields:
        Iterator[Path]: Path to the temporary workspace directory.
    """
    workspace_path = create_workspace_from_fixture(
        fixture_name=fixture_name,
        fixtures_root=fixtures_root,
        workspace_root=workspace_root,
    )

    try:
        yield workspace_path
    finally:
        if workspace_path.exists():
            shutil.rmtree(workspace_path)


def _validate_fixture_name(name: str) -> str:
    """Validate and normalize a fixture repository name.

    Args:
        name: Fixture repository name to validate.

    Returns:
        str: Normalized fixture name.

    Raises:
        TypeError: If the provided name is not a string.
        ValueError: If the provided name does not match the identifier pattern.
    """
    if not isinstance(name, str):
        raise TypeError("Fixture repo name must be a string.")

    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Fixture repo name must not be blank.")

    if not _IDENTIFIER_RE.fullmatch(normalized_name):
        raise ValueError(
            "Fixture repo name must be lowercase, start with a letter, and "
            "contain only letters, digits, and underscores."
        )

    return normalized_name


def _resolve_root(root: Path) -> Path:
    """Resolve a root path to an absolute filesystem path.

    Args:
        root: Root path to resolve.

    Returns:
        Path: Absolute root path.
    """
    return Path(root).resolve()


def _prepare_workspace_root(workspace_root: Path | None) -> Path | None:
    """Resolve and create the optional workspace root.

    Args:
        workspace_root: Optional parent directory for temporary workspaces.

    Returns:
        Path | None: Absolute workspace root if provided, otherwise `None`.

    Raises:
        NotADirectoryError: If the workspace root exists but is not a
            directory.
    """
    if workspace_root is None:
        return None

    resolved_root = _resolve_root(workspace_root)
    if resolved_root.exists() and not resolved_root.is_dir():
        raise NotADirectoryError(
            f"Workspace root exists but is not a directory: '{resolved_root}'."
        )

    resolved_root.mkdir(parents=True, exist_ok=True)
    return resolved_root
