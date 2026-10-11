# Phase 18 — Import/Export ทั้งชุด config (zip) — แผนงาน

> แผนนี้เขียนไว้ให้เซคชั่นใหม่ทำต่อได้โดยไม่ต้องเดาใหม่
> อ่านก่อนเริ่ม: `AGENTS.md` (บริบท/สถานะ) + ไฟล์นี้ + `docs/data-model.md` (โครง config)
> สถานะข้อตัดสินใจ: **[ตัดสินแล้ว]** = ไม่ต้องถามซ้ำ — ทุกหัวข้อตัดสินครบแล้ว (รวม UI import ผู้ใช้เคาะแล้ว)

## เป้าหมาย
ผู้ใช้ส่งออก **ทั้งชุด config** (กลุ่มทุกกลุ่ม + ไอคอน + ลำดับ + การตั้งค่า + ภาษาที่นำเข้า) เป็น `.zip`
แล้วนำเข้ากลับไปเครื่องใหม่ / สำรอง / แชร์ — ครบวงจรเหมือน "backup/restore"

## ขอบเขต / ไม่ทำ
- **ไม่ทำ** Windows UI — งานนี้เป็น core + GUI บน Linux ตามเดิม
- **ไม่ทำ** compress ตัว AppImage/ไฟล์แอปเอง (zip เฉพาะ config)
- **ไม่ทำ** เทียบ/แก้สคีมาเวอร์ชันข้ามมากตอน import (ดูหัวข้อ "สคีมา")

## โครง zip (สะท้อนโครง config พอดี — import ตรงไปตรงมา)
```
taskbargroups-backup-YYYYMMDD-HHMMSS.zip
├── groups/                ← คัดลอกทั้งโฟลเดอร์กลุ่ม (group.json + group_icon.* + icons/)
│   └── <GroupName>/
├── order.json
├── settings.json
└── lang/                  ← ไฟล์ภาษา overlay (*.json) ถ้ามี
```
สัญญา:
- ใช้ `/` (forward slash) ใน zip เสมอ · บีบอัด `ZIP_DEFLATED`
- อนุญาตเฉพาะ top-level: `groups/` · `order.json` · `settings.json` · `lang/` (whitelist)
- อย่างอื่นใน zip (เช่น `.DS_Store`, `thumbs.db`, ไฟล์แปลก) → **ข้าม** ไม่เอาเข้า (ไม่เอะอะ)

## [ตัดสินแล้ว] ไฟล์ใหม่: `taskbargroups/core/archive.py` (Python ล้วน ไม่ import Qt)

```python
EXPORT_DEFAULT_NAME = "taskbargroups-backup-{ts}.zip"   # ts = %Y%m%d-%H%M%S
MAX_ZIP_BYTES = 256 * 1024 * 1024                       # กันขยายตามาเต็มดิสก์

class ArchiveError(Exception): ...                       # ข้อความไทย/อังกฤษผ่าน i18n ที่ UI

def export_config(config_dir: Path, target: str | Path) -> Path
    # zip โฟลเดอร์ groups/ + order.json + settings.json + lang/ (เฉพาะที่มีอยู่)
    # คืน path ไฟล์ที่เขียน

def inspect_zip(path: str | Path) -> ZipReport
    # อ่านโดยไม่แกะ เช่น member count, ขนาดรวม, รายการ group ที่จะเข้า
    # ใช้ตอนยืนยันก่อน import (แสดง "จะนำเข้า 3 กลุ่ม...")

def import_config(path: str | Path, config_dir: Path, mode: str) -> ImportReport
    # mode: "merge" | "replace" — ผ่าน dry-run ก่อนเสมอ (ดู "ความปลอดภัย")
    # ไม่อนุญาตให้ import ซ้อน config (ปิดถ้าอยู่ใน config_dir เอง)
```

`ImportReport` เก็บ: `mode` · `groups_imported: list[str]` (ชื่อจริงหลัง unique) ·
`groups_kept` (ชนกัน) · `settings_imported: bool` · `lang_imported: list[str]` · `backup_dir: Path | None`

## พฤติกรรม import — [ตัดสินแล้ว มีการตัดสินใจ]
### mode = merge (default — ปลอดภัย ไม่ทำลายของเดิม)
- กลุ่มแต่ละกลุ่ม: ถ้าชื่อ dir ชนของเดิม (รวมของกลุ่มตัวเอง? ไม่ เว้นไว้) → ใช้ `_unique_group_name` แบบเดียวกับ
  `importer.py` คือเติม ` (2)`, ` (3)` เช่น `Tool` → `Tool (2)` (รูปแบบเดียวกันกับนำเข้าจาก Windows)
- `order.json`: **เก็บลำดับเดิม** แล้วต่อท้ายชื่อกลุ่มใหม่ (ลำดับของที่นำเข้าไว้ท้าย)
- `settings.json` / `lang/`: **ไม่แตะ** (ของคนเดิมอยู่)
### mode = replace (restore แบบเต็ม — สำรองก่อนเสมอ)
- ย้าย `config` เดิม → `config.bak-<YYYYmmdd-HHMMSS>` (พี่ config ตัวเดียวกัน) ก่อนเริ่ม
- แล้วเอา config จาก zip วางแทนทั้งชุด (groups + order + settings + lang)
- มี `backup_dir` อยู่ใน report ให้ UI บอกผู้ใช้ "สำรองไว้ที่ ..."
### หลัง import ทั้ง 2 mode
- ไม่แกะ/ไม่ทิ้ง `groups` ที่ไม่ได้ระบุขึ้นมาใหม่

## [ตัดสินแล้ว] ความปลอดภัย (ทำก่อนแกะจริงเสมอ)
1. `.zip` เท่านั้น · อ่านได้ (`zipfile.is_zipfile`) · ขนาด ≤ `MAX_ZIP_BYTES`
2. **zip-slip guard:** ทุก member — ปฏิเสธถ้า path มี `..` / ขึ้นต้น `/` / มี `\` / `resolve()` หลุดออกจาก staging root
3. **whitelist top-level** (4 รายการข้างบน) — อย่างอื่นข้าม
4. **dry-run ก่อนเขียน:** แกะลง staging temp (`<parent>/config.import-<rand>`) → validate ทุก `group.json`
   (`Group.from_dict` + `group.validate()`) → ถ้ามีกลุ่มใดเสีย → เลิกทั้งชุด (กันครึ่งเดียวขัด)
5. ไม่ใช่ repo ของ config ตัวเอง (กัน import ตัวเองทับ)

## [ตัดสินแล้ว — ผู้ใช้เคาะ 2026-10-11] หน้าต่างยืนยัน import (UI)
- `QMessageBox` ปุ่ม 3 ปุ่ม: **"เพิ่ม (merge)"** (default) / **"แทนที่ทั้งหมด (restore)"** / "ยกเลิก"
  - merge: เลือกไฟล์ zip → inspect → ถามยืนยัน → merge → สรุป (X กลุ่มนำเข้า · ชื่อชน Y กลุ่มถูกเติมเลข)
  - replace: ถามยืนยันแรง ๆ อีกชั้น ("จะสำรองของเดิมก่อนเสมอ") → ทำ → สรุปพร้อมตำแหน่ง backup
- ผู้ใช้เคาะรูปแบบนี้แล้ว (เห็น UI อีกทีหลังทำเสร็จ 555) → **ไม่ต้องถามซ้ำ**

## UI + i18n — [ตัดสินแล้ว]
- ตำแหน่ง: `SettingsDialog` เพิ่มแถวปุ่ม 2 ปุ่ม ถัดจากปุ่มภาษาที่มีอยู่:
  - **"ส่งออกทั้งหมด…"** (`QFileDialog.getSaveFileName` default `taskbargroups-backup-<ts>.zip`)
  - **"นำเข้าทั้งหมด…"** (`QFileDialog.getOpenFileName`)
- ปุ่มทั้ง 2 ต้องเข้า `_retranslate()` ของ SettingsDialog ด้วย
- เพิ่มคีย์ i18n (TH+EN) เช่น:
  - `settings.export_all` / `settings.export_all_tip`
  - `settings.import_all` / `settings.import_all_tip`
  - `settings.export_all_ok` = "ส่งออก {count} กลุ่มเป็น '{path}' แล้ว ({size})"
  - `settings.import_confirm_merge` / `_replace` · `settings.import_summary` · `settings.import_backup_note`
  - `err.archive_invalid` / `err.archive_slip` / `err.archive_too_big` / `err.archive_backup_failed`
  - (ส่งออก/นำเข้าภาษา key เดิม `settings.export_lang*` คงเดิม — อย่าไปแกะ)

## [ตัดสินแล้ว] เทสต์ — `tests/test_archive.py` (เพิ่ม ≤ ~12 เทสต์)
1. `export_config` สร้าง zip มี `groups/`, `order.json`, `settings.json` (พอมีจริง)
2. roundtrip: export จาก tmp → import "replace" ลง tmp2 ใหม่ → เทียบเท่าต้นฉบับ (รายชื่อกลุ่ม/order/settings เท่ากัน)
3. roundtrip merge: import ลงที่ที่มี "Tool" อยู่แล้ว → ได้ `Tool (2)` · ของเดิมยังอยู่
4. merge ไม่แตะ settings.json ของเดิม
5. replace สร้าง `config.bak-*` และของเดิมถูกแทนจริง
6. zip-slip: zip ปลอม member `../evil` → `ArchiveError`
7. top-level ไม่ whitelist (เช่น `random.txt`) → import สำเร็จแต่ข้ามไฟล์นั้น
8. กลุ่มที่มี `group.json` เสีย → reject ทั้งชุด (dry-run fail)
9. ขนาดเกิน cap → reject (ใช้ mock/cap เล็กในเทสต์)
10. zip ปลอม/ไม่ใช่ zip → `ArchiveError`
11. import zip ตัวที่ไม่ใช่ config ของเรา (ไม่มี groups/) → error ชัด
12. UI smoke: SettingsDialog มีปุ่ม send/import ทั้ง 2 + อยู่ใน `_retranslate` (เช็คผ่าน)

## ลำดับงาน (ทำตามนี้ในเซคชั่นใหม่)
1. ตั้ง `_unique_group_name` ใช้ร่วมกับ importer (ย้าย/แชร์ logic — หรือ import จาก storage/importer)
2. เขียน `core/archive.py` + เทสต์ 1–11 (รัน: `.venv/bin/python tests/run.py` — ต้อง 223 + ใหม่ทั้งหมดผ่าน)
3. GUI `SettingsDialog`: ปุ่ม 2 ปุ่ม + handler + `_retranslate` (เทสต์ 12)
4. i18n TH/EN — ใช้ pattern เดิม (`core/i18n.py` dict) · import เป็น en ตอนจบ
5. รันเทสต์เต็ม · wrap-up: อัปเดต `AGENTS.md`, `docs/WORKLOG.md` (Phase 18), `docs/feedback.md`,
   `docs/data-model.md` (เพิ่มหัวข้อ "Archive (zip)") — เปลี่ยน status เป็นรอบ #15
6. Build: `bash packaging/build_appimage.sh` → `bash packaging/build_deb.sh` →
   ตรวจ `dist/` + boot `--list` (ใช้ `--appimage-extract-and-run` — เครื่อง FUSE ไม่เวิร์ก)
   + ทดสอบ export/import จริงบน `dist/config` (สำเนา) ก่อนสรุป

## ข้อควรรู้
- repo เป็น fuseblk (chmod ไม่ติด) — `.deb` สคริปต์สเตจใน `/tmp` แล้ว
- `dist/config` = config จริงของผู้ใช้ (Tool/Game/Production) — **ห้ามทดสอบ import บนตัวจริง** ใช้สำเนา
- จำกัด i18n/toekn: ส่วนใหญ่เป็นโค้ดซ้ำสำเร็จรูป ระวังอย่าใส่ comment เยอะ
- รันเทสต์หลังเสร็จเสมอ + อัปเดต docs (นี่คือ "ความจำโปรเจกต์")