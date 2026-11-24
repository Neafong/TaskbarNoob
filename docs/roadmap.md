# Roadmap — TaskbarNoob

> แผนภาพรวมทุกเฟส + สถานะ · อัปเดตล่าสุด: 2026-11-24
> **เริ่มงานชุดใหม่ในเซคชั่นใหม่เสมอ** — อ่าน `../AGENTS.md` (snapshot) + ไฟล์นี้ + ไฟล์ plan ของเฟสนั้นก่อนลงมือ
> ฟีดแบ็ก/งานค้าง: [`feedback.md`](feedback.md) · ประวัติงาน: [`WORKLOG.md`](WORKLOG.md)

## ภาพรวม

เป้าหมาย: แอปจัดกลุ่ม shortcut แล้วกดครั้งเดียวเปิดทั้งกลุ่ม — **Linux Mint (Cinnamon) เป้าหลัก, Windows 11 (portable) เป้ารอง**
- **v0.1.0:** ขึ้น GitHub แล้ว (2026-10-12) — Linux Mint AppImage + `.deb` · GPL-3.0-or-later
- **v0.2.0 (ปล่อยแล้ว 2026-11-23):** รองรับ Linux Mint + Windows 11 (portable `TaskbarNoob.exe`, AUMID แยกต่อกลุ่ม/แอป, Hotkey Win32, multi-res `.ico`, MSIX/WindowsApps icon, Flyout เงามุมโค้ง, ตัวเลือกไอคอนระบบ 2 แหล่ง)
- **v0.3.0 (โค้ด & เทสต์เสร็จครบ 2 OS — รอฝั่ง Mint rebuild + tag Release):** **ปรับปรุงโครงสร้างโค้ดใหม่ทั้งหมด (Full Architecture Refactor) + รีแบรนด์ `taskbarnoob` + 9 ภาษา + ปุ่ม "จากแอป..." + Steam/ASAR/Flatpak icons**
- **v0.4.0 (วางแผนแล้ว — เริ่มหลังปล่อย `v0.3.0`):** **Quality-of-Life & Resilience** (System Tray Icon · `.url` Resilience · แคชไอคอน `.url→.exe` · ปุ่มดึงไอคอนใหม่ · Multi-select "จากแอป..." · เตือน target หายแบบเงียบเฉพาะตอนเปิดแอป)
- repo: **github.com/Neafong/TaskbarNoob** (Public) · License **GPL-3.0-or-later**

## เฟสที่ทำแล้ว (Linux — Cinnamon)

`[x]` เสร็จ

- `[x]` P0 Brainstorm/สเปก · `[x]` P1 data model + โครงไฟล์
- `[x]` P2 MVP (จัดการกลุ่ม + grid + เปิดแอป)
- `[x]` P3 panel (`.desktop` launcher + hotkey)
- `[x]` P4 เก็บงาน: cache ไอคอน, ธีม/opacity/open-all, importer จาก Windows
- `[x]` P5 Packaging: AppImage + `.deb` (PyInstaller → appimagetool / dpkg-deb)
- `[x]` P6 Settings & Flyout polish (slider opacity/ขนาดไอคอน · flyout โปร่งแสง · dblclick แก้ไข · จัดปุ่ม + เฟือง Setup · ปุ่มปักหมุด)
- `[x]` P7 Shortcut editor เป็น Grid + drag & drop + reorder
- `[x]` P8 UI polish รอบ 2 (Pin ต่อแถว · สลับลำดับกลุ่ม · ไอคอน grid ใหญ่+ดึงจริง · รวมสี · พิมพ์ตัวเลขได้)
- `[x]` P9 Cinnamon panel: ปักหมุดจริง (Grouped Window List) + คลิกเปิด flyout
- `[x]` P10 Pin toggle (ปัก/ถอน) + โชว์สถานะปักบนแถวกลุ่ม
- `[x]` P11 Repackage: rebuild AppImage + `.deb` (Phase 8/9/10)
- `[x]` P12 Fix F16–F18: extract ไอคอนใน AppImage + ลากสลับลำดับกลุ่มบันทึกจริง + ไอคอนไม่เล็ก
- `[x]` P13 Repackage: rebuild AppImage + `.deb` (รวม Phase 12)
- `[x]` P14a Flyout UX: single-instance ข้าม process + ตำแหน่งกึ่งกลางเมาส์ + ปิดเมื่อคลิกที่อื่น (F19/F20)
- `[x]` P14b Grid drag UX: แก้ตำแหน่งปล่อย + ไฮไลท์ช่องเป้าหมาย (custom — Qt IconMode ไม่เวิร์ก) (F21/F22)
- `[x]` P14c Theme (light/dark/auto) + Settings dialog จากปุ่มเฟือง (F23/F24)
- `[x]` P14d Repackage: rebuild AppImage + `.deb` (Phase 14) แล้วให้ผู้ใช้ทดสอบ
- `[x]` P15a Fix B1: ลากในกริดไอค่อนหาย (Qt `clearOrRemove` — แก้ `clearSelection`) + เทสต์
- `[x]` P15b GroupEditor UI: ลบ labels เดิม · พรีวิวแถวเดียวกับปุ่ม · ปุ่มเลือกไอค่อนระบบ · สไลด์เดอร์คุมกริด
- `[x]` P15c Width compact: label "แถว" + ย้ายแถวเดียวกับชื่อกลุ่ม
- `[x]` P15d i18n: ไทย/Eng + `config/lang` JSON + สลับ/ส่งออก/นำเข้าภาษา
- `[x]` P15e Repackage: rebuild AppImage + `.deb` แล้วให้ผู้ใช้ทดสอบ
- `[x]` P16a Auto-refresh ไอค่อน Taskbar หลังแก้กลุ่ม (N1): `_refresh_pinned_icon` + 182 เทสต์
- `[x]` P16b ✅ U3 = **ตาเปิด/ปิด** · P16c ✅ U1 เฟืองใหญ่ + U2 สีธีม-aware + tooltip แสดง/ซ่อน (184 เทสต์)
- `[x]` P16d Repackage (รวม 16a–16c): AppImage (61M) + `.deb` (51M) 01:57 · boot/PYZ ตรวจแล้ว
- `[x]` P16e ✅ U4 เฟือง 28px + U5 ตั้ง app/window icon (186 เทสต์)
- `[x]` P19 Rebrand ✅: ชื่อแสดง = **"TaskbarNoob"** (คง APP_ID `taskbargroups` — พิน/config ไม่พัง)
  · ไอค่อนใหม่จาก `packaging/assets/Logo TG.svg` (`render_icon.py` rasterize → png) · รวม build กับ 16e (04:02–04:03)
- `[x]` P17a Context menu กลุ่ม (คลิกขวา: เปิด/แก้ไข/ปัก-ถอน/hotkey/ทำสำเนา/ลบ) · `[x]` P17d Duplicate (`ConfigStore.duplicate_group`)
- `[x]` P17b hotkey ข้างชื่อ (อ่าน gsettings custom-list + binding → `cinnamon_to_display`) + **ถอนคีย์ลัด** (ปุ่มใน dialog · ลบกลุ่ม = ลบคีย์) · `[x]` P17f Credits "Noob & Pickle" (Settings + About dialog + appdata)
  · เอาปุ่มซ้ำ "ติดตั้ง launcher"/"ตั้ง hotkey" ออกจากเฟือง ⚙ (ใช้คลิกขวาต่อกลุ่มแทน — กันสับสนว่าตั้งให้กลุ่มบนสุด)
- `[x]` P17e Repackage ✅ (2026-10-11 12:47): AppImage (61M) + `.deb` (51M) · PYZ ตรวจ symbol ใหม่ครบ (รวม hotkey fix) · `dist/config` intact
- `[x]` P18 Import/Export ทั้งชุด config (zip/zip) + repackage สุดท้าย ✅ รอบ #15

## การตัดสินใจที่เคยตัด/พัก

- **P17c ค้นหา/กรอง** — ตัดออก (ผู้ใช้ตัดสิน 2026-10-11)
- **open-all** — ตัดปุ่ม เก็บ field `allow_open_all` ไว้ import compat (รอบ #10)
- **คลิกขวา flyout** — พักไว้ก่อน
- **Windows** — เป้ารอง รอเฟสหลัง (ดู [แผน Windows](#แผน-windows-งานอนาคต) ด้านล่าง)

## งานถัดไป: แผน v0.3.0 — รื้อโครงสร้างใหม่ทั้งหมด (ยึดฟีเจอร์เดิมเป็นแกน)

> **หลักการสำคัญ:** ไม่เพิ่มฟีเจอร์ฟุ่มเฟือย แต่ล้างหนี้เทคนิค/กลิ่น AI Slop ที่สะสมจากการแก้หลายรอบหลายโมเดล
> **ลำดับการทำงาน:** จัดระเบียบ `docs/` เป็นอย่างแรก (R0) → รื้อและวางโครงสร้างใหม่บน **Linux Mint (ต้นทาง)** ให้เรียบร้อยและเทสต์ผ่านครบก่อน → แล้วค่อยนำโครงสร้างเดียวกันมาปรับฝั่ง **Windows** ให้เข้าชุดกัน

### R0 — จัดระเบียบเอกสาร (`docs/`) เป็นอย่างแรกก่อนเริ่มรื้อโค้ด ✅ เสร็จ (2026-11-23)
- ย้ายแผนเก่าที่ปิดจบแล้ว (`phase18-plan.md`, `windows-plan.md`) และ log เก่ายาวๆ (`WORKLOG.md`, `feedback.md`) แยกภาค `v0.1–v0.2` ลง `docs/archive/` แล้วเริ่ม `WORKLOG.md` / `feedback.md` ชุดใหม่ให้สั้นเบา ประหยัด token
- อัปเดต `docs/README.md`, `docs/team.md` (สะท้อนการทำงานร่วมกับเจนนี่แทนทีม OpenCode เดิม) และ `AGENTS.md` ให้ตรงกับสถานะล่าสุด + แก้บั๊ก `storage._prune_order()` ให้เทสต์ Mint เขียว 100%

### R1 — Platform Backend แยกขาดชัดเจน (`core/platform/`) ✅ เสร็จ (2026-11-23)
- ยุบไฟล์เฉพาะ OS ที่กระจัดกระจาย (`desktop.py`, `panel.py`, `hotkeys.py`, `taskbar.py`, `launchers.py`, `win32.py`, `win32_com.py`) เป็นแพ็กเกจ `core/platform/`:
  - `base.py` — กำหนด interface กลาง (launcher, taskbar/pin, hotkey, reveal/open, icon source)
  - `linux/` — backend ของ Linux Mint (Cinnamon)
  - `win32/` — แตก `win32.py` (802 บรรทัด) เป็นโมดูลย่อยตามหน้าที่ (`lnk.py`, `ico.py`, `hotkey.py`, `aumid.py`, `com.py`)
- ลด `if sys.platform == ...` ในฝั่ง `gui/` (เดิมกระจายกว่า 40 จุด เฉพาะ `main_window.py` มี 17 จุด) ให้เหลือเฉพาะจุดที่จำเป็นจริง
- **พับเก็บ `core/macos.py` ออกไปก่อน** (ยังไม่มีเครื่อง Mac สำหรับพัฒนาและทดสอบจริง — ค่อยเพิ่มกลับมาเมื่อพร้อม)

### R2 — แตกไฟล์ยักษ์ให้เล็กและมีหน้าที่เดียว (Modular GUI & Core) ✅ เสร็จ (2026-11-23)
- **ไฟล์ไหนย่อยได้ให้ย่อย** — ไม่ปล่อยให้มีไฟล์ 1,000+ บรรทัดที่รวมทุกอย่างไว้ด้วยกัน:
  - แตก `gui/group_editor.py` (1,151 บรรทัด) → `shortcut_grid.py`, `shortcut_dialog.py`, `icon_picker.py`, `group_editor.py`
  - แตก `gui/main_window.py` (1,199 บรรทัด) → แยก `group_list.py` (`GroupListWidget` + delegate), logic การ sync/persist ออกจากตัวหน้าต่างหลัก
  - ตรวจไฟล์อื่นใน `core/` และ `gui/` ที่มีหลายหน้าที่ปนกันให้ย่อยตามความเหมาะสม

### R3 — รวมระบบไอคอนเป็น Pipeline เดียว + รองรับ Steam ข้าม OS ✅ เสร็จ (2026-11-23)
- รวมโค้ดดึง/แคชไอคอนที่กระจายอยู่ 3 ไฟล์ (`core/icons.py`, `gui/icons.py`, `gui/group_editor.py`) ให้เป็น pipeline เดียวที่ชัดเจน
- ลบ circular lazy import (`gui/icons.py` → `from .group_editor import _cached_provider_png`) และค่าคงที่ `_PROVIDER_ICON_CACHE_DIRNAME` ที่ประกาศซ้ำ
- เพิ่ม **ตัวเลือกไอคอนจากระบบแบบแยกหมวดบน Linux Mint (`icon_picker.py`)** ให้เหมือนฝั่ง Windows — ใช้โครงสร้างหมวดของ Freedesktop (`/usr/share/icons/<theme>/`):
  - **หมวดหมู่ & โฟลเดอร์ (`categories` / `places`)** — ค่าเริ่มต้น เหมาะตั้งเป็นไอคอนกลุ่ม
  - **แอปที่ติดตั้ง (`apps`)**
  - **ทั้งหมด** (แทนการกวาดทุกหมวดมารวมกองเดียว 4,000 รูปแบบเดิม)
- เพิ่ม **Steam `steam://rungameid/<appid>` icon resolver** ใน `core/` ให้ใช้ได้ทั้ง 2 ฝั่งพร้อมกัน:
  - **Linux Mint:** อ่าน `steam://rungameid/<appid>` จาก `.desktop` แล้ว fallback หาไอคอนใน `~/.local/share/Steam/appcache/librarycache/`
  - **Windows:** อ่าน `steam://rungameid/<appid>` จาก `.url` (กรณี `IconFile=` ว่าง/พัง) แล้วอ่าน `SteamPath` จาก Registry ไปดึงไอคอนจาก `appcache\librarycache\`

### R4 — เก็บกวาด Dead Code, i18n และเทสต์ ✅ เสร็จ (2026-11-23)
- ลบโค้ด/คอมเมนต์ PowerShell เก่าที่ไม่ได้ใช้งานจริงแล้วในฝั่ง Windows
- พับเก็บ `core/macos.py` (และเทสต์/branch ที่อ้างถึง) ออกไปก่อนตามข้อตกลง
- ปรับ `core/i18n.py` (582 บรรทัด) ให้ดูแลง่ายขึ้น (แยกตารางคำแปลออกจาก logic โหลดภาษา)
- **รีแบรนด์ชื่อภายในทั้งหมดจาก `taskbargroups` → `taskbarnoob`:**
  - เปลี่ยนชื่อแพ็กเกจ Python (`taskbargroups/` → `taskbarnoob/`), ชื่อแพ็กเกจ `.deb` (`taskbarnoob_0.3.0_amd64.deb` พร้อมใส่ `Replaces:`/`Conflicts: taskbargroups` ใน `DEBIAN/control`), `APP_ID`, `.desktop`, hicolor icon, hotkey slot, Windows AUMID และ env `TASKBARNOOB_CONFIG` (รองรับ fallback `TASKBARGROUPS_CONFIG` เก่า)
  - ออกแบบ migration ตอนเปิดแอปครั้งแรก (self-heal/อัปเกรด launcher/hotkey เก่า) ไม่ให้กลุ่มที่ปักไว้พัง
- **อัปเดตเครดิต (Credits) เป็น "Noob & Jenny (เจนนี่)":** เปลี่ยนจาก `Noob & Pickle` (น้องพริก) เป็น `Noob & Jenny` ในหน้าต่าง Settings, About dialog, `i18n` (TH/EN/JA), `.appdata.xml` และ `README.md`
- ตรวจชุดเทสต์ให้ครอบคลุมโครงสร้างใหม่ และรันเขียว 100% ทั้งบน Mint และ Windows

### งานถัดไป: แผน `v0.4.0` — Quality-of-Life & Resilience (ล็อกขอบเขตชัด — เริ่มหลังปล่อย `v0.3.0`)

> **หลักการคุมขอบเขต:** เก็บเฉพาะจุดเจ็บจริงจากการใช้งานและคุณภาพชีวิต ไม่เพิ่มฟีเจอร์ฟุ่มเฟือย เพื่อให้รุ่นนี้จบไวและเสถียรครบทั้ง 2 OS
> **ก่อนปิดรุ่นทุกครั้ง:** ต้องผ่าน **Docs Audit Checklist** ใน [`release-process.md`](release-process.md)

1. **System Tray Icon (เปิด/ปิดได้ในหน้าต่าง Settings — ข้าม OS):**
   - เพิ่ม setting `minimize_to_tray: bool = False` (ค่าเริ่มต้นปิด เพื่อไม่เปลี่ยนพฤติกรรมเดิมแบบเซอร์ไพรส์ผู้ใช้) + ช่องติ๊กใน `SettingsDialog` (แปลครบ 9 ภาษา)
   - ใช้ `QSystemTrayIcon` พร้อมไอคอน `app_window_icon()` — เมื่อเปิดโหมด Tray กด `X` จะซ่อนหน้าต่างหลักลง Tray แทนการปิดแอป (ทำให้ Win32 Global Hotkeys ทำงานต่อเนื่องได้แม้พับหน้าต่าง!)
   - เมนูคลิกขวาแบบ **เรียบง่ายแต่ครบมือ:** **เปิด TaskbarNoob** (default) · **ตั้งค่า... (Settings)** (กดเปลี่ยนภาษา/ธีม/ปิด Tray ได้จากตรงนี้เลยโดยไม่ต้องเปิดหน้าต่างหลักก่อน) · เส้นคั่น · **ออก (Quit)** · คลิกซ้าย/ดับเบิลคลิก = เปิดหน้าต่างหลัก
2. **`.url` Resilience + แคชไอคอน `.url → .exe` (3A):**
   - เพิ่ม `parse_url_file(path) -> (url, icon_file)` ใน `core/`
   - เมื่อผู้ใช้ลากหรือเลือกไฟล์ `.url` เข้ากลุ่ม:
     1. ดึงและแคชไอคอนจาก `IconFile=` (รวม `.exe`/`.ico` เช่นเกม Epic Games `River City Girls 2` ผ่าน `extract_os_icon_png`) หรือ Steam `librarycache` ลง `config/groups/<group>/icons/` ให้ครบก่อน
     2. แตกค่า `URL=` (เช่น `steam://rungameid/544630`, `com.epicgames.launcher://...`, `https://...`) มาเก็บเป็น `target` โดยตรง → **ลบไฟล์ `.url` บน Desktop ทิ้ง Flyout ก็ยังเปิดเกมและโชว์ไอคอนได้ปกติ 100%**
   - อัปเดต `core/launcher.py` (`_launch_linux`): ส่ง URI ที่มี `://` (เช่น `steam://`, `https://`) เข้า `gio open` / `xdg-open` แทนการส่งเข้า `subprocess.Popen` ตรงๆ
3. **ปุ่ม "ดึงไอคอนใหม่" (Re-detect Icon — 3B):**
   - เพิ่มปุ่มเล็กๆ ใน `ShortcutDialog` (และเมนูคลิกขวาในกริดของ `GroupEditor`) ให้ดึงไอคอนจาก `target` ใหม่แล้วทับแคชเดิมในคลิกเดียว ไม่ต้องลบแล้วแอดใหม่เวลาไอคอนเก่าพังหรืออัปเกรดเวอร์ชัน
4. **เลือกหลายแอปพร้อมกันใน "จากแอป..." (Multi-select — 3C):**
   - เปลี่ยน `AppPickerDialog` จาก `SingleSelection` เป็น `ExtendedSelection` (กด Ctrl/Shift เลือกหลายแอปทีเดียวแล้วเพิ่มเข้ากลุ่มครบในรอบเดียว)
5. **เตือนเบาๆ เมื่อ shortcut ชี้ไฟล์ที่หายไปแล้ว (Broken Target — 3D):**
   - **เงื่อนไขสำคัญ:** แสดงเฉพาะตอนผู้ใช้เปิดโปรแกรมเราเท่านั้น (เช่น สัญลักษณ์/tooltip เตือนเงียบๆ ใน `GroupEditor` / `ShortcutDialog`) **ห้ามเด้ง popup หรือ OS notification พลการ** ให้รำคาญผู้ใช้

### งานค้างระยะยาว (หลัง v0.4.0)
- **Linux DE / Display อื่น:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่นนอกเหนือจาก Cinnamon
- **macOS:** กลับมาพิจารณาเมื่อมีเครื่อง Mac สำหรับพัฒนาและทดสอบจริง
- ฟีเจอร์อื่นตามฟีดแบ็กผู้ใช้ (ดู [`feedback.md`](feedback.md))

## กระบวนการออกรุ่น

ดู [`release-process.md`](release-process.md) — bump version → Docs Audit Checklist → test & build (Mint + Win 11) → tag → Release