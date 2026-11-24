"""i18n: ภาษาไทย (ค่าเริ่มต้น) + อังกฤษ + ภาษาของผู้ใช้เองผ่าน config/lang/<lang>.json.

- ภาษาในตัว: TH / EN (อยู่ในโค้ดนี้)
- ผู้ใช้เพิ่มภาษาเองได้โดยวางไฟล์ JSON ไว้ใน `<config>/lang/<code>.json`
- key เดียวกันทั้งหมด → ภาษาไทยคือภาษาแม่ (fallback ของทุกภาษา)
"""

from __future__ import annotations

import json
from pathlib import Path

from ..paths import app_dir, bundled_assets_dir, default_config_dir

DEFAULT_LANGUAGE = "th"
LANG_DIR_NAME = "lang"

from .en import EN
from .th import TH


def bundled_lang_dir() -> Path | None:
    """โฟลเดอร์ไฟล์ภาษาที่แพ็กติดมากับแอป (bundle หรือ `packaging/lang/` ตอนรันจากซอร์ส)."""
    bundled = bundled_assets_dir()
    if bundled is not None:
        candidate = bundled / LANG_DIR_NAME
        if candidate.is_dir():
            return candidate
    source_dir = app_dir() / "packaging" / LANG_DIR_NAME
    if source_dir.is_dir():
        return source_dir
    return None


def _find_lang_file(directory: Path, code: str) -> Path | None:
    """หาไฟล์ `<code >.json` ในโฟลเดอร์ (ลองตรงตัวก่อน แล้ว fallback แบบไม่สนตัวพิมพ์ใหญ่/เล็ก)."""
    direct = directory / f"{code}.json"
    if direct.is_file():
        return direct
    if not directory.is_dir():
        return None
    target = code.casefold()
    for path in directory.glob("*.json"):
        if path.stem.casefold() == target:
            return path
    return None


def _read_lang_json(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if isinstance(k, str) and isinstance(v, str)}


class I18n:
    def __init__(
        self,
        language: str | None = None,
        config_dir: str | Path | None = None,
    ) -> None:
        self._language = language or DEFAULT_LANGUAGE
        self._config_dir = (
            Path(config_dir) if config_dir is not None else default_config_dir()
        )
        self._data = self._load()

    @property
    def language(self) -> str:
        return self._language

    def _load(self) -> dict:
        base = dict(TH)
        if self._language.casefold() == "en":
            base.update(EN)
        bundled = bundled_lang_dir()
        if bundled is not None:
            bundled_file = _find_lang_file(bundled, self._language)
            if bundled_file is not None:
                base.update(_read_lang_json(bundled_file))
        overlay = _find_lang_file(self.lang_dir(), self._language)
        if overlay is not None:
            base.update(_read_lang_json(overlay))
        return base

    def lang_dir(self) -> Path:
        return self._config_dir / LANG_DIR_NAME

    def text(self, key: str, **kwargs) -> str:
        value = self._data.get(key, key)
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return value
        return value


_active: I18n | None = None


def tr(key: str, **kwargs) -> str:
    """สตริงปัจจุบันของ key (ภาษาไทยเป็นค่าพื้นฐาน ถ้ายังไม่เรียก setup)."""
    i18n = _active or I18n(DEFAULT_LANGUAGE)
    return i18n.text(key, **kwargs)


def setup(language: str | None = None, config_dir: str | Path | None = None) -> I18n:
    global _active
    _active = I18n(language, config_dir)
    return _active


def available_languages(config_dir: str | Path | None = None) -> list[tuple[str, str]]:
    """รายการภาษา [(code, ชื่อที่แสดง), ...] — ไทย/อังกฤษ + ภาษาในตัว + ไฟล์ใน config/lang.

    ไฟล์ภาษาเพิ่มเติมสามารถฝังชื่อที่แสดงได้ด้วย key พิเศษ `_lang_name`
    เช่น {"_lang_name": "日本語", ...} → dropdown โชว์ "日本語"
    """
    result: list[tuple[str, str]] = [("th", "ไทย"), ("en", "English")]
    seen = {"th", "en"}
    # โหลดไฟล์ภาษาที่แพ็กติดมากับแอปก่อน แล้วค่อยเติม/ทับด้วย config/lang ของผู้ใช้
    bundled = bundled_lang_dir()
    if bundled is not None:
        for path in sorted(bundled.glob("*.json")):
            code = path.stem
            if code not in seen:
                result.append((code, _lang_display_name(path, code)))
                seen.add(code)
    user_lang_dir = I18n(config_dir=config_dir).lang_dir()
    if user_lang_dir.is_dir():
        for path in sorted(user_lang_dir.glob("*.json")):
            code = path.stem
            if code not in seen:
                result.append((code, _lang_display_name(path, code)))
                seen.add(code)
    return result


def _lang_display_name(path: Path, fallback: str) -> str:
    """อ่านชื่อแสดงจาก key `_lang_name` ในไฟล์ภาษา (ถ้ามี) ไม่งั้นใช้ code."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    name = data.get("_lang_name") if isinstance(data, dict) else None
    return str(name).strip() if isinstance(name, str) and name.strip() else fallback


def lang_dir(config_dir: str | Path | None = None) -> Path:
    return I18n(config_dir=config_dir).lang_dir()


def export_language(
    target: Path,
    language: str | None = None,
    config_dir: str | Path | None = None,
) -> None:
    """ส่งออกคู่ key/ข้อความของภาษาที่ระบุ (หรือภาษาที่ active อยู่) ลงไฟล์ JSON."""
    i18n = I18n(language or (_active.language if _active else DEFAULT_LANGUAGE), config_dir)
    data = {}
    for key in TH:
        data[key] = i18n.text(key)
    for key, value in i18n._data.items():
        if key not in data:
            data[key] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def import_language(
    source: Path,
    config_dir: str | Path | None = None,
) -> str | None:
    """นำเข้าภาษา JSON ไปไว้ที่ config/lang/<ชื่อไฟล์>.json → คืน language code."""
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        return None
    destination = lang_dir(config_dir)
    code = source.stem
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f"{code}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return code