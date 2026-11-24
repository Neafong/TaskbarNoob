# Contributing — TaskbarNoob

ขอบคุณที่สนใจร่วมพัฒนา 🙏 โปรเจกต์นี้แจกฟรี ทำด้วยใจ — ทุกความช่วยเหลือมีค่า

## เริ่มจากตรงไหน

1. อ่าน [`README.md`](README.md) + [`AGENTS.md`](AGENTS.md) (snapshot สถานะ) + [`docs/README.md`](docs/README.md) (แผนที่เอกสาร) ก่อนเสมอ
2. ดูงานค้าง/ฟีดแบ็ก: [`docs/feedback.md`](docs/feedback.md) · แผนระยะยาว: [`docs/roadmap.md`](docs/roadmap.md)
3. อยากแก้บั๊ก/เพิ่มฟีเจอร์ → เปิด **Issue** ก่อน (มี template) แล้วค่อยทำ PR

## รายงานบั๊ก / เสนอฟีเจอร์

- ใช้ GitHub Issue: [`bug_report.md`](.github/ISSUE_TEMPLATE/bug_report.md) / [`feature_request.md`](.github/ISSUE_TEMPLATE/feature_request.md)
- ฝนสภาพแวดล้อมให้ครบ (OS/DE · X11 หรือ Wayland · หลายจอไหม · เวอร์ชันแอป) — ตรงนี้ช่วยแก้ไวมาก

## เซตอัป Dev

```bash
# Linux / macOS
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m taskbarnoob      # รันแอป
.venv/bin/python tests/run.py        # รันเทสต์ (ต้องผ่านทั้งหมด)
```

```powershell
# Windows (PowerShell)
py -3 -m venv .venv-win
.venv-win\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv-win\Scripts\python.exe -m taskbarnoob
.venv-win\Scripts\python.exe tests/run.py
```

> หมายเหตุเครื่องผู้ดูแลฝั่ง Linux Mint: venv ทำด้วย `--without-pip` · รันจากซอร์สอาจต้องมี `lib/libxcb-cursor.so.0` (เครื่องอื่นทั่วไปไม่จำเป็น)

## กติกาโค้ด

- **สถาปัตยกรรม:** `core/` = Python ล้วน **ห้าม import Qt** (ข้าม OS ได้ · แยก backend ใต้ `core/platform/{linux,win32}/`) · `gui/` = ส่วน PySide6
- **Type hints** ครบ (`from __future__ import annotations`) · PEP-8 · ไม่ใส่คอมเมนต์เยอะเกินจำเป็น
- **รีวัดการทำงานจริง:** รัน `tests/run.py` **ต้องผ่านทั้งหมดก่อนส่ง PR**
- **i18n (9 ภาษาในตัว):** คีย์หลักอยู่ใน `taskbarnoob/core/i18n/th.py` + `en.py` · **หากเพิ่ม/เปลี่ยนคีย์ต้องอัปเดตทุกไฟล์ใน `packaging/lang/*.json` (7 ภาษา)** ให้ครบ parity 100% (มีเทสต์เช็กอัตโนมัติ)
- **ไม่อัป binary/build/config เข้า repo** (`dist/`, `config/`, `*.AppImage`, `*.deb`, `*.zip` ถูก gitignore) — แนบเป็น GitHub **Release**
- **ห้าม commit secret/token/คีย์** เด็ดขาด

## แนวทาง PR (ย่อ)

- ไปตาม [`PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md): summary + checklist + notes
- commit message: สั้น อิมเพอเรทีฟ เช่น `fix: …` · `feat: …` · `docs: …`
- ปิดจบงาน: อัปเดต `docs/WORKLOG.md` (จบงาน) + `docs/feedback.md` (ถ้าปิดฟีดแบ็ก) + `AGENTS.md` (snapshot) · หากเป็นงานออกรุ่นให้ไล่เช็ก **Docs Audit Checklist** ใน [`docs/release-process.md`](docs/release-process.md) ด้วย
- CI (GitHub Actions) รันเทสต์อัตโนมัติทุก push/PR — รอให้เขียว 🟢

## จุดที่เทสต์ยาก (ขอความช่วยเหลือพิเศษ)

hotkey/การปักหมุด panel = **Cinnamon เท่านั้น** · ยังเทสต์ไม่ได้บนเครื่องผู้ดูแล: Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น
→ ถ้าใช้สภาพแวดล้อมเหล่านี้แล้วเจอปัญหาช่วยรายงานด้วยค่ะ

## สนับสนุน

ถ้าชอบและอยากเลี้ยงกาแฟ ☕ → https://ko-fi.com/neafong (ค่าใช้จ่ายเท่ากัน ทำฟรีตลอดไป)