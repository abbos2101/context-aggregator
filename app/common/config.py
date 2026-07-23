import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class AppConfig(BaseModel):
    file_tree: list[Path] = []
    file_tree_level: int = -1
    skip_files: list[str] = []
    paths: list[Path] = []

    @field_validator("file_tree", "paths", mode="before")
    @classmethod
    def expand_paths(cls, v):
        if not v:
            return []
        return [Path(p).expanduser().resolve() for p in v]

    @field_validator("file_tree_level", mode="before")
    @classmethod
    def validate_level(cls, v):
        if v is None:
            return -1
        level = int(v)
        if level == 0 or level < -1:
            raise ValueError("file_tree_level must be -1 (unlimited) or a positive int")
        return level


def load_config(path: str | Path = "context.yaml") -> AppConfig:
    if getattr(sys, "frozen", False):
        config_path = Path(sys.executable).parent / "context.yaml"
    else:
        config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text())
    return AppConfig.model_validate(raw)
