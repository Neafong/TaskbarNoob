# Changelog

โปรเจกต์นี้ยึดแนวทาง [Keep a Changelog](https://keepachangelog.com/th/1.1.0/) และ
[Semantic Versioning](https://semver.org/lang/th/).
ข้อมูลการออกรุ่น: ขั้นตอนใน [`docs/release-process.md`](docs/release-process.md)

## [Unreleased]

### Added

- **Windows/macOS portable (alpha — ยังไม่ได้รันบนเครื่องจริง)**
  · launcher ข้าม OS (`.lnk` ผ่าน PowerShell / `.command`)
  · ปัก taskbar/dock (best-effort) · global hotkey Windows (`RegisterHotKey` จำใน settings)
  · ดึงไอคอน `.exe/.lnk/.app` ผ่าน `QFileIconProvider` · สคริปต์ `packaging/build_windows.ps1`
  · แผน+เช็กลิสต์เทสต์ที่ออฟฟิศใน `docs/windows-plan.md`

## [0.2.0] — 2026-10-16

รุ่นปรับปรุงใหญ่: "กระเป๋าใส่ได้ทุกอย่าง" + UI polish · ยังเน้น Linux Mint (Cinnamon)

### Added

- **กระเป๋าใส่ได้ทุกอย่าง** — launcher แบบ type-aware เปิด target ได้หลายชนิด (แอป · โฟลเดอร์ · ไฟล์ · URL)
- **flyout คลิกขวาเปิดที่อยู่** — เปิดตำแหน่งโฟลเดอร์ที่มีไฟล์นั้น

### Changed

- **UI polish** — accent token กลาง (ปรับสีได้ที่เดียว) · ไอคอน SVG ของเรา tint ตามธีม
  · swatch สี + ช่อง hex · จัดเมนู/ลากใหม่
- **accent สีฟ้า** — ปรับเป็น `#1f9ede` (สดขึ้น) ใช้ทุกจุด (hover · selection · drop · ลิงก์)
- **hover ช่องกริด** ในตัวแก้ไข — ไฮไลท์ช่องโปร่งแสงแบบเดียวกับหน้าหลัก
- **i18n** — ไทยล้วน/อังกฤษล้วน · popup ไม่มีไอคอนปุ่ม + คำแปลครบ (`ตกลง`/`ยกเลิก`/`ปิด`)
- **ลากสลับเป็นสลับที่กัน (swap)** — ทั้งกริด shortcut และลำดับกลุ่มหน้าหลัก
  (ตรงกับที่ไฮไลท์โชว์ · ปล่อยที่ว่าง = ย้ายไปท้ายสุด)

### Fixed

- **ไอคอนไม่รีเฟรชตอนสลับธีม** (ต้องคลิก 2 รอบ) — อ่านสีจาก app palette ตรง ๆ ตอน tint
- ชื่อ/คำแปลผสมไทย-อังกฤษในกล่องข้อความ (`โฟลเดอร์ทำงาน` · `อาร์กิวเมนต์` · `รายการทางลัด`)
- **ไอคอนปุ่มหายใน AppImage/.deb** — SVG ทั้งชุดไม่ถูกแพ็ก + หา assets ผิด layout
  (PyInstaller 6 วางใต้ `_internal/`) → ปุ่มเฟือง/ตาว่างเปล่า (ดูเหมือน 0.1.0)
- **กด shortcut ที่เป็นไฟล์รันได้แล้วแอปไม่เปิด** — `gio open` ส่งให้ editor/disk-mounter
  (หรือไม่มี handler สำหรับ ELF) · ไฟล์ที่มี `+x` (AppImage/ELF/สคริปต์) กลับไปรันตรง
- **พรีวิวไอคอนกลุ่มขยายตามสไลเดอร์** — ตรึง 48px คงที่ (สไลเดอร์คุมแค่ไอคอนในกริด)
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

[Unreleased]: https://github.com/Neafong/TaskbarNoob/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Neafong/TaskbarNoob/releases/tag/v0.2.0
[0.1.0]: https://github.com/Neafong/TaskbarNoob/releases/tag/v0.1.0