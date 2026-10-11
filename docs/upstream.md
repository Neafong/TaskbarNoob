# Upstream Research — Taskbar Groups (Windows)

> เก็บผลตรวจต้นฉบับแยกจาก AGENTS.md (เช็กผ่าน GitHub API — 2026-10-10)

## ต้นฉบับ
- Repo: https://github.com/tjackenpacken/taskbar-groups (MIT)
- Windows-only: C# WinForms (.NET Framework) + Windows Shell/Taskbar API

## สถานะจริงของ upstream
- **โค้ดจริงหยุดที่ v0.2.0.0 / commit 2021-01-05** — master ไม่มี commit หลังวันนั้น
- เหลือแค่ 2 branch: `master` (นิ่ง 2021) + `add-license-1` (2020)
- `pushed_at` ปี 2024 มาจาก **PR #315** (คนนอก, open ไม่ถูก merge) ไม่ใช่การอัปเดตจริง
- เปิด issues ค้าง ~276 รายการ, repo ไม่ถูก archive (ทิ้งงานมากกว่าเสถียร)

## ฟีเจอร์ที่คนอยากได้ แต่ค้างเป็น open PR (ไม่เข้าแอป)
- hover tooltip บนไอคอน (#352)
- เปิดแอปแบบ admin (#305)
- รองรับ Windows 11 / แก้ absolute path (#346)
- แก้บั๊ก multi-monitor (#109)
- tray options (#52) / autostart (#86) — ปิดไปแล้ว

## โครงเก็บข้อมูลของต้นฉบับ (ใช้อ้างอิงทำ importer)
- `config/<GroupName>/ObjectData.xml` = ค่าตั้งกลุ่ม + รายการ shortcut
- `config/<GroupName>/Icons/` = cache ไอคอน
- `config/<GroupName>/GroupIcon.ico` / `GroupImage.png` = ไอคอนกลุ่ม

## ฟีเจอร์ต้นฉบับ (เป้า MVP — v0.2.0.0)
ชื่อกลุ่ม, width (จำนวนต่อแถว), สี (dark/light/custom), opacity,
hotkeys (เลข 1-0 เลือกชิ้นที่ 1-10), Ctrl+Enter เปิดทั้งหมด, working directory,
arguments, open-all

**สรุป:** สเปก "แช่แข็ง" → ยึดฟีเจอร์ v0.2.0.0 เป็นเป้า MVP ได้เลย
