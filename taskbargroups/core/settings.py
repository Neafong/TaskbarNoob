"""ตั้งค่าระดับแอป เก็บใน config/settings.json (portable)."""

from __future__ import annotations

import json
from pathlib import Path

from .paths import default_config_dir

SETTINGS_FILE = "settings.json"
DEFAULT_THEME = "auto"
DEFAULT_LANGUAGE = "th"
DEFAULT_DONATE_URL = "https://ko-fi.com/neafong"

VALID_THEMES = ("auto", "light", "dark")


class Settings:
    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = (
            Path(config_dir) if config_dir is not None else default_config_dir()
        )
        self.path = self.config_dir / SETTINGS_FILE

    def _load(self) -> dict:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def get(self, key: str, default=None):
        return self._load().get(key, default)

    def set(self, key: str, value) -> None:
        data = self._load()
        data[key] = value
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            return

    def get_theme(self) -> str:
        theme = self.get("theme", DEFAULT_THEME)
        return theme if theme in VALID_THEMES else DEFAULT_THEME

    def set_theme(self, theme: str) -> None:
        if theme in VALID_THEMES:
            self.set("theme", theme)

    def get_language(self) -> str:
        language = self.get("language", DEFAULT_LANGUAGE)
        return language if isinstance(language, str) and language else DEFAULT_LANGUAGE

    def set_language(self, language: str) -> None:
        if isinstance(language, str) and language.strip():
            self.set("language", language.strip().lower())

    def get_donate_url(self) -> str:
        url = self.get("donate_url", DEFAULT_DONATE_URL)
        return url.strip() if isinstance(url, str) else ""

    def set_donate_url(self, url: str) -> None:
        if isinstance(url, str):
            self.set("donate_url", url.strip())