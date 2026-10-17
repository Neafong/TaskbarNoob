# Release Process — TaskbarNoob

> ขั้นตอนออกรุ่น/อัปเดต · อัปเดตล่าสุด: 2026-10-17
> แผนระยะยาว: [`roadmap.md`](roadmap.md) · คำสั่ง dev: `../AGENTS.md`

## หลักการเวอร์ชัน (SemVer)

- ตัวเลขเวอร์ชัน**แหล่งเดียว** = `__version__` ใน `taskbargroups/__init__.py`
  (build scripts อ่านจากตรงนี้ — อย่าแก้ที่อื่น)
- รูปแบบ `MAJOR.MINOR.PATCH` เช่น `0.1.0` · แท็ก = `v<version>` เช่น `v0.1.0`
- กดด้วยปุ่ม Release บน GitHub + **แนบ binary เป็น assets** (AppImage/.deb) — ไม่ commit binary เข้า repo

## วงรอบออกรุ่นปกติ

1. **bump version** — แก้ `taskbargroups/__init__.py` → `__version__ = "x.y.z"`
2. **อัปเดต `CHANGELOG.md`** — หัวข้อใหม่ใต้ "Unreleased" ตามแนวคิด [Keep a Changelog](https://keepachangelog.com/)
3. **เทสต์** — `.venv/bin/python tests/run.py` ต้องผ่าน (ปัจจุบัน 307)
4. **build** — `bash packaging/build_appimage.sh` และ `bash packaging/build_deb.sh`
5. **คัดลอก AppImage ไปที่ใช้งานจริง** — `cp dist/TaskbarNoob-x86_64.AppImage ~/AppImage/Tool/`
   (ที่เดียวที่ใช้รัน/เทสต์ — ดูข้อตกลง "ที่เก็บไฟล์" ใน `../AGENTS.md` · อย่าเทสต์จาก `dist/` ตรง ๆ)
6. **smoke test** — ตรวจ boot: `~/AppImage/Tool/TaskbarNoob-x86_64.AppImage --list` (หรือรันจากซอร์ส)
7. **commit + push** (กุญแจ SSH ตั้งไว้แล้ว):
   ```bash
   git add -A && git commit -m "vX.Y.Z: <สรุปสั้น>"
   git push
   ```
8. **สร้างแท็ก**:
   ```bash
   git tag -a vX.Y.Z -m "TaskbarNoob vX.Y.Z: <สรุปสั้น>"
   git push origin vX.Y.Z
   ```
9. **สร้าง GitHub Release** (เว็บ): https://github.com/Neafong/TaskbarNoob/releases/new
   - Choose a tag: `vX.Y.Z` · title `TaskbarNoob vX.Y.Z` · release notes (ไทย)
   - แนบ assets: `dist/TaskbarNoob-x86_64.AppImage` + `dist/taskbargroups_<ver>_amd64.deb`
   - **ไม่** ติ๊ก Pre-release (เว้นใช้กับ rc) · เผยแพร่
10. **อัปเดตเอกสาร** — `docs/WORKLOG.md` (บันทึกงาน) + `docs/feedback.md` (ถ้าปิดฟีดแบ็ก) · อัปเดต `AGENTS.md` snapshot

## งานระหว่างรุ่น (เท่าปกติ)

- แก้โค้ด → `tests/run.py` → commit + push (ทุกชุดงาน) — **หาเรียก tag/release ทุกครั้งไม่**
- เริ่มงานชุดใหญ่ในเซคชั่นใหม่เสมอ (ประหยัด token)

## จุด release vs ปกติ

| งาน | ปกติ | ตอนออกรุ่น |
|---|---|---|
| commit + push | ✅ | ✅ |
| บัmp version | ❌ | ✅ |
| อัปเดต CHANGELOG | ❌ | ✅ |
| build + smoke | ❌ (นาน) | ✅ |
| tag + GitHub Release | ❌ | ✅ |

## รุ่นทดลอง (Pre-release) — ถ้าจำเป็น

- แท็กตามด้วย `-rcN` เช่น `v0.2.0-rc1` → Release ติ๊ก **"Set as a pre-release"**
- ผู้ใช้ที่อยากลองดาวน์โหลดได้จากหน้า release · ไม่โชว์เป็นเวอร์ชันแนะนำ

## อนาคต (CI)

- เฟส E จะเพิ่ม GitHub Actions: รัน `tests/run.py` อัตโนมัติทุก push/PR
- (ทางเลือก) workflow สร้าง AppImage/.deb อัตโนมัติเมื่อกด tag → ค่อยๆ ลดงาน manual ตรง build