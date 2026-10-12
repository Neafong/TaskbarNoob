# เอกสารโปรเจกต์ TaskbarNoob — แผนที่ (Docs Index)

> ดัชนีเอกสารทั้งหมด + แผนการจัดระเบียบเอกสาร · อัปเดตล่าสุด: 2026-10-12
> **เปิด [`../AGENTS.md`](../AGENTS.md) ก่อนเสมอ** เพื่อดู snapshot สถานะปัจจุบัน

## หลักการจัดเอกสาร

- **1 ไฟล์ = 1 หน้าที่** — อย่าให้ไฟล์เดียวบวมรวมทุกเรื่อง
- **snapshot สั้น** (`AGENTS.md`) · **log ต่อท้ายอย่างเดียว** (`WORKLOG.md`)
- **ของเฉพาะ GitHub** → ไว้ที่ root หรือ `.github/` (ไม่ปนกับ `docs/`)

## เอกสารที่มีอยู่

| ไฟล์ | หน้าที่ |
|---|---|
| [`../AGENTS.md`](../AGENTS.md) | snapshot สถานะปัจจุบัน (สั้น · อัปเดตทุกครั้งที่จบงาน) |
| [`WORKLOG.md`](WORKLOG.md) | บันทึกงานย้อนหลังต่อเฟส (append-only) |
| [`feedback.md`](feedback.md) | ฟีดแบ็กผู้ใช้ + สถานะ + งานค้าง |
| [`roadmap.md`](roadmap.md) | แผนภาพรวมทุกเฟส + งานถัดไป + แผน Windows (W0–W5) |
| [`release-process.md`](release-process.md) | ขั้นตอนออกรุ่น/อัปเดต (bump → CHANGELOG → build → tag → Release) |
| [`data-model.md`](data-model.md) | สกีมา `group.json` + ฟอร์แมตเก็บกลุ่ม |
| [`upstream.md`](upstream.md) | ผลวิจัยต้นฉบับ Windows (Taskbar Groups) |
| [`phase18-plan.md`](phase18-plan.md) | แผน Phase 18 (import/export zip) — อ้างอิงย้อนหลัง |
| [`screenshots/`](screenshots/) | รูปหน้าจอสำหรับ README |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | วิธีร่วมพัฒนา (Issue → PR → CI → เอกสาร) |
| `../CHANGELOG.md` | ประวัติเวอร์ชัน (Keep a Changelog) |
| `../.github/**` | CI (`workflows/`) · เทมเพลต issue/PR · `FUNDING.yml` |

## เอกสารที่จะเพิ่มถัดไป

| ไฟล์ | หน้าที่ |
|---|---|
| [`windows-plan.md`](windows-plan.md) | แผนพอร์ต Windows (เฟส W0–W5) — เลื่อนไว้ทำตอนเริ่ม Windows จริง (ดูแผนคร่าว ๆ ใน `roadmap.md`) |

## ลำดับเฟสสร้างเอกสาร (ทีละเฟส = 1 commit)

| เฟส | ทำอะไร | ไฟล์ | สถานะ |
|---|---|---|---|
| **A** | ดัชนี/แผนที่เอกสาร (ไฟล์นี้) | `docs/README.md` | ✅ เสร็จ |
| **B** | แผนภาพรวมทุกเฟส + ย่อ `AGENTS.md` ให้ชี้ไปแผน | `docs/roadmap.md` + `../AGENTS.md` | ✅ เสร็จ |
| **C** | ขั้นตอนออกรุ่น/อัปเดต | `docs/release-process.md` | ✅ เสร็จ |
| **D** | ประวัติเวอร์ชัน (เริ่ม v0.1.0) | `CHANGELOG.md` | ✅ เสร็จ |
| **E** | ของ GitHub: CI + เทมเพลต + ปุ่มสนับสนุน | `.github/**` | ✅ เสร็จ |
| **F** | แผนพอร์ต Windows (W0–W5) | `docs/windows-plan.md` | ⏳ |
| **G** | วิธีร่วมพัฒนา | `CONTRIBUTING.md` | ✅ เสร็จ |

**เหตุผลลำดับ:** จัดของเดิมให้เข้าที่ (A→B) → ของ GitHub ที่ใช้ตอนแจกจริง (C→E) → งานอนาคต Windows (F→G)
