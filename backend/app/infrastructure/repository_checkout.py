import os
import stat
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar
from urllib.parse import urlparse

from git import Repo


def build_authenticated_url(repo_url: str, token: str | None) -> str:
    if not token:
        return repo_url
    parsed = urlparse(repo_url)
    return f"{parsed.scheme}://x-access-token:{token}@{parsed.netloc}{parsed.path}"


T = TypeVar("T")


def with_cloned_repository(repo_url: str, operation: Callable[[Path], T]) -> T:
    temp_dir = Path(tempfile.mkdtemp(prefix="devpulse_"))
    git_repo: Repo | None = None
    try:
        git_repo = Repo.clone_from(repo_url, str(temp_dir))
        return operation(temp_dir)
    finally:
        if git_repo is not None:
            git_repo.close()
        shutil.rmtree(temp_dir, onerror=_force_remove_readonly)


def _force_remove_readonly(func: Callable[..., object], path: str, exc_info: object) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        pass
