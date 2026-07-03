import fnmatch
from pathlib import Path


def should_skip(path: Path, skip_patterns: list[str]) -> bool:
    name = path.name
    for pattern in skip_patterns:
        # "/." → hidden files/dirs (starts with dot)
        if pattern == "/.":
            if name.startswith("."):
                return True
        elif fnmatch.fnmatch(name, pattern):
            return True
    return False
