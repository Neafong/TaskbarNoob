# Roadmap — TaskbarNoob

> แผนภาพรวมทุกเฟส + สถานะ · อัปเดตล่าสุด: 2026-10-12
> **เริ่มงานชุดใหม่ในเซคชั่นใหม่เสมอ** — อ่าน `../AGENTS.md` (snapshot) + ไฟล์นี้ + ไฟล์ plan ของเฟสนั้นก่อนลงมือ
> ฟีดแบ็ก/งานค้าง: [`feedback.md`](feedback.md) · ประวัติงาน: [`WORKLOG.md`](WORKLOG.md)

## ภาพรวม

เป้าหมาย: แอปจัดกลุ่ม shortcut แล้วกดครั้งเดียวเปิดทั้งกลุ่ม — **Linux Mint (Cinnamon) เป้าหลัก, Windows เป้ารอง**
- สถานะ: **v0.1.0 ขึ้น GitHub แล้ว (2026-10-12)** — Phase 18 เสร็จ · v0.2-A (ตัด importer Windows) เสร็จ · 221 เทสต์ · build ผ่าน
- repo: **github.com/Neafong/TaskbarNoob** (Public) · License **GPL-3.0-or-later** · Release แนบ AppImage + `.deb`

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

## งานถัดไป (หลัง v0.1.0)

1. **เก็บฟีดแบ็กผู้ใช้จริง** — รอคนลอง v1 ใช้แล้วส่ง feedback (ดู `docs/feedback.md`)
2. **งานค้างที่ยังเทสต์ไม่ได้บนเครื่องนี้:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น (hotkey/pin = Cinnamon-only)
3. **v0.2 — "กระเป๋าใส่ได้ทุกอย่าง" (⭐ ล็อกดีไซน์แล้ว):** ลากไฟล์/โฟลเดอร์อะไรก็ได้เข้ากลุ่ม (F7 ทำแล้ว) ·
   เพิ่มใน **Flyout**: คลิกไอค่อน = เปิดด้วยโปรแกรม Default (type-aware: `gio open`) · คลิกขวา = เปิดที่อยู่ (โฟลเดอร์แม่)
   — รายละเอียดรอบ #18 ใน `docs/feedback.md`
4. **v0.2 — cleanup: ตัดฟีเจอร์ "นำเข้ากลุ่ม (Windows)" ออกทั้งชุด (⭐ ล็อกข้อตัดสินใจแล้ว):**
   ลบปุ่ม + `core/importer.py` + CLI `--import` + เทสต์ + i18n keys · เหลือ "นำเข้าทั้งหมด" ปุ่มเดียวจบ
   — รายละเอียด + เช็กลิสต์รอบ #19 ใน `docs/feedback.md`
5. **v0.2 — UI polish (⭐ ล็อกแนวทางแล้ว):** เคอร์เซอร์ลากกลุ่ม = ลูกศร 4 ทิศ `Qt.SizeAllCursor` ↕️↔️ (แก้ 🚫) ·
   accent token กลาง + ไฮไลท์แถวโปร่งแสง + คุมสี light theme · **ไอคอนปุ่ม SVG solid ของเราเอง (tint ตามธีม)** ให้ทั้งหน้าหลัก + ตัวแก้ไข
   — รายละเอียดรอบ #20 ใน `docs/feedback.md`
6. **Windows port** — ผู้ใช้ตัดสิน 2026-10-12: **เขียน Linux ให้จบก่อน · Windows = พร้อมรุ่นถัดไป หลังรวมฟีดแบ็กครบ**
   (เฟส W0–W5 ข้างล่าง · รายละเอียด `docs/windows-plan.md` — ยังไม่เริ่ม)
7. **macOS (อนาคต — หลัง Windows):** ศึกษาตลาดแล้ว (คู่แข่งใกล้สุด = DockGroups) · จุดได้เปรียบ = portable config + ฟรี/GPL + ฟอร์แมตข้าม OS
   · ติดที่ยังไม่มีเครื่อง Mac ทดลอง (ใช้ GitHub Actions macOS runner รันเทสต์ `core/` ได้) — รอบ #21 ใน `docs/feedback.md`
8. ฟีเจอร์อื่นตามฟีดแบ็ก

## แผน Windows (งานอนาคต)

ย่อ — W0 spike ตรวจ reuse → W1 core platform backends → W2 tray + global hotkey + flyout (MVP) → W3 taskbar/pin launcher → W4 packaging `.exe` + installer → W5 เทสต์ Win10/11 + release
> `core/` + `gui/` (Qt) ข้าม OS ได้เยอะ · ต้องทำใหม่: ไอคอน (.exe/.lnk/.ico), hotkey (`RegisterHotKey`), `.lnk`, admin, packaging

## กระบวนการออกรุ่น

ดู [`release-process.md`](release-process.md) — bump version → CHANGELOG → build → tag → Release