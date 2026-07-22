import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi import File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.common.config import load_config
from app.common.tokens import count_tokens
from app.sources.clipboard import ClipboardError, copy_to_clipboard
from app.sources.file_tree import get_file_tree
from app.sources.paths import get_paths_context

EXAMPLE_CONFIG = """\
file_tree:
  enabled: true
  root: /Users/yourname/PycharmProjects/my-project

paths: [
  /Users/yourname/PycharmProjects/my-project,
]

skip_files: [
  ".",
  "..",
  ".android",
  ".claude",
  ".DS_Store",
  ".dart_tool",
  ".env.dev.json",
  ".env.local",
  ".env.prod.json",
  ".flutter-plugins-dependencies",
  ".git",
  ".idea",
  ".ios",
  ".metadata",
  ".pytest_cache",
  ".run",
  ".symlinks",
  ".venv",
  ".vscode",
  "*.config.dart",
  "*.db",
  "*.env",
  "*.freezed.dart",
  "*.g.dart",
  "*.gif",
  "*.htm",
  "*.html",
  "*.jpeg",
  "*.jpg",
  "*.lock",
  "*.log",
  "*.png",
  "*.pyc",
  "*.spec",
  "__init__.py",
  "__pycache__",
  "build",
  "fonts",
  "firebase_options.dart",
  "gradle",
  "Pods",
  "dist",
  "test",
]
"""


def get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "context.yaml"
    return Path("context.yaml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = get_config_path()
    if not config_path.exists():
        config_path.write_text(EXAMPLE_CONFIG)
        print(
            f"context.yaml not found — example config created at {config_path}. "
            "Please edit it and restart."
        )
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
)


@app.get("/")
async def health():
    return {"message": "Context Aggregator"}


@app.get("/context")
async def get_context():
    config = load_config(get_config_path())
    parts: list[str] = []

    if config.file_tree.enabled:
        parts.append(get_file_tree(config.file_tree.root, config.skip_files))

    if config.paths:
        parts.append(get_paths_context(config.paths, config.skip_files))

    if not parts:
        content = "nothing configured"
    else:
        content = "\n\n".join(parts)

    return JSONResponse(
        {
            "tokens": count_tokens(content),
            "characters": len(content),
            "content": content,
        }
    )


@app.get("/context/files", response_class=PlainTextResponse)
async def get_files():
    config = load_config(get_config_path())
    if not config.file_tree.enabled:
        return "file_tree disabled"
    return get_file_tree(config.file_tree.root, config.skip_files)


@app.get("/context/paths", response_class=PlainTextResponse)
async def get_paths():
    config = load_config(get_config_path())
    if not config.paths:
        return "paths not configured"
    return get_paths_context(config.paths, config.skip_files)


@app.get("/context/open")
async def context_open():
    config_path = get_config_path().resolve()
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"{config_path} topilmadi")
    try:
        subprocess.run(["open", str(config_path)], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"open failed: {e}")
    return {"opened": str(config_path)}


@app.post("/context/copy_clipboard")
async def copy_clipboard(
    ui_data: str | None = Form(None),
    ui_image: UploadFile | None = File(None),
):
    if ui_data is None and ui_image is None:
        raise HTTPException(
            status_code=400, detail="ui_data yoki ui_image talab qilinadi"
        )

    image_bytes: bytes | None = None
    image_type: str | None = None
    if ui_image is not None:
        image_bytes = await ui_image.read()
        image_type = ui_image.content_type

    try:
        copied = copy_to_clipboard(ui_data, image_bytes, image_type)
    except ClipboardError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"copied": copied}


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 2101
    uvicorn.run(app, host="0.0.0.0", port=port)
