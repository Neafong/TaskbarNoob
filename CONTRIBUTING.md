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
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m taskbargroups      # รันแอป
.venv/bin/python tests/run.py          # รันเทสต์ (ต้องผ่านทั้งหมด)
```

> หมายเหตุเครื่องนี้ (ของผู้ดูแล): venv ทำด้วย `--without-pip` · รันจากซอร์สอาจต้องมี `lib/libxcb-cursor.so.0` ในเครื่องอื่นไม่จำเป็น

## กติกาโค้ด

- **สถาปัตยกรรม:** `core/` = Python ล้วน **ห้าม import Qt** (ข้าม OS ได้) · `gui/` = ส่วน PySide6
- **Type hints** ครบ (`from __future__ import annotations`) · PEP-8 · ไม่ใส่คอมเมนต์เยอะเกินจำเป็น
- **รีวัดการทำงานจริง:** `.venv/bin/python tests/run.py` **ต้องผ่านก่อนส่ง PR**
- **i18n:** คีย์ base = `core/i18n.py` (TH) · เพิ่มคีย์ → ต้องอัปเดต `packaging/lang/ja.json` ให้ parity ด้วย
- **ไม่อัป binary/build/config เข้า repo** (`dist/`, `config/`, `*.AppImage`, `*.deb` ถูก gitignore) — แนบเป็น GitHub **Release**
- **ห้าม commit secret/token/คีย์** เด็ดขาด

## แนวทาง PR (ย่อ)

- ไปตาม [`PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md): summary + checklist + notes
- commit message: สั้น อิมเพอเรทีฟ เช่น `fix: …` · `feat: …` · `docs: …`
- ปิดจบงาน: อัปเดต `docs/WORKLOG.md` (จบงาน) + `docs/feedback.md` (ปิดฟีดแบ็ก) + `AGENTS.md` (snapshot)
- CI (GitHub Actions) รันเทสต์อัตโนมัติทุก push/PR — รอให้เขียว 🟢

## จุดที่เทสต์ยาก (ขอความช่วยเหลือพิเศษ)

hotkey/การปักหมุด panel = **Cinnamon เท่านั้น** · ยังเทสต์ไม่ได้บนเครื่องผู้ดูแล: Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น
→ ถ้าใช้สภาพแวดล้อมเหล่านี้แล้วเจอปัญหาช่วยรายงานด้วยค่ะ

## สนับสนุน

ถ้าชอบและอยากเลี้ยงกาแฟ ☕ → https://ko-fi.com/neafong (ค่าใช้จ่ายเท่ากัน ทำฟรีตลอดไป)