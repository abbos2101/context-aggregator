import sys
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, field_validator, model_validator


class FileTreeConfig(BaseModel):
    enabled: bool = False
    root: Optional[Path] = None

    @model_validator(mode="after")
    def root_required_if_enabled(self):
        if self.enabled and not self.root:
            raise ValueError("file_tree.root required when enabled=true")
        return self

    @field_validator("root", mode="before")
    @classmethod
    def expand_root(cls, v):
        if v:
            return Path(v).expanduser().resolve()
        return v


class AppConfig(BaseModel):
    file_tree: FileTreeConfig = FileTreeConfig()
    skip_files: list[str] = []
    paths: list[Path] = []

    @field_validator("paths", mode="before")
    @classmethod
    def expand_paths(cls, v):
        return [Path(p).expanduser().resolve() for p in v]


def load_config(path: str | Path = "context.yaml") -> AppConfig:
    if getattr(sys, "frozen", False):
        config_path = Path(sys.executable).parent / "context.yaml"
    else:
        config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text())
    return AppConfig.model_validate(raw)
