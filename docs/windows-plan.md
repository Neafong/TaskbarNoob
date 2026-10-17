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

## W2 — ทำงานบนเครื่อง Windows (ลำดับ 1 → 3 แบบสั้น ๆ)

### 1. เตรียมเครื่อง
1. ติดตั้ง [Python 3.11+](https://www.python.org/) → **ต้องติ๊ก "Add python.exe to PATH"**
2. เปิด Windows Terminal (PowerShell)
3. ลงเครื่องมือ Git ถ้ายังไม่มี (หรือใช้ Git for Windows)

### 2. โคลน repo แล้ว build
1. **โคลน:** `git clone git@github.com:Neafong/TaskbarNoob.git` (หรือ HTTPS: `https://github.com/Neafong/TaskbarNoob.git`)
2. `cd TaskbarNoob`
3. **Build portable:** `powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1`
4. รอจนจบ → ได้โฟลเดอร์ `dist\TaskbarNoob\TaskbarNoob.exe`

### 3. ทดสอบ (เช็กลิสต์)
1. คัดลอกทั้งโฟลเดอร์ `dist\TaskbarNoob` ไปใช้งาน เช่น `D:\Tool\TaskbarNoob\` (ย้ายได้)
2. ทดสอบ CLI: `.\TaskbarNoob.exe --list` (ควรเห็นรายชื่อกลุ่มจาก `config/` ข้าง exe)
3. **เปิดแอป** → สร้างกลุ่มใหม่
4. **ลากไฟล์** `.exe` / `.lnk` เข้ากริด → ไอคอนต้องขึ้น
5. **ปักหมุด (ตา)** → `.lnk` โผล่ Start Menu (Win11 อาจต้องคลิกขวา Pin to taskbar เอง)
6. **ตั้ง Hotkey** → ปิดแอป แล้วเปิดใหม่ → กด hotkey → flyout เปิด
7. ลองเปิดโฟลเดอร์/ไฟล์จาก flyout (ถ้าใช้ AppImage/DE อื่นไม่เกี่ยว แต่ฝั่ง Windows ลองเช็ค context/reveal ได้บ้าง)
8. **จดบั๊ก**: ถ้ามี error → เก็บ screenshot + error text

### 4. จบ release (ถ้าไม่เจอบั๊ก)
1. ถ้าเทสต์ผ่านทั้งหมด → **zip** โฟลเดอร์ `TaskbarNoob` (เช่น `TaskbarNoob-Windows-0.2.0.zip`) แล้วแนบลง **draft Release** เดิมที่พี่เคย save
2. **Save Draft** → ถ้าแน่ใจจะแจก → **Publish release**
3. ถ้าเจอ**บั๊กเล็กน้อย** → แก้โค้ดบน Windows (หรือ clone กลับมาแก้บน Linux) → `powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1` ใหม่ → ทดสอบ → อัปเดตไฟล์ zip ใน draft → Save Draft → publish
4. ถ้าแก้ต้องอัปเดตโค้ด + tests → ทำเหมือนปกติ: แก้ → `.venv/bin/python tests/run.py` ผ่าน → commit + push → rebuild Linux (.deb/.AppImage) ด้วย + rebuild Windows → อัปเดต draft → publish (หรือ bump version ตาม `release-process.md` ถ้ามีความเหมาะสม)

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
