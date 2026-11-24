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

- **Build `.deb` สำเร็จ:** `dist/taskbarnoob_0.3.0_amd64.deb` (43 MB · `Package: taskbarnoob`, `Version: 0.3.0`, `Replaces: taskbargroups`, `Conflicts: taskbargroups`, แพ็ก `assets/lang/*.json` ทั้ง 7 ภาษา + `taskbarnoob.svg` ครบ)

---

## 📌 Handoff สำหรับเจนนี่ฝั่ง Windows 11 (v0.3.0)

ฝั่ง **Linux Mint (Cinnamon)** เสร็จสมบูรณ์ 100% และ push ขึ้น `origin/main` แล้วค่ะ ต่อไปเป็นคิวทดสอบและ build ฝั่ง **Windows 11** ก่อนปล่อย GitHub Release `v0.3.0`:

### สิ่งที่เปลี่ยนแปลงใหญ่ใน v0.3.0 ที่กระทบฝั่ง Windows 11
1. **รีแบรนด์แพ็กเกจภายใน:** `taskbargroups` → `taskbarnoob` (AUMID ใหม่: `Noob.TaskbarNoob.*`, env: `TASKBARNOOB_CONFIG` โดยยังรองรับ `TASKBARGROUPS_CONFIG` เก่า)
2. **แยกแพลตฟอร์มเป็น 6 โมดูลย่อย:** `taskbarnoob/core/platform/win32/{com,aumid,icons,shortcuts,taskbar,launcher}.py` + ลบ PowerShell dead code ทิ้งหมดแล้ว (ใช้ COM `IShellLinkW` + `IPropertyStore` ล้วน)
3. **ปุ่ม "จากแอป..." (`gui/app_picker.py`):** สแกน Start Menu (`.lnk` + MSIX/WindowsApps เช่น Affinity) มาให้เลือกเพิ่มเข้ากลุ่มได้ตรงๆ ในคลิกเดียว
4. **9 ภาษาในตัวแอป (`packaging/lang/*.json`):** อัปเดต `packaging/build_windows.ps1` ให้แพ็ก `--add-data "packaging/lang;taskbarnoob/assets/lang"` แล้ว
5. **Steam icon resolver (`core/icons/steam.py`):** รองรับ `steam://rungameid/<appid>` ข้าม OS รวมถึงไฟล์ `.url` ของ Steam บน Windows
6. **Electron/Portable ASAR icon (`core/icons/portable.py`)** + **ไอคอนแอปเนียนทุกระดับ (`app_window_icon()`)**

### เช็กลิสต์สำหรับเจนนี่ฝั่ง Windows 11
1. **ซิงก์โค้ดล่าสุด:** `git pull origin main`
2. **รันเทสต์เต็มระบบบน Windows:** `python tests/run.py`
   - ยืนยันว่า **392/392 เทสต์ผ่าน 100% (0 skipped)** รวมถึงเทสต์ Windows COM/Shell32 ทั้ง 10 ตัว
3. **Build Windows Portable:** `powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1`
   - ตรวจว่า `dist/TaskbarNoob/` มี `taskbarnoob/assets/lang/` ครบทั้ง 7 ไฟล์ JSON (+ `th`/`en` ในตัว รวม 9 ภาษา)
   - นำไปทดสอบใช้งานจริงที่ `D:\Portable\Tool\TaskbarNoob`
4. **Live-Test บน Windows 11:**
   - [x] เปิดแอปได้ปกติ, ไอคอน titlebar/taskbar คมเนียน
   - [x] เปลี่ยนภาษาใน Settings เห็นครบทั้ง 9 ภาษาและเปลี่ยนได้จริง *(แก้บั๊ก `set_language().lower()` ที่ทำให้ `zh_CN`/`pt_BR` เด้ง dropdown กลับไทย — กระทบทั้ง Win & Linux · ฝั่ง Mint ต้อง `git pull` + rebuild AppImage/`.deb` ใหม่)*
   - [x] กดปุ่ม **"จากแอป..."** ใน Group Editor → ใช้งานได้
   - [x] เปิดแอปต่างๆ จาก flyout ได้ปกติ (ทั้งกลุ่มเดิมและกลุ่มใหม่)
   - [x] สร้างกลุ่มใหม่และแก้ไขกลุ่มเดิมใช้งานได้ปกติ
   - [x] Global Hotkey Win32 + Flyout foreground focus ทำงานปกติ *(ทำงานระหว่างเปิดแอปตามการออกแบบ Win32 `RegisterHotKey`)*
   - [x] ไอคอนเกม Steam (`steam://rungameid/...` หรือ `.url`) แสดงครบ *(ตรวจ `River City Melee Battle Royal Special` AppID `544630` — ต้นเหตุคือแคชกระดาษขาวเก่าค้างจาก v0.2.0 · พอแอดใหม่ใน v0.3.0 ดึง `logo.png` จาก `librarycache` ผ่านสมบูรณ์!)*
5. **ปล่อย GitHub Release `v0.3.0`:** (ส่งไม้ต่อกลับไปฝั่ง Linux Mint ด้านล่าง)

## 2026-11-24 — ปิดจ๊อบทดสอบฝั่ง Windows 11 (`v0.3.0`) + Docs Audit + ล็อกแผน `v0.4.0` `[เสร็จ]`
- **แก้บั๊กข้าม OS (`zh_CN` / `pt_BR` เด้งกลับไทย):**
  - `taskbarnoob/core/settings.py`: ลบ `.lower()` ใน `Settings.set_language()` เพื่อคงตัวพิมพ์ใหญ่ของรหัสภาษา (`zh_CN`, `pt_BR`)
  - `taskbarnoob/core/i18n/__init__.py`: เพิ่ม `_find_lang_file()` จับคู่ไฟล์ภาษาแบบ case-insensitive fallback ให้ไฟล์ `settings.json` เก่าที่เก็บ `"zh_cn"` ยังโหลดติดทั้งบน Linux ext4 และ Windows NTFS
  - `taskbarnoob/gui/settings_dialog.py`: เพิ่ม `.casefold()` fallback ตอนเลือกภาษาปัจจุบันใน dropdown
  - `tests/test_settings.py`: เพิ่ม 2 เทสต์ (`test_set_language_preserves_case`, `test_mixed_case_language_restored_on_reopen`) → **394 เทสต์ ผ่าน 100% (`OK (skipped=25 Linux-only)`)**
- **Build & Live-Test Windows 11:** build ผ่าน `packaging/build_windows.ps1` → deploy ทับ `D:\Portable\Tool\TaskbarNoob` (ไม่แตะ `config\`) → Live-Test ผ่านครบทั้ง 7/7 ข้อ + แพ็ก `dist\TaskbarNoob-win64-portable.zip`
- **Docs Audit & กฎ Release Hygiene:**
  - เพิ่มกฎถาวร **Docs Hygiene** ใน `AGENTS.md` + ยกเครื่อง `docs/release-process.md` (เพิ่ม Docs Audit Checklist + ขั้นตอนข้าม 2 OS Linux Mint ↔ Windows 11)
  - ซ่อมเอกสาร GitHub ที่ยังค้างชื่อ `taskbargroups` / ข้อมูลเก่า: `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `CHANGELOG.md`, `README.md`, `README.th.md`, `docs/feedback.md`, `docs/roadmap.md`

---

## 📌 Handoff #1 — ปิดจ๊อบ `v0.3.0` สำหรับเจนนี่ฝั่ง Linux Mint (ทำทันที!)

ฝั่ง **Windows 11** ทดสอบผ่านครบ 100% และ push commit สุดท้าย (รวมแก้บั๊ก `zh_CN`/`pt_BR` + Docs Audit) ขึ้น `origin/main` แล้วค่ะ
⚠️ **สำคัญ:** บั๊ก `set_language().lower()` กระทบฝั่ง Linux (ext4 case-sensitive) หนักกว่า Windows เพราะทำให้เปิดแอปใหม่แล้วโหลด `zh_cn.json` ไม่เจอเลย → **ฝั่ง Mint ต้อง `git pull` แล้ว rebuild AppImage + `.deb` ใหม่ก่อนปล่อย Release `v0.3.0` นะคะ!**

### เช็กลิสต์ปิดจ๊อบ `v0.3.0` ฝั่ง Linux Mint
1. **ซิงก์โค้ดล่าสุด:** `git pull origin main`
2. **รันเทสต์เต็มระบบ:** `QT_QPA_PLATFORM=offscreen .venv/bin/python tests/run.py`
   - ยืนยัน **394 เทสต์ ผ่าน 100% (`skipped=10` Windows-only)**
3. **Rebuild แพ็กเกจ Linux ทั้ง 2 ตัว:**
   - `bash packaging/build_appimage.sh` → คัดลอกทับ `~/AppImage/Tool/TaskbarNoob-x86_64.AppImage`
   - `bash packaging/build_deb.sh` → `dist/taskbarnoob_0.3.0_amd64.deb`
4. **Smoke Test สั้นๆ บน Mint:**
   - รัน `~/AppImage/Tool/TaskbarNoob-x86_64.AppImage --list`
   - เปิดแอป → ลองสลับเป็น `简体中文` หรือ `Português (Brasil)` → ปิดแล้วเปิดใหม่ ยืนยันว่าภาษาและ dropdown ตรงกัน (ไม่เด้งกลับไทย) แล้วสลับกลับภาษาเดิม
5. **สร้าง Tag & ปล่อย GitHub Release `v0.3.0`:**
   - `git tag -a v0.3.0 -m "TaskbarNoob v0.3.0: Full architecture refactor, rebrand, 9 languages & App Picker"`
   - `git push origin v0.3.0`
   - ปล่อย Release บน GitHub แนบครบ **3 assets**:
     - `TaskbarNoob-x86_64.AppImage` (จากเครื่อง Mint)
     - `taskbarnoob_0.3.0_amd64.deb` (จากเครื่อง Mint)
     - `TaskbarNoob-win64-portable.zip` (แพ็กเสร็จแล้วบนเครื่อง Windows ที่ `D:\Obsidian\TaskbarNoob\dist\TaskbarNoob-win64-portable.zip`)

---

## 📌 Handoff #2 — แผนเริ่มงาน `v0.4.0` (เริ่มหลังปล่อย Release `v0.3.0` เรียบร้อยแล้ว)

> ดูสเปกละเอียดใน [`docs/roadmap.md`](roadmap.md) และรายการเช็กใน [`docs/feedback.md`](feedback.md)
> **หลักการ:** ล็อกขอบเขตแค่ 5 ข้อนี้ให้จบไว เสถียร และคลีนทั้ง Linux Mint + Windows 11 (ห้ามเพิ่ม scope นอกแผนโดยไม่ถามพี่ก่อน)

1. **System Tray Icon (`QSystemTrayIcon`):**
   - `Settings.minimize_to_tray: bool = False` + ช่องติ๊กใน `SettingsDialog` (แปลครบ 9 ภาษา)
   - เมื่อเปิด: กด `X` → ซ่อนหน้าต่างลง Tray (ให้ Win32 Global Hotkeys ยังทำงานต่อได้)
   - เมนูคลิกขวาเรียบง่าย: **เปิด TaskbarNoob** (default) · **ตั้งค่า... (Settings)** · เส้นคั่น · **ออก (Quit)**
2. **`.url` Resilience + แคชไอคอน `.url→.exe` (3A):**
   - เพิ่ม `parse_url_file()` ใน `core/` → แคชไอคอนจาก `IconFile=` (รวม `.exe`/`.ico` เช่นเกม Epic) หรือ Steam `librarycache` ลง `icons/` ก่อน แล้วแตก `URL=` เก็บเป็น `target` ตรงๆ (ลบ `.url` บน Desktop ก็ยังเปิดได้)
   - แก้ `_launch_linux()` ให้ส่ง URI scheme (`://`) เข้า `gio open` / `xdg-open`
3. **ปุ่ม "ดึงไอคอนใหม่" (Re-detect Icon — 3B):**
   - เพิ่มใน `ShortcutDialog` และคลิกขวาบนกริดใน `GroupEditor` ให้ดึงไอคอนจาก target ใหม่ทับแคชเดิมในคลิกเดียว
4. **เลือกหลายแอปพร้อมกันใน "จากแอป..." (Multi-select — 3C):**
   - เปลี่ยน `AppPickerDialog` เป็น `ExtendedSelection` เพื่อเลือกหลายแอปเข้ากลุ่มในรอบเดียว
5. **เตือนเงียบๆ เมื่อ shortcut ชี้ไฟล์ที่หายไปแล้ว (Broken Target — 3D):**
   - แสดงเฉพาะตอนผู้ใช้เปิดโปรแกรมเราเท่านั้น (ใน `GroupEditor` / `ShortcutDialog`) **ห้ามเด้ง popup หรือ OS notification พลการ**
6. **ปิดรุ่น `v0.4.0`:** ไล่เช็ก **Docs Audit Checklist** ใน `docs/release-process.md` ให้ครบทุกไฟล์ก่อน tag เสมอ!
