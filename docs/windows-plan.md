# แผน Windows + macOS (Portable ล้วน — ไม่ทำตัวติดตั้ง)

> เป้าหมาย: เอา TaskbarNoob ไปรันที่ออฟฟิศ (Windows) ได้ + เผื่อ macOS · Portable ทั้งคู่
> (config อยู่ข้างแอป ย้ายโฟลเดอร์แล้วยังใช้ได้ — แต่ต้อง "ติดตั้ง launcher ใหม่"
> ทุกครั้งหลังย้าย เพราะ .lnk/.command เก็บ path สัมบูรณ์)
> สถานะโค้ด: W0–W2 ทำแล้ว (ยัง**ไม่ได้รันบน Windows/macOS จริง** — รอเทสต์ที่ออฟฟิศ)

## W0 — สำรวจ (เสร็จ)

- ผูก Linux อยู่ 5 จุด: `desktop.py` (.desktop) · `panel.py` (Grouped Window List)
  · `hotkeys.py` (gsettings) · `icons.py` (AppImage/.desktop) · `launcher.py`
  (มี `_launch_windows/_launch_macos` อยู่แล้ว)
- GUI เรียกผ่านชื่อฟังก์ชันเดิมได้เลย — ชั้น dispatch ใหม่ชื่อเหมือนเดิม
  (`launchers.py`/`taskbar.py`) → diff ฝั่ง GUI เหลือแค่ import + branch เล็ก ๆ

## W1 — core ข้าม OS (เสร็จ — เทสต์ด้วย mock บน Linux)

- `core/win32.py`: สร้าง/อ่าน `.lnk` ผ่าน PowerShell (`WScript.Shell` ไม่ต้องลงอะไรเพิ่ม)
  · โฟลเดอร์ Start Menu + User Pinned · `parse_hotkey_binding` (`<Control><Alt>t` → MOD/VK)
  · `RegisterHotKey/UnregisterHotKey` ผ่าน ctypes
- `core/macos.py`: launcher `.command` (+x) · ปัก/ถอน Dock ผ่าน `defaults` + `killall Dock`
- `core/launchers.py`: `install/remove_launcher`, `launcher_file_name`
  (.desktop/.lnk/.command ตาม OS — GUI ใช้ชื่อเดิม `desktop_file_name` ได้)
- `core/taskbar.py`: `pin/unpin/is_pinned/pinned_*` ชื่อเดิม ส่งงานต่อตาม OS
- `core/settings.py`: เก็บ `{slot: binding}` ใน `settings.json` (Windows ไม่มีที่เก็บของระบบ)
- `gui/win32_hotkey.py`: `HotkeyRegistry` + `WinHotkeyFilter` (WM_HOTKEY → เปิด flyout
  ผ่านโปรเซสใหม่ `exe --open <dir>` — single-instance เดิมจัดการต่อ)
- `gui/icons.py`: `shortcut_icon` + `cache_provider_icon` ใช้ `QFileIconProvider`
  ดึงไอคอน `.exe/.lnk/.app` จาก OS (display + แคชพกพา)
- `gui`: `main_window` (import + unregister + inline hotkey + ลงทะเบียนตอนบูต),
  `hotkey_dialog` (branch win32), `_sync_pinned_launchers` ข้ามถ้าไม่ใช่ Linux

## W2 — build + เทสต์ที่ออฟฟิศ (ถัดไป — ทำบนเครื่อง Windows)

1. ลง Python 3.11+ (python.org, ติ๊ก Add python to PATH) + `pip install PySide6 pyinstaller`
2. โคลน repo → รัน `powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1`
   → ได้ `dist\TaskbarNoob\TaskbarNoob.exe` (portable ทั้งโฟลเดอร์)
3. คัดลอกโฟลเดอร์ `dist\TaskbarNoob` ไปที่ใช้งาน (เช่น `D:\Tool\TaskbarNoob`)
4. รัน `TaskbarNoob.exe --list` ใน PowerShell (ควรเห็นรายชื่อกลุ่ม — config อยู่ข้าง exe)
5. เปิดแอป → สร้างกลุ่ม → ลาก `.exe/.lnk` ใส่ → ตรวจไอคอนขึ้น
6. กดตา (ปัก) → ตรวจ `.lnk` โผล่ใน Start Menu + taskbar (Win11 อาจต้องคลิกขวา Pin เอง)
7. ตั้ง hotkey → ปิดแอป เปิดใหม่ → กด hotkey → flyout ต้องเปิด (ลงทะเบียนใหม่ตอนบูต)
8. จดบั๊กกลับมา (ถ่ายรูป + ข้อความ error ถ้ามี)

## W3 — macOS (ยังไม่เริ่ม — ต้องมีเครื่อง Mac)

- build: `pip install pyinstaller` บน Mac → `pyinstaller --windowed --name TaskbarNoob ...`
  (ได้ `TaskbarNoob.app` — วางข้าง `config/`)
- `paths.app_dir()` ยังชี้ข้าง exe (ใน `.app/Contents/MacOS`) — ถ้าอยาก portable ข้าง `.app`
  ให้ปรับเพิ่ม (งานเล็ก)
- เทสต์: `.command` ดับเบิลคลิก · Dock pin · ไอคอน `.app`

## ข้อจำกัดที่รู้แล้ว (alpha)

- ย้ายโฟลเดอร์แอปแล้ว `.lnk/.command` เก่าใช้ไม่ได้ → ติดตั้ง launcher ใหม่ (มีปุ่มอยู่แล้ว)
- ปัก taskbar Win11 อาจถูกบล็อก → แ fallback: ปักจาก Start Menu เอง (คลิกขวา → Pin to taskbar)
- hotkey ชนกับโปรแกรมอื่น → `RegisterHotKey` ล้มเหลว จะมีกล่องเตือน (เปลี่ยนปุ่มใหม่)
- ไอคอน `.exe` บางตัวดึงไม่ได้ (packer แปลก ๆ) → ตั้งรูปเองได้เหมือนเดิม
