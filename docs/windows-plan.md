# แผน Windows + macOS (Portable ล้วน — ไม่ทำตัวติดตั้ง)

> เป้าหมาย: เอา TaskbarNoob ไปรันที่ออฟฟิศ (Windows) ได้ + เผื่อ macOS · Portable ทั้งคู่
> (config อยู่ข้างแอป ย้ายโฟลเดอร์แล้วยังใช้ได้ — แต่ต้อง "ติดตั้ง launcher ใหม่"
> ทุกครั้งหลังย้าย เพราะ .lnk/.command เก็บ path สัมบูรณ์)
> สถานะโค้ด: W0–W2 เสร็จ · **ทดสอบบน Windows จริงแล้ว (2026-10-19)**

## ⚠️ ข้อจำกัดสำคัญ: Win11 ไม่ให้โปรแกรมปัก taskbar เอง

วิจัย + ทดสอบบนเครื่องจริง (Win11 Home 26H2 build 26300.9711) — **ปิดทุกช่องทาง**
(เอกสาร MS เขียนตรงๆ ว่า *"programmatic pinning by an application is not permitted"*):

| วิธี | ผลลัพธ์ |
|---|---|
| `shutil.copy2` → `User Pinned\TaskBar` | ไฟล์อยู่ แต่ taskbar ไม่แสดง |
| Shell COM `InvokeVerb("pintotaskbar")` | verb ถูกถอด / ถูกเมินเงียบ |
| COM `IPinnedList3::Modify` (วิธีที่ Chromium/Firefox ใช้) | `S_OK` แต่ไม่มีผลจริง |
| API ทางการ `TaskbarManager` | ใช้กับ WinUI/packaged เท่านั้น — Python/Qt เรียกไม่ได้ |

**ต้นฉบับ (Taskbar Groups) ก็ทำไม่ได้** — README บอกให้ user คลิกขวาเอง
(`"2. Click on \"Pin to taskbar\""`) + issue #321 ยืนยันว่าพังบน Win11

### ทำไมเมนู "Pin to taskbar" หายไปเลย
เครื่องที่ไม่มี `LayoutModification.xml` → Win11 (24H2+) ตีความว่า taskbar ถูกล็อก
→ ผู้ใช้ปักเองไม่ได้ **แม้แต่แอปอื่นที่ติดตั้งมา**
(เช็ค: `Test-Path "$env:LOCALAPPDATA\Microsoft\Windows\Shell\LayoutModification.xml"`)

ถ้าอยากปลดล็อก: deploy XML + policy key (ต้องสิทธิ์ admin · explorer กะพริบ 5-15 วิ)
→ ได้เมนู pin กลับมาทั้งเครื่อง · **แต่ไม่จำเป็นกับเรา** เพราะใช้วิธี "ลากวาง" แทน

## W2.5 — เก็บของดีจากซอร์สต้นฉบับ (2026-10-19)

ดาวน์โหลด `v0.2.0.0` มาศึกษา → เก็บ 4 อย่าง (ทำตามต้นฉบับเป๊ะ):

1. **AUMID เฉพาะกลุ่ม** — ฝัง `AppUserModel_ID` ลง `.lnk` (ของเดิมไม่มี)
   · ต้องใช้ COM `IShellLinkW` + `IPropertyStore` (ctypes) เพราะ
     PowerShell `WScript.Shell` ตั้ง AUMID ไม่ได้ → โมดูลใหม่ `core/win32_com.py`
   · ตอนเปิด flyout เรียก `SetCurrentProcessExplicitAppUserModelID` ให้ตรงกัน
   · **ผลข้างเคียงที่ดี:** แต่ละกลุ่มเป็นปุ่ม taskbar แยก ไม่ซ้อนกัน
   · gotcha: `CoCreateInstance` ต้องเรียก `CoInitializeEx` **ก่อน** ไม่งั้นได้ `0x800401F0`
2. **ชื่อ `.lnk` = ชื่อกลุ่ม** (`Game.lnk`) — Windows เอาชื่อไฟล์ไปแสดงบน taskbar
3. **เก็บ `.lnk` ใน `config/shortcuts/`** — portable เหมือนฝั่ง Linux
   (เดิมเก็บใน Start Menu ผู้ใช้ → ไม่ portable)
4. **อ่านสถานะปักจาก AUMID** — ไฟล์ใน `User Pinned\TaskBar` เป็นของ Windows เขียน
   ตอนผู้ใช้ลากวาง → รู้ว่า "ลากแล้วหรือยัง" แม่นกว่าเช็คชื่อไฟล์

### UX ฝั่ง Windows (Linux เหมือนเดิมทุกอย่าง)
- ไอคอน **ตา → โฟลเดอร์** (`folder-fill.svg`) · สีจาง = ยังไม่ลากวาง · เข้ม = อยู่บน taskbar
- ปุ่ม **ไม่ toggle** — คลิกเพื่อเปิดโฟลเดอร์ให้ผู้ใช้ลากวาง
  (toggle มีความหมายเฉพาะ Linux ที่ปัก/ถอนได้จริง)
- **สร้างกลุ่ม → ได้ `.lnk` อัตโนมัติ** (ไม่ต้องกดปุ่มก่อน ไม่งั้น user ไม่มีไฟล์ให้ลาก)
- tooltip อธิบายขั้นตอน + ชื่อไฟล์ที่ต้องลาก

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
2. ทดสอบ CLI: `.\TaskbarNoob.exe --list` — **⚠️ ใช้ไม่ได้** (บิลด์ `--windowed`
   ไม่มี console → ไม่เห็น stdout) · ทดสอบจากซอร์สแทน:
   `.venv\Scripts\python.exe -m taskbargroups --list`
3. **เปิดแอป** → สร้างกลุ่มใหม่
4. **ลากไฟล์** `.exe` / `.lnk` เข้ากริด → ไอคอนต้องขึ้น ✅ (ผ่านแล้ว 2026-10-19)
5. **ปุ่มโฟลเดอร์** → ต้องเปิด Explorer ที่ `config\shortcuts\` พร้อมเลือก `Game.lnk`
   → **ลากไฟล์ไปวางบน taskbar** (Win11 ไม่มีเมนู pin ให้กด)
6. **ตั้ง Hotkey** → ปิดแอป แล้วเปิดใหม่ → กด hotkey → flyout เปิด
7. ลองเปิดโฟลเดอร์/ไฟล์จาก flyout + ดูว่าไอคอนบน taskbar ตรงกลุ่มไหม
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

### ��ͨӡѴ (Windows ��ҹ��)
- **���º� taskbar = ������� `.lnk` �͹������ҡ�ҧ** ? ����¹���͡��������ѧ����
  ���¨������ ��� *rename �����ѡ��������* (Windows ź����駷ѹ��)
   �ҧ��: ��駪��͡�������١**��͹**�ҡ�ҧ ���Ͷ͹�����ҡ����
- **�͹��ش��᷹�����** (Win11 �Դ)  ������ͧ��ԡ��ҷ���ͤ͹�� taskbar �ͧ
- ����� `.lnk` ���ѡ���������� (`repoint_pinned`)  ����¹���͡��������
  �������ѧ�Դ������١��ͧ (������������¹)
