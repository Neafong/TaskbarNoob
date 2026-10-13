# Data Model & Storage — TaskbarGroups

> ออกแบบใน Phase 1 · ปรับปรุงได้เรื่อยๆ (มี `schema_version` กันพัง)

## หลักการ
- **Portable** — ข้อมูลทั้งหมดอยู่ใต้ `config/` ในโฟลเดอร์แอป (เหมือนต้นฉบับ)
  override ได้ด้วย env `TASKBARGROUPS_CONFIG` (มีประโยชน์ตอนทดสอบ/พกพา)
- **ข้าม OS** — เก็บเป็น JSON (UTF-8) ใช้ได้ทั้ง Linux และ Windows
  path ภายในเก็บเป็น string ตรงๆ ของแต่ละ OS
- **แยก core ออกจาก UI** — `taskbargroups/core/` เป็น Python ล้วน ไม่ import Qt
  เพื่อให้เขียนเทสต์ได้โดยไม่ต้องมี GUI และพอร์ตง่าย

## โครงโฟลเดอร์ (portable)
```
<app>/config/                 ← override ด้วย env TASKBARGROUPS_CONFIG
└── groups/
    └── <GroupName>/          ← ชื่อโฟลเดอร์ = ชื่อกลุ่มที่ sanitize แล้ว
        ├── group.json        ← ค่าตั้งกลุ่ม + รายการ shortcut
        ├── group_icon        ← ไอคอนกลุ่ม (คัดลอกมาเก็บ, Phase 4)
        └── icons/            ← cache ไอคอนของแต่ละ shortcut (Phase 4)
```

## สกีมา `group.json`
```jsonc
{
  "schema_version": 1,
  "name": "My Group",          // 1..49 ตัวอักษร
  "icon": "group_icon",        // path สัมพัทธ์ในโฟลเดอร์กลุ่ม หรือ null
  "width": 6,                  // จำนวนไอคอนต่อแถว (1..50)
  "color": {
    "mode": "dark",            // "dark" | "light" | "custom"
    "custom": null             // hex #RGB / #RRGGBB เมื่อ mode = custom
  },
  "opacity": 0,                // 0 (ทึบ) .. 100 (โปร่งใส)
  "allow_open_all": false,     // เปิดทุกอย่างพร้อมกัน (Ctrl+Enter)
  "items": [
    {
      "name": "Firefox",       // 1..27 ตัวอักษร (label บนไอคอน)
      "target": "/usr/bin/firefox",  // โปรแกรม/คำสั่ง/ไฟล์ .desktop
      "working_dir": null,     // working directory (ถ้ามี)
      "arguments": "",         // อาร์กิวเมนต์ตอนเปิด
      "icon": null             // path สัมพัทธ์ใน icons/ หรือ null
    }
  ]
}
```

## ทำไมเลือก JSON (ไม่ใช่ `.desktop` / XML)
| ทางเลือก | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|
| **JSON ต่อกลุ่ม** | ควบคุมสกีมาได้, ข้าม OS, อ่าน/เขียนง่าย | ต้องมีโค้ดแปลงเอง | ✅ เลือกใช้ |
| `.desktop` ล้วน | ต่อกับเมนู Linux เนียน | เก็บ opacity/สี/width ไม่ตรง, Windows ไม่รู้จัก | ใช้เฉพาะ launcher (Phase 3) |
| `ObjectData.xml` (แบบต้นฉบับ) | นำเข้ากลุ่มเดิมง่าย | รูปแบบ XML เฉพาะทาง | เก็บไว้ทำ importer (Phase 4) |

แผน: **`group.json` = แหล่งข้อมูลจริง** → ตอนปัก panel (Phase 3) จะ *generate* `.desktop`
ให้ระบบ และตอน import กลุ่มจาก Windows (Phase 4) จะอ่าน `ObjectData.xml` → `group.json`

## กติกาการ validate (บังคับตอน `save_group`)
- ชื่อกลุ่ม: ห้ามว่าง, ≤ 49 ตัวอักษร
- ชื่อ shortcut: ห้ามว่าง, ≤ 27 ตัวอักษร
- `target`: ห้ามว่าง
- `width`: 1..50 · `opacity`: 0..100
- `color_mode="custom"` → `custom_color` ต้องเป็น hex ที่ถูกต้อง

## API หลัก (`taskbargroups.core.storage.ConfigStore`)
- `list_groups() -> list[str]` — คืนชื่อโฟลเดอร์กลุ่ม (เรียงตามตัวอักษร)
- `load_group(dir_name) -> Group`
- `save_group(group) -> Path` — validate + เขียน JSON + สร้าง `icons/`
- `delete_group(dir_name)`
- `group_dir / icons_dir / group_icon_path`

## แคชไอคอน (`taskbargroups.core.icons`)

แยกออกมาเป็น core (Python ล้วน ไม่ผูก Qt) เพื่อพอร์ต/เทสต์ง่าย
- `resolve_icon_source(target)` — หา *ไฟล์รูปจริง*: ถ้าเป็นไฟล์รูปก็ใช้เลย
  ถ้าเป็น `.desktop` จะอ่านคีย์ `Icon=` แล้วค้นในธีมของระบบ (`~/.local/share/icons`,
  `/usr/share/icons`, `/usr/share/pixmaps`, ...)
- `cache_icon(source, icons_dir, stem)` / `cache_shortcut_icon(...)` — คัดลอกเข้า
  `icons/` ตั้งชื่อเป็น `<stem>.<ext>` (แทนไฟล์ชื่อซ้ำเดิม) แล้วคืน path สัมพัทธ์
  เช่น `icons/Firefox.png`
- ไอคอนกลุ่มใช้ `ConfigStore.import_group_icon()` → เก็บเป็น `group_icon.<ext>`

> GUI ตอน Save จะแคชไอคอนให้อัตโนมัติเมื่อ target หาไอคอนเจอ (หรือผู้ใช้เลือกไฟล์เอง)

## Importer จาก Windows (`taskbargroups.core.importer`) — ❌ ถูกตัดใน v0.2

ตัดฟีเจอร์นี้ออกทั้งชุด (รอบ #19 — ผู้ใช้ตัดสินใจ 2026-10-12): ลบปุ่ม / `core/importer.py` /
CLI `--import` / เทสต์ เหลือ "นำเข้าทั้งหมด" จาก `.zip` สำรองใน Settings ปุ่มเดียวจบ
ดูฟอร์แมต `ObjectData.xml` ของต้นฉบับย้อนหลังได้ที่ [`upstream.md`](upstream.md)

## Archive — Export/Import ทั้งชุด config (`taskbargroups.core.archive`)

Phase 18: สำรอง/กู้คืน config ทั้งชุดเป็น `.zip` (Python ล้วน ไม่ import Qt)

โครง zip (สะท้อนโครง config):
```
taskbargroups-backup-YYYYMMDD-HHMMSS.zip
├── groups/<GroupName>/...   ← group.json + group_icon + icons/
├── order.json
├── settings.json            (ถ้ามี)
└── lang/<code>.json         (ถ้ามี)
```

- `export_config(config_dir, target) -> Path` — zip เฉพาะที่มีอยู่ (`ZIP_DEFLATED`, `/` เสมอ)
- `inspect_zip(path) -> ZipReport` — อ่านก่อน import (รายชื่อกลุ่ม · settings · lang · ขนาด)
- `import_config(path, config_dir, mode) -> ImportReport` — `mode` = `"merge"` | `"replace"`
  - **merge:** กลุ่มชื่อชน → เติม ` (2)`, ` (3)` (เหมือน `unique_group_name`) · `order.json` ต่อท้าย ·
    `settings.json`/`lang/` **ไม่แตะ**
  - **replace:** สำรอง config เดิมเป็น `config.bak-<ts>` ก่อน แล้ววางทับทั้งชุด (มี `backup_dir` ใน report)
- ความปลอดภัย: `.zip` เท่านั้น · `MAX_ZIP_BYTES` 256MB · **zip-slip guard** (`..`/absolute/backslash) ·
  whitelist top-level (`groups/`, `order.json`, `settings.json`, `lang/`) · **dry-run** (validate
  `group.json` ทุกกลุ่มใน staging) ก่อนเขียนจริง · ไฟล์แปลกนอก whitelist = ข้าม
- UI: ปุ่ม **"ส่งออกทั้งหมด…"** / **"นำเข้าทั้งหมด…"** / **"ลบสำรองเก่า…"** ใน `SettingsDialog`
  (import มี 3 ปุ่ม merge/replace/ยกเลิก)
- `list_backups(config_dir)` / `delete_backups(config_dir, backups)` — จัดการ `config.bak-*` ที่ค้าง
  (ลบเฉพาะโฟลเดอร์สำรองใน parent เดียวกับ config)

## ภาษา (i18n) — ภาษาที่เพิ่มเองผ่าน asset
- ภาษาในตัว: `th` (แม่/fallback) + `en` ในโค้ด `core/i18n.py`
- ภาษาที่ 3+ = ไฟล์ `<config>/lang/<code>.json` (ผู้ใช้ได้มาจากปุ่ม **ส่งออกภาษา** ใน Settings หรือ
  โหลด asset จาก repo `packaging/lang/`) · import ผ่าน Settings → ขึ้นใน dropdown
- ชื่อแสดงใน dropdown: key พิเศษ `_lang_name` ในไฟล์ (เช่น `"日本語"`) — ถ้าไม่มีใช้ code แทน
- ตัวอย่าง asset: `packaging/lang/ja.json` (ญี่ปุ่น แปลครบ 147 คีย์) — ต้นแบบให้ผู้ใช้รายอื่นแปลตาม
- ภาษาไทยคือ fallback ของทุกภาษา → แปลเป็นไฟล์บางส่วนได้ (คีย์ที่ไม่ได้แปลจะโผล่เป็นไทย)

