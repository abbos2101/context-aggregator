import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

import yaml
from pydantic import BaseModel, field_validator, model_validator


class DatabaseConfig(BaseModel):
    enabled: bool = False
    url: Optional[str] = None
    skip_tables: list[str] = []

    @field_validator("url", mode="before")
    @classmethod
    def normalize_db_url(cls, v):
        if not v:
            return v

        v = str(v).strip()

        # SQLite: prefiks yo'q → fayl path
        if not v.startswith(("sqlite", "postgresql", "postgres", "jdbc")):
            path = Path(v).expanduser().resolve()
            return f"sqlite:///{path}"

        # SQLite: prefiks bor, path normalize
        if v.startswith("sqlite"):
            parsed = urlparse(v)
            path = Path(parsed.path).expanduser().resolve()
            return f"sqlite:///{path}"

        # JDBC → SQLAlchemy
        if v.startswith("jdbc:postgresql"):
            v = v.replace("jdbc:postgresql", "postgresql", 1)

        # PostgreSQL: host fallback + query params tozalash
        if v.startswith(("postgresql", "postgres")):
            parsed = urlparse(v)

            import socket

            host = parsed.hostname or "localhost"
            try:
                socket.getaddrinfo(host, None)
            except socket.gaierror:
                host = "localhost"

            port = parsed.port or 5432
            userinfo = ""
            if parsed.username:
                userinfo = parsed.username
                if parsed.password:
                    userinfo += f":{parsed.password}"
                userinfo += "@"

            new_netloc = f"{userinfo}{host}:{port}"

            allowed_params = {"sslmode", "connect_timeout", "application_name"}
            filtered = {
                k: vals[0]
                for k, vals in parse_qs(parsed.query).items()
                if k in allowed_params
            }

            clean = urlunparse(
                parsed._replace(netloc=new_netloc, query=urlencode(filtered))
            )
            return clean.replace("postgres://", "postgresql://", 1)

        return v

    @model_validator(mode="after")
    def url_required_if_enabled(self):
        if self.enabled and not self.url:
            raise ValueError("database.url required when enabled=true")
        return self


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
    database: DatabaseConfig = DatabaseConfig()
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
