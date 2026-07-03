from pathlib import Path

from app.common.utils import should_skip


def read_path(path: Path) -> str:
    try:
        content = path.read_text(errors="replace")
        return f'<file path="{path}">\n{content}\n</file>'
    except Exception as e:
        return f'<file path="{path}" error="{e}" />'


def collect_files(paths: list[Path], skip_patterns: list[str]) -> list[Path]:
    """Expand dirs recursively, deduplicate, apply skip filters."""
    seen: set[Path] = set()
    result: list[Path] = []

    for path in paths:
        if not path.exists():
            continue

        if path.is_file():
            if path not in seen and not should_skip(path, skip_patterns):
                seen.add(path)
                result.append(path)

        elif path.is_dir():
            for file in sorted(path.rglob("*")):
                if not file.is_file():
                    continue
                if file in seen:
                    continue
                # skip if any part of path matches patterns
                if any(
                    should_skip(p, skip_patterns) for p in [file] + list(file.parents)
                ):
                    continue
                seen.add(file)
                result.append(file)

    return result


def get_paths_context(paths: list[Path], skip_patterns: list[str]) -> str:
    files = collect_files(paths, skip_patterns)
    if not files:
        return "<paths></paths>"
    blocks = [read_path(f) for f in files]
    return "\n\n".join(blocks)
