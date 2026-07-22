from pathlib import Path

from app.common.utils import dedupe_nested, should_skip


# Bitta o'tishda ham tree satrlarini, ham (dirs, files) statistikani qaytaradi —
# ko'rsatilgan tree va statistika har doim bir-biriga mos bo'lishi uchun.
def _walk(
    root: Path,
    skip_patterns: list[str],
    prefix: str = "",
) -> tuple[list[str], int, int]:
    lines: list[str] = []
    dirs = 0
    files = 0

    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    except OSError:
        return lines, dirs, files

    entries = [e for e in entries if not should_skip(e, skip_patterns)]

    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if not entry.is_dir():
            files += 1
            continue

        dirs += 1
        # symlink papka ichiga kirilmaydi — rekursiya sikliga tushib qolmaslik uchun
        if entry.is_symlink():
            continue

        extension = "    " if last else "│   "
        sub_lines, sub_dirs, sub_files = _walk(entry, skip_patterns, prefix + extension)
        lines.extend(sub_lines)
        dirs += sub_dirs
        files += sub_files

    return lines, dirs, files


def _render_tree(root: Path, skip_patterns: list[str]) -> str:
    if not root.exists():
        return f'<file_tree path="{root}" error="not found" />'

    if root.is_file():
        body = root.name
        stats = "0 directories, 1 files"
    else:
        lines, dirs, files = _walk(root, skip_patterns)
        body = "\n".join(lines)
        stats = f"{dirs} directories, {files} files"

    content = f"{body}\n\n{stats}" if body else stats
    return f'<file_tree path="{root}">\n{content}\n</file_tree>'


# Ro'yxatdagi har bir path uchun alohida tree bloki.
# Boshqa pathning ichida joylashgan pathlar o'tkazib yuboriladi.
def get_file_trees(roots: list[Path], skip_patterns: list[str]) -> str:
    roots = dedupe_nested(roots)
    if not roots:
        return "<file_tree></file_tree>"
    return "\n\n".join(_render_tree(root, skip_patterns) for root in roots)
