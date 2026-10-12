# Changelog

โปรเจกต์นี้ยึดแนวทาง [Keep a Changelog](https://keepachangelog.com/th/1.1.0/) และ
[Semantic Versioning](https://semver.org/lang/th/).
ข้อมูลการออกรุ่น: ขั้นตอนใน [`docs/release-process.md`](docs/release-process.md)

## [Unreleased]

- (รอใส่เมื่อมีงานเข้า — ดู `docs/roadmap.md` สำหรับแผน)

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

[Unreleased]: https://github.com/Neafong/TaskbarNoob/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Neafong/TaskbarNoob/releases/tag/v0.1.0