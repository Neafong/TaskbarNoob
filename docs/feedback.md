# Feedback & Backlog — TaskbarNoob (v0.3.0+)

> งานค้าง/ฟีดแบ็กที่ยังไม่ปิด · ประวัติฟีดแบ็กภาค v0.1–v0.2 ถูกเก็บไว้ที่ [`archive/feedback-v0.1-v0.2.md`](archive/feedback-v0.1-v0.2.md)

## งานในรอบ v0.3.0 ✅ ปิดครบแล้ว (2026-11-24)
- [x] **R1:** แยก Platform Backend เข้า `core/platform/{base,linux,win32}` และพับเก็บ `core/macos.py`
- [x] **R2:** แตกไฟล์ยักษ์ (`main_window.py`, `group_editor.py`, `win32.py`) ให้เล็กและมีหน้าที่เดียว
- [x] **R3:** รวม Icon Pipeline เป็นจุดเดียว (ลบ circular import) + ตัวเลือกไอคอนระบบแบบแยกหมวดบน Linux Mint + Steam `steam://rungameid/<appid>` icon resolver ข้าม OS
- [x] **R4:** เก็บกวาด Dead Code / แยก `i18n` (9 ภาษาในตัว) + รีแบรนด์ชื่อภายใน `taskbargroups` → `taskbarnoob` พร้อม Auto-Migration + อัปเดตเครดิตเป็น `Noob & Jenny` + แก้บั๊ก `zh_CN`/`pt_BR` ข้าม OS

## งานในรอบ v0.4.0 — Quality-of-Life & Resilience ✅ ปิดครบฝั่งโค้ด & เทสต์ Mint (2026-11-24 · รอเทสต์/build ฝั่ง Win 11)
- [x] **System Tray Icon** — เปิด/ปิดได้ในหน้าต่าง Settings (`minimize_to_tray`, เมนูคลิกขวาเรียบง่ายมี เปิดหน้าต่าง / ตั้งค่า... / ออก, ช่วยให้ Win32 Global Hotkeys ทำงานต่อเนื่องเมื่อพับหน้าต่าง)
- [x] **`.url` Resilience + แคชไอคอน `.url→.exe` (3A)** — แตก `URL=` เก็บเป็น target ตรงๆ + แคชไอคอนจาก `IconFile=` (รวม `.exe` เช่นเกม Epic) / Steam `librarycache` ลงกลุ่ม เพื่อให้ลบไฟล์ `.url` บน Desktop ได้โดย Flyout ไม่พัง + รองรับ URI `://` ใน `_launch_linux`
- [x] **ปุ่ม "ดึงไอคอนใหม่" (Re-detect Icon — 3B)** — กดรีเฟรชไอคอนจาก target ในหน้าแก้ไข shortcut / คลิกขวาในกริด ไม่ต้องลบแล้วแอดใหม่
- [x] **เลือกหลายแอปพร้อมกันใน "จากแอป..." (Multi-select — 3C)** — `AppPickerDialog` รองรับ Ctrl/Shift เลือกหลายรายการทีเดียว
- [x] **เตือนเบาๆ เมื่อ shortcut ชี้ไฟล์ที่หายไปแล้ว (Broken Target — 3D)** — แสดงเงียบๆ เฉพาะตอนเปิดโปรแกรมเรา (ใน `GroupEditor` / `ShortcutDialog`) ห้ามเด้ง popup หรือ notification พลการ
- [x] **แก้ wording `Cinnamon` ใน `SettingsDialog` (`settings.theme_hint`)** — ปรับเป็นคำกลาง (`system theme` / `ธีมของระบบ`) ครบ 9 ภาษา + ล็อกกฎตั้งชื่อไฟล์ Release มีเลขเวอร์ชันทุกแพลตฟอร์ม & auto-zip ใน `build_windows.ps1`

## รายการค้างระยะยาว (หลัง v0.4.0)
- **ไอคอน default ของกลุ่มที่ไม่ได้ตั้งไอคอน:** ปัจจุบันใช้ไอคอนโฟลเดอร์จากธีมระบบ (พี่ยังไม่ตัดสินใจว่าจะเปลี่ยนเป็นโลโก้แอปไหม — คงเดิมไว้ก่อน)
- **Linux DE / Display อื่น:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่นนอกเหนือจาก Cinnamon
- **macOS:** พับเก็บโค้ดออกก่อน — กลับมาพิจารณาเมื่อมีเครื่อง Mac จริงสำหรับพัฒนาและทดสอบ
- **คลิกขวา shortcut ใน flyout:** พักไว้ก่อน รอฟีดแบ็กจากผู้ใช้จริง
- **Windows `--list` จาก exe:** build เป็น `--windowed` ไม่มี stdout console — พิจารณาภายหลังถ้าจำเป็น
- **Windows `shell:AppsFolder` scan ใน "จากแอป...":** พิจารณาเพิ่มภายหลังถ้าผู้ใช้เจอแอป Store/MSIX ที่ไม่มี `.lnk` ใน Start Menu
