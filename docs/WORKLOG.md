# Work Log — TaskbarNoob (v0.3.0+)

> บันทึกงานย้อนหลังต่อเฟส (append-only) · ประวัติภาค v0.1–v0.2 ถูกเก็บไว้ที่ [`archive/WORKLOG-v0.1-v0.2.md`](archive/WORKLOG-v0.1-v0.2.md)
> Snapshot ปัจจุบันอยู่ที่ [`../AGENTS.md`](../AGENTS.md) · แผนงานอยู่ที่ [`roadmap.md`](roadmap.md)

## 2026-11-23 — R0: จัดระเบียบเอกสาร (`docs/`) + แก้บั๊กเทสต์ฐานเดิมบน Mint `[เสร็จ]`
- **แก้บั๊กเทสต์บน Linux (`core/storage.py`):** เรียงผลลัพธ์ `self.groups_dir.iterdir()` ด้วย `sorted(..., key=lambda p: p.name.casefold())` ใน `ConfigStore._prune_order()` → `test_order_matches_disk_after_selfheal` ผ่านบน Linux ext4 (375 เทสต์ ผ่าน 100%, skipped 10 Windows-only)
- **จัดระเบียบ `docs/`:**
  - ย้าย `WORKLOG.md` (1,369 บรรทัด), `feedback.md` (~110 KB), `phase18-plan.md`, `windows-plan.md` ลง [`archive/`](archive/)
  - เริ่ม `docs/WORKLOG.md` และ `docs/feedback.md` ชุดใหม่สำหรับภาค `v0.3.0` ให้สั้นเบา ประหยัด token
  - อัปเดต `docs/README.md`, `docs/team.md`, `docs/roadmap.md` และ `AGENTS.md` ให้สะท้อนสถานะล่าสุด (`v0.2.0` ปล่อยแล้ว, workspace หลักบน Mint `/mnt/Backup/TaskbarNoob`, ทำงานร่วมกับเจนนี่)
- **ต่อไป:** เฟส **R1** — แยก Platform Backend เข้า `core/platform/{base,linux,win32}` + พับเก็บ `core/macos.py`

## 2026-11-23 — R1: แยก Platform Backend (`core/platform/`) + พับเก็บ macOS `[เสร็จ]`
- **สร้างแพ็กเกจ `core/platform/`:**
  - `base.py` — `PlatformBackend` ABC กำหนดสัญญาเมธอดกลาง (`supports_direct_pin`, `supports_cinnamon_hotkeys`, `supports_win_hotkeys`, `set_app_process_id`, `set_group_process_id`, launcher/pin/stale_pin_label)
  - `linux/` — ย้าย `desktop.py`, `panel.py`, `hotkeys.py` พร้อม `LinuxCinnamonBackend`
  - `win32/` — แตก `core/win32.py` (849 บรรทัด) เป็น 6 โมดูลย่อยตามหน้าที่ (`aumid.py`, `com.py`, `ico.py`, `lnk.py`, `pin.py`, `hotkey.py`) + `Win32Backend`
  - `__init__.py` — `get_backend()` + facade กลาง
- **พับเก็บ macOS:** ลบ `core/macos.py`, `tests/test_macos.py` และ branch `darwin` ใน `core/launcher.py`, `core/icons.py`, `gui/flyout.py`
- **ลด `sys.platform` ใน `gui/`:** ย้าย `_reveal()` เข้า `core/launcher.reveal_path()` (ลด `sys.platform` ใน `gui/flyout.py` เหลือ 0) และให้ `gui/main_window.py` เรียกผ่าน `core.platform` / `get_backend()`
- **ลบไฟล์เก่าซ้ำซ้อน:** `core/taskbar.py`, `core/launchers.py`, `core/win32.py`
- **เทสต์:** อัปเดต imports + เพิ่ม `test_backend_capabilities` → **367 เทสต์ ผ่าน 100% (`OK (skipped=10)`)**
- **ต่อไป:** เฟส **R2** — แตกไฟล์ยักษ์ (`gui/group_editor.py`, `gui/main_window.py`) เป็นโมดูลย่อยหน้าที่เดียว

## 2026-11-23 — R2: แตกไฟล์ยักษ์ GUI เป็นโมดูลย่อยหน้าที่เดียว `[เสร็จ]`
- **แตก `gui/group_editor.py` (1,240 → 570 บรรทัด):**
  - `gui/icon_picker.py` (327 บรรทัด) — `SystemIconDialog` (`_SystemIconDialog`) + Windows DLL/Start Menu helpers
  - `gui/shortcut_grid.py` (237 บรรทัด) — `_DropHighlightDelegate` + `ShortcutGrid`
  - `gui/shortcut_dialog.py` (212 บรรทัด) — `ShortcutDialog` + `_style_dialog_buttons`
- **แตก `gui/main_window.py` (1,193 → 759 บรรทัด):**
  - `gui/group_list.py` (353 บรรทัด) — `_RowDropHighlightDelegate` + `GroupListWidget` + `PINNED_ROLE` + `_style_menu`
  - `gui/app.py` (93 บรรทัด) — `run()`, `_run_flyout()`, `_register_saved_win_hotkeys()` + อัปเดต `__main__.py` เรียก `gui.app.run`
- **เทสต์:** อัปเดต mock target ใน `tests/test_group_editor.py` → **367 เทสต์ ผ่าน 100% (`OK (skipped=10)`)** + `compileall` ผ่าน
- **ต่อไป:** เฟส **R3** — รวม Icon Pipeline เดียว + ตัวเลือกไอคอนระบบแยกหมวดบน Linux Mint + Steam `steam://rungameid/<appid>` icon resolver ข้าม OS
