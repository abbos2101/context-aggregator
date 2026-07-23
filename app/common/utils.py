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


# Faqat aynan takrorlanadigan pathlarni olib tashlaydi, tartib saqlanadi.
def dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []

    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)

    return unique


# Ichma-ich (nested) pathlarni olib tashlaydi: agar path ro'yxatdagi
# boshqa pathning ichida bo'lsa — tashlab yuboriladi.
def drop_nested(paths: list[Path]) -> list[Path]:
    unique = dedupe(paths)
    roots = set(unique)
    return [p for p in unique if not any(parent in roots for parent in p.parents)]
