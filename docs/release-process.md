# Release Process — TaskbarNoob

> ขั้นตอนออกรุ่น/อัปเดต (Linux Mint + Windows 11) · อัปเดตล่าสุด: 2026-11-24
> แผนระยะยาว: [`roadmap.md`](roadmap.md) · คำสั่ง dev & กฎกลาง: [`../AGENTS.md`](../AGENTS.md)

## หลักการเวอร์ชัน (SemVer)

- ตัวเลขเวอร์ชัน**แหล่งเดียว** = `__version__` ใน `taskbarnoob/__init__.py`
  (build scripts อ่านจากตรงนี้ — อย่าแก้ที่อื่น)
- รูปแบบ `MAJOR.MINOR.PATCH` เช่น `0.3.0` · แท็ก = `v<version>` เช่น `v0.3.0`
- ปล่อยรุ่นผ่าน GitHub Releases + **แนบ binary เป็น assets** (AppImage, `.deb`, Windows portable `.zip`) — ไม่ commit binary เข้า repo

## Docs Audit Checklist (บังคับก่อนปิดรุ่นทุกครั้ง!)

> ห้ามสร้าง tag / ปล่อย GitHub Release จนกว่าจะไล่เช็กครบทุกไฟล์ด้านล่าง:

- [ ] **`README.md` & `README.th.md`** — อัปเดตฟีเจอร์ใหม่, แพลตฟอร์มที่รองรับ, คำสั่งรัน/build, เลขจำนวนเทสต์, และ Roadmap
- [ ] **`CHANGELOG.md`** — สรุปหัวข้อ `Added / Changed / Fixed / Removed` ตาม [Keep a Changelog](https://keepachangelog.com/) + เพิ่ม reference link `[X.Y.Z]` ท้ายไฟล์
- [ ] **`CONTRIBUTING.md` & `.github/PULL_REQUEST_TEMPLATE.md`** — ตรวจชื่อแพ็กเกจ, คำสั่ง dev/test ทั้ง Linux & Windows, กฎ i18n (9 ภาษา)
- [ ] **`packaging/appimage/taskbarnoob.appdata.xml`** — ตรวจชื่อแอป, คำอธิบาย, และเครดิต
- [ ] **`docs/roadmap.md` & `docs/feedback.md`** — ติ๊กงานที่ปิดแล้ว + อัปเดตแผนรุ่นถัดไป
- [ ] **`docs/WORKLOG.md` & `AGENTS.md`** — บันทึกงานที่เสร็จ, อัปเดต snapshot และ Handoff สำหรับเครื่อง/รุ่นถัดไป

## วงรอบออกรุ่นปกติ (ข้าม 2 OS: Linux Mint ↔ Windows 11)

1. **bump version** — แก้ `taskbarnoob/__init__.py` → `__version__ = "X.Y.Z"`
2. **Docs Audit** — ไล่เช็กและอัปเดตเอกสารทั้งหมดตาม **Docs Audit Checklist** ด้านบน
3. **เทสต์เต็มระบบทั้ง 2 OS:**
   - Linux Mint: `QT_QPA_PLATFORM=offscreen .venv/bin/python tests/run.py`
   - Windows 11: `.venv-win\Scripts\python.exe tests/run.py`
4. **Build & Smoke Test ฝั่ง Linux Mint:**
   - `bash packaging/build_appimage.sh` → `dist/TaskbarNoob-x86_64.AppImage`
   - `bash packaging/build_deb.sh` → `dist/taskbarnoob_<ver>_amd64.deb`
   - **คัดลอก AppImage ไปที่ใช้งานจริง:** `cp dist/TaskbarNoob-x86_64.AppImage ~/AppImage/Tool/`
     *(ที่เดียวที่ใช้รัน/เทสต์ — ดูข้อตกลง "ที่เก็บไฟล์" ใน `../AGENTS.md` · อย่าเทสต์จาก `dist/` ตรง ๆ)*
   - smoke test: `~/AppImage/Tool/TaskbarNoob-x86_64.AppImage --list` + ทดสอบเปิดแอปจริง
5. **Build & Smoke Test ฝั่ง Windows 11:**
   - `powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1` → `dist\TaskbarNoob\`
   - deploy ทับโฟลเดอร์ใช้งานจริง `D:\Portable\Tool\TaskbarNoob` (ไม่แตะ `config\`) + live-test
   - ตรวจว่า `dist\TaskbarNoob\` ไม่มี `config\` หลงเหลือ แล้วบีบอัดเป็น `dist\TaskbarNoob-win64-portable.zip`
6. **ซิงก์โค้ด (ถ้ามีการแก้บั๊กระหว่างทดสอบอีก OS):**
   - `git commit` + `git push origin main` → ให้เครื่องอีกฝั่ง `git pull`, รันเทสต์, และ rebuild แพ็กเกจให้ตรง commit เดียวกัน
7. **สร้างแท็กจาก commit สุดท้ายที่ผ่านทั้ง 2 OS:**
   ```bash
   git tag -a vX.Y.Z -m "TaskbarNoob vX.Y.Z: <สรุปสั้น>"
   git push origin vX.Y.Z
   ```
8. **สร้าง GitHub Release** (เว็บ): https://github.com/Neafong/TaskbarNoob/releases/new
   - Choose a tag: `vX.Y.Z` · title `TaskbarNoob vX.Y.Z` · release notes
   - แนบ assets ครบ 3 ไฟล์:
     - `TaskbarNoob-x86_64.AppImage`
     - `taskbarnoob_<ver>_amd64.deb`
     - `TaskbarNoob-win64-portable.zip`
   - **ไม่** ติ๊ก Pre-release (เว้นใช้กับ `-rcN`) · เผยแพร่

## งานระหว่างรุ่น (ปกติ)

- แก้โค้ด → `tests/run.py` → commit + push (ทุกชุดงาน) — **ไม่จำเป็นต้องสร้าง tag/release ทุกครั้ง**
- เริ่มงานชุดใหญ่ในเซคชั่นใหม่เสมอ (ประหยัด token)

## จุด release vs ปกติ

| งาน | ปกติ | ตอนออกรุ่น |
|---|---|---|
| commit + push | ✅ | ✅ |
| bump version | ❌ | ✅ |
| Docs Audit Checklist (`README*`, `CHANGELOG`, `CONTRIBUTING`, ฯลฯ) | ❌ | ✅ |
| build + smoke (Mint & Win 11) | ❌ (นาน) | ✅ |
| tag + GitHub Release (3 assets) | ❌ | ✅ |

## รุ่นทดลอง (Pre-release) — ถ้าจำเป็น

- แท็กตามด้วย `-rcN` เช่น `v0.4.0-rc1` → Release ติ๊ก **"Set as a pre-release"**
- ผู้ใช้ที่อยากลองดาวน์โหลดได้จากหน้า release · ไม่โชว์เป็นเวอร์ชันแนะนำ
