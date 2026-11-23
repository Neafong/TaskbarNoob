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

## 2026-11-23 — R3: รวม Icon Pipeline เดียว + แยกหมวด Mint + Steam Icon Resolver `[เสร็จ]`
- **แตก `core/icons.py` เป็นแพ็กเกจ `core/icons/`:**
  - `cache.py` — `ICONS_DIR_NAME`, `PROVIDER_ICON_CACHE_DIRNAME` (แหล่งเดียวจบ), `IMAGE_SUFFIXES`, `IconError`, `cache_icon`
  - `theme.py` — `theme_search_dirs`, `desktop_search_dirs`, `find_theme_icon` + `scan_theme_icons(category="categories"|"apps"|"all")`
  - `appimage.py` — `is_appimage`, `icon_from_appimage`, `_extract_appimage_icon`
  - `steam.py` — **Steam `steam://rungameid/<appid>` icon resolver ข้าม OS** (รองรับ `.desktop` Linux, `.url` Windows, raw `steam://`, โครงสร้าง `librarycache` ทั้งเก่า `<appid>_icon.jpg` และใหม่ `<appid>/`, รวมถึง Flatpak Steam และ Windows Registry `SteamPath`)
  - `__init__.py` — facade รวม `resolve_icon_source`, `icon_from_desktop_file`, `icon_from_executable`, `cache_shortcut_icon`
- **เลิก circular import ใน `gui/icons.py`:** ย้าย `cached_provider_png` (`_cached_provider_png`, `_provider_png`) เข้า `gui/icons.py` โดยตรง — ไม่มี `from .group_editor import ...` และไม่มีค่าคงที่ซ้ำอีกต่อไป
- **ตัวเลือกไอคอนระบบแบบแยกหมวดบน Linux Mint (`gui/icon_picker.py`):** เพิ่ม `QComboBox` 3 หมวด (`หมวดหมู่และโฟลเดอร์` [default], `แอปที่ติดตั้ง`, `ไอคอนทั้งหมด`) พร้อมแคชต่อหมวด + เพิ่ม i18n keys ครบ TH/EN/`ja.json`
- **เทสต์:** เพิ่ม `tests/test_steam_icons.py` + `ScanThemeIconsTests` + `test_linux_icon_picker_switches_categories` + `test_gui_icons_has_no_circular_import_to_group_editor` → **381 เทสต์ ผ่าน 100% (`OK (skipped=10)`)** + `compileall` ผ่าน
- **ต่อไป:** เฟส **R4** — ลบ dead code PowerShell, แยก `core/i18n/`, รีแบรนด์ `taskbargroups` → `taskbarnoob` พร้อม Auto-Migration, อัปเดตเครดิต `Noob & Jenny`, และ bump เป็น `v0.3.0`

## 2026-11-23 — R4: ล้าง Dead Code, แยก `i18n`, รีแบรนด์ `taskbarnoob` + Auto-Migration + เครดิต `Noob & Jenny` (`v0.3.0`) `[เสร็จ]`
- **ลบ dead code PowerShell ฝั่ง Windows:** ลบ `build_png_to_ico_ps_script`, `build_lnk_ps_script`, `build_read_lnk_ps_script`, `lnk_command`, `_ps_quote` และเทสต์ที่ผูกอยู่
- **แยก `core/i18n.py` เป็นแพ็กเกจ `core/i18n/{__init__.py, th.py, en.py}`**
- **อัปเดตเครดิตเป็น `Noob & Jenny` (เจนนี่):** ครบทั้ง `th.py`, `en.py`, `packaging/lang/ja.json`, `gui/about_dialog.py`, `packaging/appimage/taskbarnoob.appdata.xml`, `README.md`
- **รีแบรนด์ชื่อภายในทั้งหมด `taskbargroups` → `taskbarnoob`:**
  - `git mv taskbargroups taskbarnoob` + รีเนม `packaging/appimage/taskbargroups.*` → `taskbarnoob.*`
  - อัปเดต imports, `APP_ID = "taskbarnoob"`, `TASKBARNOOB_CONFIG` (fallback `TASKBARGROUPS_CONFIG`), `TASKBARNOOB_NO_PIN` (fallback `TASKBARGROUPS_NO_PIN`), `EXPORT_DEFAULT_NAME = "taskbarnoob-backup-{ts}.zip"`, `build_appimage.sh`, `build_deb.sh` (เพิ่ม `Replaces: taskbargroups` & `Conflicts: taskbargroups`), `build_windows.ps1`, `.github/workflows/tests.yml`
- **Auto-Migration (`core/platform/linux/migrate.py` + `core/paths.py`):**
  - Non-portable `~/.config/taskbargroups` fallback เมื่อ `~/.config/taskbarnoob` ยังไม่มี
  - ย้ายการปักหมุด Cinnamon (`taskbargroups-*.desktop` → `taskbarnoob-*.desktop`) ในตำแหน่งเดิมบน panel พร้อมติดตั้งไอคอนใหม่ ลบของเก่า และ `ReloadXlet` (idempotent)
  - ย้ายฮอตคีย์ Cinnamon (`taskbargroups-*` → `taskbarnoob-*`) พร้อมล้าง/ถอน slot เก่าอย่างปลอดภัย
- **Bump เป็น `v0.3.0`** + อัปเดต `CHANGELOG.md`, `README.md`, `AGENTS.md`, `docs/roadmap.md`
- **เทสต์:** เพิ่ม `tests/test_linux_migration.py` + env/config fallback ใน `tests/test_paths.py` → **385 เทสต์ ผ่าน 100% (`OK (skipped=10)`)** + `compileall` ผ่าน
- **ต่อไป:** ทดสอบ build AppImage/deb จริงบน Linux Mint แล้วค่อยส่งไม้ต่อทดสอบฝั่ง Windows 11!

## 2026-11-24 — v0.3.0 Live-Test Polish บน Linux Mint `[เสร็จ]`
- **ไอคอนแอปขอบเนียน (`gui/icons.app_window_icon`):** สร้าง `QIcon` หลายขนาดแบบ mipmap (16–256px) + แนบ `taskbarnoob.svg` ลง `hicolor/scalable/apps/` ใน AppImage/`.deb`
- **ดึงไอคอนแอป portable / Electron `app.asar` อัตโนมัติ (`core/icons/portable.py`):** อ่าน `resources/app.asar` ด้วย Python ล้วน (แก้ปัญหา Antigravity และแอป Electron/VS Code tarball ไม่มีไอคอน)
- **ล็อกตำแหน่ง flyout เหนือไอคอนบน Cinnamon (`panel.pinned_icon_rect`):** ถามพิกัด `(x, y, w, h)` จริงของไอคอนที่ปักจาก Cinnamon DBus แล้วตรึง flyout ตรงกลางเหนือไอคอนนั้นเสมอ ไม่วิ่งตามเมาส์อีกต่อไป
- **รองรับ Flatpak/Snap + เลือกไอคอนความละเอียดสูงสุด/SVG + ปุ่ม "จากแอป..." (`gui/app_picker.py`):** แก้ Zen Browser (Flatpak) ไม่มีไอคอน และ Chrome/Firefox/Brave ขนาดไม่เท่ากัน (16px/24px) + เพิ่มไดอะล็อกค้นหา/เพิ่มแอปที่ติดตั้งในคลิกเดียว (Linux `.desktop`/Flatpak/Snap + Windows Start Menu)
- **9 ภาษาในตัวแอป (`core/i18n/` + `packaging/lang/`):** แพ็ก 9 ภาษา (`th`, `en`, `ja`, `zh_CN`, `ko`, `es`, `de`, `fr`, `pt_BR`) ติดมากับ AppImage/`.deb`/Windows `.exe` พร้อมเทสต์เช็กครบทุกคีย์ 100% → **392 เทสต์ ผ่าน 100% (`OK (skipped=10)`)**
