import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class AppConfig(BaseModel):
    file_tree: list[Path] = []
    skip_files: list[str] = []
    paths: list[Path] = []

    @field_validator("file_tree", "paths", mode="before")
    @classmethod
    def expand_paths(cls, v):
        if not v:
            return []
        return [Path(p).expanduser().resolve() for p in v]


def load_config(path: str | Path = "context.yaml") -> AppConfig:
    if getattr(sys, "frozen", False):
        config_path = Path(sys.executable).parent / "context.yaml"
    else:
        config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text())
    return AppConfig.model_validate(raw)
