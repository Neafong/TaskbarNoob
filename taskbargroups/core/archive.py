"""Export/import ทั้งชุด config เป็น ZIP (Phase 18).

โครง zip:
- groups/  (โฟลเดอร์กลุ่มทั้งหมด: group.json + ไอคอน)
- order.json
- settings.json (ถ้ามี)
- lang/ (ถ้ามี *.json)

ไฟล์นี้เป็น Python ล้วน ไม่ import Qt.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import paths
from .models import Group
from .storage import GROUP_FILE_NAME, ORDER_FILE, ConfigStore

EXPORT_DEFAULT_NAME = "taskbargroups-backup-{ts}.zip"
MAX_ZIP_BYTES = 256 * 1024 * 1024

_TOP_LEVEL_ALLOWED = {"groups", "order.json", "settings.json", "lang"}


class ArchiveError(Exception):
    """ข้อผิดพลาดในการ export/import zip config (ข้อความจริงขึ้นกับ UI/i18n)."""


@dataclass
class ZipReport:
    groups: list[str]
    has_settings: bool
    has_lang: list[str]
    member_count: int
    total_size: int


@dataclass
class ImportReport:
    mode: str
    groups_imported: list[str]
    groups_kept: list[str]
    settings_imported: bool
    lang_imported: list[str]
    backup_dir: Path | None = None


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _is_unsafe_member(name: str) -> bool:
    """zip-slip guard: ปฏิเสธ absolute path, backslash, หรือ `..` ใน path."""
    if name.startswith("/") or "\\" in name:
        return True
    return ".." in Path(name).parts


def _top_level(name: str) -> str:
    return name.split("/", 1)[0]


def export_config(config_dir: str | Path, target: str | Path) -> Path:
    cfg = Path(config_dir)
    groups_root = paths.groups_root(cfg)
    order_path = cfg / ORDER_FILE
    settings_path = cfg / "settings.json"
    lang_dir = cfg / "lang"

    out = Path(target)
    if out.suffix.lower() != ".zip":
        out = out.with_suffix(".zip")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ArchiveError(f"สร้างโฟลเดอร์ปลายทางไม่สำเร็จ: {exc}") from exc

    try:
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if groups_root.is_dir():
                for root, _dirs, files in os.walk(groups_root):
                    rpath = Path(root)
                    rel_root = (
                        rpath.relative_to(groups_root) if rpath != groups_root else Path(".")
                    )
                    for fname in files:
                        full = rpath / fname
                        rel = str(rel_root / fname).replace("\\", "/").lstrip("./")
                        if rel in {"", "."}:
                            continue
                        zf.write(full, f"groups/{rel}")
            if order_path.is_file():
                zf.write(order_path, "order.json")
            if settings_path.is_file():
                zf.write(settings_path, "settings.json")
            if lang_dir.is_dir():
                for lang_file in sorted(lang_dir.glob("*.json")):
                    zf.write(lang_file, f"lang/{lang_file.name}")
    except OSError as exc:
        raise ArchiveError(f"เขียนไฟล์ zip ไม่สำเร็จ: {exc}") from exc
    return out.resolve()


def inspect_zip(path: str | Path) -> ZipReport:
    p = Path(path)
    if not p.is_file() or not zipfile.is_zipfile(p):
        raise ArchiveError("ไฟล์ไม่ใช่ zip")
    total_size = p.stat().st_size
    if total_size > MAX_ZIP_BYTES:
        raise ArchiveError("ไฟล์ zip ใหญ่เกินกำหนด")

    groups_set: set[str] = set()
    has_settings = False
    lang_list: list[str] = []
    member_count = 0
    with zipfile.ZipFile(p, "r") as zf:
        for name in zf.namelist():
            member_count += 1
            if _is_unsafe_member(name):
                raise ArchiveError("zip contains unsafe member path")
            parts = name.split("/")
            top = parts[0] if parts else ""
            if top not in _TOP_LEVEL_ALLOWED:
                continue  # ข้ามไฟล์แปลกที่ไม่รู้จัก
            if top == "settings.json":
                has_settings = True
            elif top == "lang" and len(parts) == 2 and parts[1].endswith(".json"):
                lang_list.append(parts[1])
            elif top == "groups" and len(parts) >= 2 and parts[1]:
                groups_set.add(parts[1])
    return ZipReport(
        groups=sorted(groups_set),
        has_settings=has_settings,
        has_lang=sorted(set(lang_list)),
        member_count=member_count,
        total_size=total_size,
    )


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            _copy_tree(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)


def _backup_prefix(config_dir: str | Path) -> str:
    return f"{Path(config_dir).name}.bak-"


def list_backups(config_dir: str | Path) -> list[Path]:
    """หาฟอล์เดอร์สำรอง `config.bak-*` (จากการนำเข้าแบบ replace) เรียงล่าสุดก่อน."""
    cfg = Path(config_dir)
    prefix = _backup_prefix(cfg)
    return sorted(
        (
            p
            for p in cfg.parent.iterdir()
            if p.is_dir() and p.name.startswith(prefix)
        ),
        key=lambda p: p.name,
        reverse=True,
    )


def delete_backups(config_dir: str | Path, backups: list[Path]) -> int:
    """ลบฟอล์เดอร์สำรอง — ยอมลบเฉพาะ `config.bak-*` ในโฟลเดอร์เดียวกันกับ config เท่านั้น."""
    cfg = Path(config_dir).resolve()
    prefix = f"{cfg.name}.bak-"
    count = 0
    for backup in backups:
        try:
            path = Path(backup).resolve()
        except OSError:
            continue
        if path.parent != cfg.parent or not path.name.startswith(prefix):
            continue
        shutil.rmtree(path, ignore_errors=True)
        count += 1
    return count


def _validate_staged_groups(staging: Path) -> None:
    groups_root = staging / "groups"
    if not groups_root.is_dir():
        return
    for gdir in sorted(groups_root.iterdir()):
        if not gdir.is_dir():
            continue
        gfile = gdir / GROUP_FILE_NAME
        if not gfile.is_file():
            continue
        try:
            data = json.loads(gfile.read_text(encoding="utf-8"))
            Group.from_dict(data)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise ArchiveError(f"invalid group.json in '{gdir.name}': {exc}") from exc


def _extract_to_staging(p: Path, staging: Path) -> None:
    with zipfile.ZipFile(p, "r") as zf:
        for name in zf.namelist():
            if _is_unsafe_member(name):
                raise ArchiveError("zip contains unsafe member path")
            top = _top_level(name)
            if top not in _TOP_LEVEL_ALLOWED:
                continue
            zf.extract(name, staging)


def _replace_from_staging(staging: Path, cfg: Path) -> Path:
    backup_dir = cfg.with_name(f"{cfg.name}.bak-{_timestamp()}")
    suffix = 0
    while backup_dir.exists():
        suffix += 1
        backup_dir = cfg.with_name(f"{cfg.name}.bak-{_timestamp()}-{suffix}")
    try:
        if cfg.is_dir():
            shutil.copytree(cfg, backup_dir)
        else:
            backup_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, shutil.Error) as exc:
        raise ArchiveError(f"สำรอง config เดิมไม่สำเร็จ: {exc}") from exc

    shutil.rmtree(cfg, ignore_errors=True)
    cfg.mkdir(parents=True, exist_ok=True)
    _copy_tree(staging / "groups", paths.groups_root(cfg))
    if (staging / ORDER_FILE).is_file():
        shutil.copy2(staging / ORDER_FILE, cfg / ORDER_FILE)
    if (staging / "settings.json").is_file():
        shutil.copy2(staging / "settings.json", cfg / "settings.json")
    if (staging / "lang").is_dir():
        shutil.copytree(staging / "lang", cfg / "lang", dirs_exist_ok=True)
    return backup_dir


def _merge_from_staging(staging: Path, cfg: Path) -> tuple[list[str], list[str]]:
    store = ConfigStore(cfg)
    imported: list[str] = []
    kept: list[str] = []
    groups_root = staging / "groups"
    if not groups_root.is_dir():
        return imported, kept
    for gdir in sorted(groups_root.iterdir()):
        if not gdir.is_dir():
            continue
        gfile = gdir / GROUP_FILE_NAME
        if not gfile.is_file():
            continue
        try:
            data = json.loads(gfile.read_text(encoding="utf-8"))
            group = Group.from_dict(data)
        except (OSError, ValueError, TypeError, KeyError):
            continue
        original_name = group.name
        group.name = store.unique_group_name(group.name, use_parens=True)
        try:
            saved_path = store.save_group(group)
        except Exception:
            continue
        new_dir = saved_path.parent.name
        target_dir = paths.groups_root(cfg) / new_dir
        for item in gdir.iterdir():
            if item.name == GROUP_FILE_NAME:
                continue
            if item.is_dir():
                _copy_tree(item, target_dir / item.name)
            else:
                shutil.copy2(item, target_dir / item.name)
        if group.name != original_name:
            kept.append(original_name)
        imported.append(new_dir)

    order = store.load_order()
    for dname in store.list_groups():
        if dname not in order:
            order.append(dname)
    for dname in imported:
        if dname not in order:
            order.append(dname)
    store.save_order(order)
    return imported, kept


def import_config(
    path: str | Path,
    config_dir: str | Path,
    mode: str = "merge",
) -> ImportReport:
    if mode not in {"merge", "replace"}:
        raise ArchiveError(f"unknown import mode: {mode}")
    p = Path(path)
    cfg = Path(config_dir)
    if not p.is_file() or not zipfile.is_zipfile(p):
        raise ArchiveError("ไฟล์ไม่ใช่ zip")
    if p.stat().st_size > MAX_ZIP_BYTES:
        raise ArchiveError("ไฟล์ zip ใหญ่เกินกำหนด")

    staging = cfg.parent / f"config.import-{os.getpid()}-{_timestamp()}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    try:
        _extract_to_staging(p, staging)
        _validate_staged_groups(staging)
        if not (staging / "groups").is_dir() and not (
            staging / "order.json"
        ).is_file() and not (staging / "settings.json").is_file() and not (
            staging / "lang"
        ).is_dir():
            raise ArchiveError("zip นี้ไม่ใช่ไฟล์สำรองของ TaskbarNoob")

        if mode == "replace":
            backup_dir = _replace_from_staging(staging, cfg)
            report = inspect_zip(p)
            return ImportReport(
                mode=mode,
                groups_imported=report.groups[:],
                groups_kept=[],
                settings_imported=report.has_settings,
                lang_imported=report.has_lang[:],
                backup_dir=backup_dir,
            )

        imported, kept = _merge_from_staging(staging, cfg)
        return ImportReport(
            mode=mode,
            groups_imported=imported,
            groups_kept=kept,
            settings_imported=False,
            lang_imported=[],
            backup_dir=None,
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)
