# Changelog

โปรเจกต์นี้ยึดแนวทาง [Keep a Changelog](https://keepachangelog.com/th/1.1.0/) และ
[Semantic Versioning](https://semver.org/lang/th/).
ข้อมูลการออกรุ่น: ขั้นตอนใน [`docs/release-process.md`](docs/release-process.md)

## [0.3.0] — 2026-11-23

รื้อโครงสร้างสถาปัตยกรรมใหม่ทั้งหมด (Full Architecture Refactor) ยึดฟีเจอร์เดิมเป็นแกน ล้างหนี้เทคนิค + รีแบรนด์ชื่อภายในเป็น `taskbarnoob` เต็มรูปแบบ

### Added

- **ตัวเลือกแอปที่ติดตั้ง ("จากแอป..." / `gui/app_picker.py`)** — ค้นหาและเพิ่มแอปในคลิกเดียว (Linux สแกน `.desktop` ทั้ง `.deb` + Flatpak + Snap / Windows สแกน Start Menu)
- **9 ภาษาในตัวแอป (`core/i18n/` + `packaging/lang/`)** — แพ็กติดมากับแอปพร้อมใช้งานทันที (`ไทย`, `English`, `日本語`, `简体中文`, `한국어`, `Español`, `Deutsch`, `Français`, `Português (Brasil)`) และยัง Export/Import ทับเองได้เหมือนเดิม
- **ดึงไอคอนแอป portable / Electron `resources/app.asar` อัตโนมัติ (`core/icons/portable.py`)** — อ่าน `app.asar` ด้วย Python ล้วน (เช่น Antigravity, VS Code tarball)
- **ตัวเลือกไอคอนระบบแบบแยกหมวดบน Linux Mint (`gui/icon_picker.py`)** — แยก 3 หมวด (`หมวดหมู่และโฟลเดอร์`, `แอปที่ติดตั้ง`, `ไอคอนทั้งหมด`) พร้อมแคชต่อหมวด
- **Steam `steam://rungameid/<appid>` icon resolver ข้าม OS (`core/icons/steam.py`)** — ดึงไอคอนเกมจาก `librarycache` (รองรับโครงสร้างเก่า/ใหม่, Flatpak Steam, `.desktop` Linux, `.url` Windows + Registry `SteamPath`)
- **Auto-Migration อัตโนมัติบน Linux Mint (`core/platform/linux/migrate.py`)** — ย้ายการปักหมุด `taskbargroups-*.desktop` → `taskbarnoob-*.desktop` ในตำแหน่งเดิมบน panel, ย้ายฮอตคีย์ Cinnamon `taskbargroups-*` → `taskbarnoob-*`, รองรับ fallback env `TASKBARGROUPS_CONFIG` / `TASKBARGROUPS_NO_PIN` และ `~/.config/taskbargroups`, และใส่ `Replaces:`/`Conflicts: taskbargroups` ใน `.deb`

### Changed

- **แยก Platform Backend (`core/platform/{base,linux,win32}`)** — ยุบไฟล์เฉพาะ OS ลง backend กลาง (`PlatformBackend` ABC) + แตก `win32.py` เป็น 6 โมดูลย่อย (`aumid`, `com`, `ico`, `lnk`, `pin`, `hotkey`) + ลด `sys.platform` ใน `gui/`
- **แตกไฟล์ยักษ์เป็นโมดูลย่อยหน้าที่เดียว** — `gui/group_editor.py` → `icon_picker`/`shortcut_grid`/`shortcut_dialog`/`group_editor`, `gui/main_window.py` → `group_list`/`app`/`main_window`, `core/icons/` (`cache`/`theme`/`appimage`/`steam`), `core/i18n/` (`th`/`en`/`__init__`)
- **รวม Icon Pipeline เป็นจุดเดียว** — เลิก circular import ใน `gui/icons.py` และรวมค่าคงที่แคชไว้ที่เดียว
- **รีแบรนด์ภายใน `taskbargroups` → `taskbarnoob`** — แพ็กเกจ Python, `APP_ID`, `.desktop`, `.deb`, AppImage, env `TASKBARNOOB_CONFIG`, และไฟล์ backup `taskbarnoob-backup-*.zip`
- **อัปเดตเครดิต** เป็น **Noob & Jenny (เจนนี่)** (TH/EN/JA, `.appdata.xml`, `README.md`)

### Removed

- พับเก็บ `core/macos.py` และ branch `darwin` ออกไปก่อน (รอเครื่อง Mac จริงสำหรับพัฒนาและทดสอบ)
- ลบโค้ด PowerShell เก่าที่ไม่ได้ใช้งานแล้วในฝั่ง Windows (`build_png_to_ico_ps_script`, `build_lnk_ps_script`, `build_read_lnk_ps_script`, `lnk_command`, `_ps_quote`)

### Fixed

- **flyout ไม่วิ่งตามเมาส์บน Cinnamon** — ถามพิกัด `(x, y, w, h)` จริงของไอคอนกลุ่มที่ปักบน panel ผ่าน Cinnamon DBus (`panel.pinned_icon_rect()`) แล้วล็อก flyout ตรงกลางเหนือไอคอนนั้นเสมอ
- **ไอคอนแอปขอบหยักบน panel/titlebar** — สร้าง `QIcon` หลายขนาดแบบ mipmap (`16–256px`) ใน `gui/icons.app_window_icon()` + แนบ `taskbarnoob.svg` ลง `hicolor/scalable/apps/`
- **Flatpak `.desktop` ไม่มีไอคอน + ไอคอนขนาดไม่เท่ากัน (16px vs 24px vs SVG)** — เพิ่มโฟลเดอร์ Flatpak/Snap ใน `core/icons/theme.py` และให้ `find_theme_icon()` เลือก SVG / ความละเอียดสูงสุด (เลี่ยง `-symbolic`) แทนการคืนไฟล์แรกที่เจอ
- `ConfigStore._prune_order()` เรียงรายชื่อโฟลเดอร์กลุ่มตามชื่อ (แก้ผลลัพธ์ไม่แน่นอนบน Linux ext4)

## [0.2.0] — 2026-11-23

รุ่นปรับปรุงใหญ่: "กระเป๋าใส่ได้ทุกอย่าง" + UI polish + รองรับ Windows 11 (portable)
· **Linux Mint (Cinnamon)** = รองรับหลัก (ทดสอบแล้ว)
· **Windows 11** = portable `TaskbarNoob.exe` (ทดสอบใช้งานจริงแล้ว — ลาก `.lnk` วางบน taskbar เองตามข้อจำกัด Win11)
· **macOS** = พับเก็บไว้ก่อนใน `v0.3.0` (รอมีเครื่องจริงสำหรับพัฒนาและทดสอบ)

### Added

- **กระเป๋าใส่ได้ทุกอย่าง** — launcher แบบ type-aware เปิด target ได้หลายชนิด (แอป · โฟลเดอร์ · ไฟล์ · URL)
- **flyout คลิกขวาเปิดที่อยู่** — เปิดตำแหน่งโฟลเดอร์ที่มีไฟล์นั้น (ทุก OS)
- **รองรับ Windows 11 (portable)** — `.lnk` ผ่าน COM `IShellLinkW` + `IPropertyStore` (แยก AUMID ต่อกลุ่ม + แยก `app_aumid()` สำหรับหน้าต่างหลักไม่ให้รวมปุ่ม) · multi-res `.ico` (16–256px) · global hotkey (`RegisterHotKey` + `AllowSetForegroundWindow` + ย้ายคีย์ตามเมื่อเปลี่ยนชื่อกลุ่ม) · ดึงไอคอนความละเอียดสูงไร้ลูกศร (`SHDefExtractIconW`) · ดึงไอคอนแอป MSIX/WindowsApps อัตโนมัติ (`IO_REPARSE_TAG_APPEXECLINK` + `IShellItemImageFactory`) · ตัวเลือกไอคอนระบบ 2 แหล่ง (`imageres.dll` / `shell32.dll` + แอป Start Menu กรอง Uninstall ออก) · Flyout เงาตามมุมโค้งไร้ขอบสี่เหลี่ยม (`Qt.NoDropShadowWindowHint` + `QGraphicsDropShadowEffect`) · สคริปต์ `packaging/build_windows.ps1`
- **ชื่อใต้ไอคอน** — เปิด/ปิดได้ต่อกลุ่ม (ค่าเริ่มต้นระดับแอป · ปิดไว้ตั้งต้น) · เปิดแล้วปุ่มกว้างตามชื่อ
- **โหมดโฟกัส (เปิดด้วย hotkey)** — flyout กลางจอ ไอคอนใหญ่ขึ้น · ขยายได้ 1.0–3.0x ต่อกลุ่ม (ค่าเริ่มต้น 2.0x)

### Changed

- **UI polish** — accent token กลาง (ปรับสีได้ที่เดียว) · ไอคอน SVG ของเรา tint ตามธีม
  · swatch สี + ช่อง hex · จัดเมนู/ลากใหม่
- **accent สีฟ้า** — ปรับเป็น `#1f9ede` (สดขึ้น) ใช้ทุกจุด (hover · selection · drop · ลิงก์)
- **hover ช่องกริด** ในตัวแก้ไข — ไฮไลท์ช่องโปร่งแสงแบบเดียวกับหน้าหลัก
- **i18n** — ไทยล้วน/อังกฤษล้วน · popup ไม่มีไอคอนปุ่ม + คำแปลครบ (`ตกลง`/`ยกเลิก`/`ปิด`)
- **ลากสลับเป็นสลับที่กัน (swap)** — ทั้งกริด shortcut และลำดับกลุ่มหน้าหลัก
  (ตรงกับที่ไฮไลท์โชว์ · ปล่อยที่ว่าง = ย้ายไปท้ายสุด)
- **ตำแหน่ง flyout ตรึงแน่นอน** — โหมดปกติวางชิดขอบ panel ตามที่จับตอนเปิด (เลิกไล่ตามเมาส์ที่มาช้า)

### Fixed

- **ไอคอนไฟล์กลายเป็นเฟือง** — ใช้ Qt icon provider ดึงไอคอนจริงจากระบบ (ทุก OS)
- **โฟลเดอร์ไม่แสดงไอคอน + คลิกขวาไม่ได้** — เดิมเช็ค `is_file()` → โฟลเดอร์ไม่มีไอคอน/ไม่มีเมนู
- **เปิดโฟลเดอร์/ไฟล์จาก AppImage ไม่ได้** — ตัด `LD_LIBRARY_PATH`/Qt/GTK ออกจาก env ของโปรเซสลูก
  (xdg-open/nemo โหลด lib ผิด) + เปิดโฟลเดอร์ผ่าน `gio open`
- **ไฟล์มีเดีย (+x) บนไดรฟ์ NTFS/exFAT เปิดไม่ขึ้น** — ดูแค่ executable-bit ไม่ได้
  (ไดรฟ์พวกนี้ทุกไฟล์ +x หมด) → ดู magic แทน (ELF/shebang/MZ ถึงรันตรง นอกนั้น `gio open`)
- **คลิกขวา reveal ไม่เคยทำงานเลย** — `flyout.py` ลืม `from pathlib import Path`
  (NameError ทุกครั้งที่คลิกขวา) · เติมสาขา Windows (`explorer /select`) + macOS (`open -R`) ด้วย
- **ไอคอนไม่รีเฟรชตอนสลับธีม** (ต้องคลิก 2 รอบ) — อ่านสีจาก app palette ตรง ๆ ตอน tint
- ชื่อ/คำแปลผสมไทย-อังกฤษในกล่องข้อความ (`โฟลเดอร์ทำงาน` · `อาร์กิวเมนต์` · `รายการทางลัด`)
- **ไอคอนปุ่มหายใน AppImage/.deb** — SVG ทั้งชุดไม่ถูกแพ็ก + หา assets ผิด layout
  (PyInstaller 6 วางใต้ `_internal/`) → ปุ่มเฟือง/ตาว่างเปล่า (ดูเหมือน 0.1.0)
- **กด shortcut ที่เป็นไฟล์รันได้แล้วแอปไม่เปิด** — `gio open` ส่งให้ editor/disk-mounter
  (หรือไม่มี handler สำหรับ ELF) · ไฟล์ที่มี `+x` (AppImage/ELF/สคริปต์) กลับไปรันตรง
- **พรีวิวไอคอนกลุ่มขยายตามสไลเดอร์** — ตรึงขนาดคงที่ (สไลเดอร์คุมแค่ไอคอนในกริด)
- **ไฮไลท์ hover ในกริดยืดหดตามข้อความ** — ใช้กรอบคงที่ขนาด gridSize ชิดขอบให้เลื่อนหนี (ไม่ตัด)
- **ไฮไลท์ตอนลากสลับหลอก** — โชว์จุดแทรกดิบ (ลงอีกช่องตอนปล่อย) · ตอนนี้โชว์ช่องลงจอดจริง
- **stroke กระโดดไปช่องสุดท้ายทั้งที่ลากไม่ถึง** — ช่องว่างระหว่างเซลล์ตีเป็นที่ว่างท้ายสุด
  · ตอนนี้ใช้เซลล์ใกล้สุด ที่ว่างจริง ๆ (เลยเซลล์สุดท้าย) ค่อยไปท้ายสุด
- **ลากย้อน (เช่น 4→1) กลายเป็นหมุน 3 ตัว** — เสียบไอเทมกลับผิดลำดับตอน source > target
- **stroke หน้าหลักเล็กกว่ากรอบ + ทับไอคอนดูตลก** — ย้ายไปวาดรองพื้นผ่าน delegate
  (แบบเดียวกับกริด เนื้อหาวาดทับทีหลัง) + ขยายเกาะขอบแถว + ระยะห่างแถว 2px + ร่อง stroke↔ไอคอน 1px

### Removed

- ตัดฟีเจอร์ "นำเข้ากลุ่ม (Windows Taskbar Groups)" ทั้งชุด — ลบปุ่ม + CLI `--import` +
  `core/importer.py` + เทสต์ (เหลือ "นำเข้าทั้งหมด" จาก `.zip` สำรองปุ่มเดียวจบ)

## [0.1.0] — 2026-10-12

รุ่นแรก · จัดกลุ่ม shortcut แล้วกดครั้งเดียวเปิดทั้งกลุ่ม — สำหรับ Linux Mint (Cinnamon)
ขึ้น GitHub: `Neafong/TaskbarNoob` (Public, GPL-3.0)

### Added

- **จัดกลุ่ม shortcut** — การ์ดใบใหญ่ มีกริดไอคอน ลากจัดลำดับได้ (grid)
- **ปักหมุดลง panel (Cinnamon Grouped Window List)** — กดแล้วเปิด flyout · มี self-heal ไอคอนหลัง reboot
- **ตั้งปุ่มลัด (hotkey) เปิดกลุ่ม** — gsettings Cinnamon + ถอนคีย์ลัดได้
- **ธีม auto / light / dark** · ปรับความโปร่งใส และขนาดไอคอน
- **Portable config** — อยู่ในโฟลเดอร์แอป (`config/`) · override ด้วย `TASKBARGROUPS_CONFIG`
- **นำเข้ากลุ่มจาก Windows Taskbar Groups** (`ObjectData.xml`) — กัน XML entity attack
- **ภาษา ไทย / English** ในตัว + **เพิ่มภาษาใหม่เอง** ผ่านไฟล์ JSON (asset ตัวอย่าง ญี่ปุ่น)
- **สำรอง/กู้คืน config ทั้งชุด (.zip)** — ส่งออกทั้งหมด / นำเข้าทั้งหมด (merge / replace) · zip-slip guard
- **ปุ่ม "ลบสำรองเก่า…"** — จัดการ `config.bak-*` ที่ค้างจากการ replace
- **CLI** — `--list` / `--open "<GroupDir>"` / `--import`
- **About / โดเนท** — Ko-fi (`ko-fi.com/neafong`)

### Fixed

- ไอค่อนในกริดหายตอนลาก (drag & drop) — `clearSelection()` ใน `dropEvent`
- ไอค่อน panel หายหลัง reboot — ใช้ icon theme + `launcher_id` แทน path สัมบูรณ์
- hotkey schema ของ Cinnamon (เอกพจน์ `custom-keybinding` + GVariant literal + “แตะ” custom-list) — กดคีย์แล้วทำงานจริง
- popup พังตอนปิด (heap corruption) — ใช้ `deleteLater()` แทนการตั้ง `window=None`
- ไอคอนจาก `.AppImage` — แตก squashfs ดึง `.DirIcon`/`Icon=` จริง

### Removed

- ปุ่ม open-all (เก็บ field `allow_open_all` ไว้ import compatibility)

### Packaging

- **AppImage** — `TaskbarNoob-x86_64.AppImage` · **.deb** — `taskbargroups_0.1.0_amd64.deb`
- ไลบรารี Qt/PySide6 นำมารวมแต่เป็นลิขสิทธิ์แยก (LGPLv3)

## การออกรุ่น

- ขั้นตอน bump → build → tag → Release ดู [`docs/release-process.md`](docs/release-process.md)

[0.2.0]: https://github.com/Neafong/TaskbarNoob/releases/tag/v0.2.0
[0.1.0]: https://github.com/Neafong/TaskbarNoob/releases/tag/v0.1.0