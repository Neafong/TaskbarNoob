"""Auto-Migration จากรหัสเดิม `taskbargroups` → `taskbarnoob` บน Linux Mint (Cinnamon).

ทำงานแบบ idempotent (รันซ้ำได้ปลอดภัย ไม่พังถ้าไม่พบของเก่า):
1. ปักหมุดบน panel: แทนที่ `taskbargroups-<slug>.desktop` → `taskbarnoob-<slug>.desktop`
   ในตำแหน่งเดิมบน Grouped Window List / panel-launchers พร้อมติดตั้งไอคอนใหม่และลบไฟล์เก่า
2. ฮอตคีย์ Cinnamon: ย้าย slot `taskbargroups-<slug>` → `taskbarnoob-<slug>`
   แล้วล้าง/ถอน slot เก่าอย่างปลอดภัยตามกติกาของ Cinnamon
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from ...storage import ConfigStore, StorageError
from . import desktop as _desktop
from . import hotkeys as _hotkeys
from . import panel as _panel

LEGACY_APP_ID = "taskbargroups"


def _slug_for_dir(dir_name: str) -> str:
    return "".join(
        ch if (ch.isalnum() or ch in "-_") else "-"
        for ch in str(dir_name).strip().lower()
    ).strip("-") or "group"


def legacy_launcher_id(dir_name: str) -> str:
    return f"{LEGACY_APP_ID}-{_slug_for_dir(dir_name)}"


def legacy_desktop_file_name(dir_name: str) -> str:
    return f"{legacy_launcher_id(dir_name)}.desktop"


def legacy_hotkey_slot(dir_name: str) -> str:
    return f"{LEGACY_APP_ID}-{_slug_for_dir(dir_name)}"


def _replace_in_grouped_window_list(
    old_id: str, new_id: str, config_dir: Path | None = None
) -> bool:
    """แทนที่ `old_id` → `new_id` ในตำแหน่งเดิมของ `pinned-apps`."""
    replaced = False
    for path in _panel._grouped_window_config_files(config_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "pinned-apps" not in data:
            continue
        entry = data["pinned-apps"]
        values = entry.get("value") if isinstance(entry, dict) else entry
        if not isinstance(values, list) or old_id not in values:
            continue
        new_values: list[str] = []
        for item in values:
            if item == old_id:
                if new_id not in new_values:
                    new_values.append(new_id)
                replaced = True
            elif item == new_id and new_id in new_values:
                continue
            else:
                new_values.append(item)
        if isinstance(entry, dict):
            entry["value"] = new_values
        else:
            data["pinned-apps"] = new_values
        try:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            continue
    return replaced


def _replace_in_panel_launchers(
    old_id: str, new_id: str, runner: Callable = _panel._run
) -> bool:
    """แทนที่ `old_id` → `new_id` ใน `panel-launchers` (กรณีไม่ได้ใช้ Grouped Window List)."""
    try:
        current = _panel.read_panel_launchers(runner)
    except _panel.PinError:
        return False
    if old_id not in current:
        return False
    updated: list[str] = []
    for item in current:
        if item == old_id:
            if new_id not in updated:
                updated.append(new_id)
        elif item == new_id and new_id in updated:
            continue
        else:
            updated.append(item)
    runner(
        [
            "gsettings",
            "set",
            _panel.CINNAMON_SCHEMA,
            _panel.LAUNCHERS_KEY,
            _panel._format_string_array(updated),
        ]
    )
    return True


def _remove_legacy_launcher_icon(
    old_icon_id: str, icons_root: Path | str | None = None
) -> None:
    root = Path(icons_root) if icons_root is not None else _desktop.hicolor_icons_dir()
    for subdir in ("256x256/apps", "scalable/apps"):
        folder = root / subdir
        if not folder.is_dir():
            continue
        for old in folder.glob(f"{old_icon_id}.*"):
            try:
                old.unlink()
            except OSError:
                pass


def migrate_pinned_launchers(
    store: ConfigStore,
    applications_dir: Path | str | None = None,
    icons_root: Path | str | None = None,
    panel_config_dir: Path | None = None,
    runner: Callable = _panel._run,
) -> int:
    """ย้าย launcher ที่ปักไว้จาก `taskbargroups-*.desktop` → `taskbarnoob-*.desktop`."""
    apps_dir = (
        Path(applications_dir)
        if applications_dir is not None
        else _desktop.applications_dir()
    )
    pinned = _panel.pinned_desktop_ids(panel_config_dir, runner)
    migrated = 0
    for dir_name in store.list_groups():
        old_id = legacy_desktop_file_name(dir_name)
        new_id = _desktop.desktop_file_name(dir_name)
        if old_id not in pinned:
            continue
        try:
            group = store.load_group(dir_name)
            _desktop.install_launcher(
                group, store, dir_name, target_dir=apps_dir, icons_root=icons_root
            )
        except (StorageError, OSError):
            continue
        swapped = _replace_in_grouped_window_list(old_id, new_id, panel_config_dir)
        if not swapped:
            swapped = _replace_in_panel_launchers(old_id, new_id, runner)
        if not swapped:
            continue
        old_desktop = apps_dir / old_id
        try:
            if old_desktop.exists():
                old_desktop.unlink()
        except OSError:
            pass
        _remove_legacy_launcher_icon(legacy_launcher_id(dir_name), icons_root)
        migrated += 1
    if migrated > 0:
        try:
            _panel.reload_grouped_window_applet()
        except _panel.PinError:
            pass
    return migrated


def migrate_cinnamon_hotkeys(
    store: ConfigStore,
    runner: Callable = _hotkeys._run,
) -> int:
    """ย้ายฮอตคีย์ Cinnamon จาก slot `taskbargroups-*` → `taskbarnoob-*`."""
    try:
        raw_list = runner(_hotkeys.list_command())
    except _hotkeys.HotkeyError:
        return 0
    slots = _hotkeys._clean_list(_hotkeys.parse_gvariant_string_array(raw_list))
    if not slots:
        return 0
    migrated = 0
    for dir_name in store.list_groups():
        old_slot = legacy_hotkey_slot(dir_name)
        new_slot = _hotkeys.hotkey_slot(dir_name)
        if old_slot not in slots:
            continue
        binding = _hotkeys.get_binding(old_slot, runner)
        try:
            group = store.load_group(dir_name)
            title = f"TaskbarNoob — {group.name}"
        except StorageError:
            title = f"TaskbarNoob — {dir_name}"
        if binding and new_slot not in slots:
            cmd = _desktop.build_exec(dir_name, center=True)
            _hotkeys.register_cinnamon_hotkey(new_slot, title, cmd, binding, runner)
        _hotkeys.unregister_cinnamon_hotkey(old_slot, runner)
        migrated += 1
    return migrated


def migrate_legacy_linux_state(
    store: ConfigStore,
    applications_dir: Path | str | None = None,
    icons_root: Path | str | None = None,
    panel_config_dir: Path | None = None,
) -> tuple[int, int]:
    """รัน Auto-Migration ทั้งปักหมุดและฮอตคีย์อย่างปลอดภัย (ไม่โยน error ใส่ผู้ใช้)."""
    if os.environ.get("TASKBARNOOB_NO_PIN") or os.environ.get("TASKBARGROUPS_NO_PIN"):
        return (0, 0)
    if not _hotkeys.is_cinnamon():
        return (0, 0)
    pins = 0
    keys = 0
    try:
        pins = migrate_pinned_launchers(
            store,
            applications_dir=applications_dir,
            icons_root=icons_root,
            panel_config_dir=panel_config_dir,
        )
    except (OSError, _panel.PinError):
        pass
    try:
        keys = migrate_cinnamon_hotkeys(store)
    except (OSError, _hotkeys.HotkeyError):
        pass
    return (pins, keys)
