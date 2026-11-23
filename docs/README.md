# เอกสารโปรเจกต์ TaskbarNoob — แผนที่ (Docs Index)

> ดัชนีเอกสารทั้งหมด · อัปเดตล่าสุด: 2026-11-23
> **เปิด [`../AGENTS.md`](../AGENTS.md) ก่อนเสมอ** เพื่อดู snapshot สถานะปัจจุบัน

## หลักการจัดเอกสาร

- **1 ไฟล์ = 1 หน้าที่** — อย่าให้ไฟล์เดียวบวมรวมทุกเรื่อง
- **snapshot สั้น** (`AGENTS.md`) · **log ต่อท้ายอย่างเดียว** (`WORKLOG.md`)
- **เอกสารเก่าที่ปิดจบแล้ว** → เก็บไว้ใน `docs/archive/` เพื่อประหยัด context
- **ของเฉพาะ GitHub** → ไว้ที่ root หรือ `.github/` (ไม่ปนกับ `docs/`)

## เอกสารที่ใช้งานอยู่ (Active)

| ไฟล์ | หน้าที่ |
|---|---|
| [`../AGENTS.md`](../AGENTS.md) | snapshot สถานะปัจจุบัน (สั้น · อัปเดตทุกครั้งที่จบงาน) |
| [`WORKLOG.md`](WORKLOG.md) | บันทึกงานย้อนหลังภาค `v0.3.0+` (append-only) |
| [`feedback.md`](feedback.md) | งานค้างและฟีดแบ็กที่ยังไม่ปิด |
| [`roadmap.md`](roadmap.md) | แผนภาพรวมทุกเฟส + แผน `v0.3.0` (R0–R4) |
| [`release-process.md`](release-process.md) | ขั้นตอนออกรุ่น/อัปเดต (bump → CHANGELOG → build → tag → Release) |
| [`data-model.md`](data-model.md) | สกีมา `group.json` + ฟอร์แมตเก็บกลุ่ม |
| [`upstream.md`](upstream.md) | ผลวิจัยต้นฉบับ Windows (Taskbar Groups) |
| [`team.md`](team.md) | บทบาทผู้ช่วยและแนวทางการทำงานร่วมกัน |
| [`screenshots/`](screenshots/) | รูปหน้าจอสำหรับ README |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | วิธีร่วมพัฒนา (Issue → PR → CI → เอกสาร) |
| [`../CHANGELOG.md`](../CHANGELOG.md) | ประวัติเวอร์ชัน (Keep a Changelog) |
| [`../.github/`](../.github/) | CI (`workflows/`) · เทมเพลต issue/PR · `FUNDING.yml` |

## เอกสารเก่าเก็บ ([`archive/`](archive/))

| ไฟล์ | หน้าที่ |
|---|---|
| [`archive/WORKLOG-v0.1-v0.2.md`](archive/WORKLOG-v0.1-v0.2.md) | ประวัติการทำงานทั้งหมดของภาค `v0.1.0–v0.2.0` |
| [`archive/feedback-v0.1-v0.2.md`](archive/feedback-v0.1-v0.2.md) | ฟีดแบ็กและมติทั้งหมดที่ปิดจบแล้วในภาค `v0.1.0–v0.2.0` |
| [`archive/phase18-plan.md`](archive/phase18-plan.md) | แผน Phase 18 (import/export zip) — อ้างอิงย้อนหลัง |
| [`archive/windows-plan.md`](archive/windows-plan.md) | แผนพอร์ต Windows 11 (W0–W5) — ปิดจบใน `v0.2.0` |
