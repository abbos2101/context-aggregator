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


# Takror va ichma-ich (nested) pathlarni olib tashlaydi.
# Agar path ro'yxatdagi boshqa pathning ichida bo'lsa — tashlab yuboriladi.
def dedupe_nested(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)

    return [p for p in unique if not any(parent in seen for parent in p.parents)]
