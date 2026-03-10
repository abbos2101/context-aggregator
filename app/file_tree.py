from pathlib import Path

from app.utils import should_skip


def build_tree(
    root: Path,
    skip_patterns: list[str],
    prefix: str = "",
    is_last: bool = True,
) -> list[str]:
    lines = []

    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return lines

    entries = [e for e in entries if not should_skip(e, skip_patterns)]

    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if last else "│   "
            lines.extend(build_tree(entry, skip_patterns, prefix + extension, last))

    return lines


def get_file_tree(root: Path, skip_patterns: list[str]) -> str:
    lines = [str(root)]
    lines.extend(build_tree(root, skip_patterns))

    # stats
    all_entries = list(root.rglob("*"))
    dirs = [
        e
        for e in all_entries
        if e.is_dir()
        and not any(should_skip(p, skip_patterns) for p in [e] + list(e.parents))
    ]
    files = [
        e
        for e in all_entries
        if e.is_file()
        and not any(should_skip(p, skip_patterns) for p in [e] + list(e.parents))
    ]

    lines.append(f"\n{len(dirs)} directories, {len(files)} files")
    return "\n".join(lines)
