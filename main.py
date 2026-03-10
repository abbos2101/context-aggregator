import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import load_config
from app.database import get_db_context
from app.file_tree import get_file_tree
from app.paths import get_paths_context

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
)

@app.get("/")
async def health():
    return {"message": "Context Aggregator"}


@app.get("/context", response_class=PlainTextResponse)
async def get_context():
    config = load_config()
    parts: list[str] = []

    if config.database.enabled:
        parts.append(get_db_context(config.database.url, config.database.skip_tables))

    if config.file_tree.enabled:
        parts.append(get_file_tree(config.file_tree.root, config.skip_files))

    if config.paths:
        parts.append(get_paths_context(config.paths, config.skip_files))

    if not parts:
        return "nothing configured"

    return "\n\n".join(parts)


@app.get("/context/files", response_class=PlainTextResponse)
async def get_files():
    config = load_config()
    if not config.file_tree.enabled:
        return "file_tree disabled"

    return get_file_tree(config.file_tree.root, config.skip_files)


@app.get("/context/paths", response_class=PlainTextResponse)
async def get_paths():
    config = load_config()
    if not config.paths:
        return "paths not configured"
    return get_paths_context(config.paths, config.skip_files)


@app.get("/context/db", response_class=PlainTextResponse)
async def get_db():
    config = load_config()
    if not config.database.enabled:
        return "database disabled"
    return get_db_context(config.database.url, config.database.skip_tables)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 2101
    uvicorn.run(app, host="0.0.0.0", port=port)
