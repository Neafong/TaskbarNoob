# Work Log — TaskbarNoob (v0.3.0+)

> บันทึกงานย้อนหลังต่อเฟส (append-only) · ประวัติภาค v0.1–v0.2 ถูกเก็บไว้ที่ [`archive/WORKLOG-v0.1-v0.2.md`](archive/WORKLOG-v0.1-v0.2.md)
> Snapshot ปัจจุบันอยู่ที่ [`../AGENTS.md`](../AGENTS.md) · แผนงานอยู่ที่ [`roadmap.md`](roadmap.md)

## 2026-11-23 — R0: จัดระเบียบเอกสาร (`docs/`) + แก้บั๊กเทสต์ฐานเดิมบน Mint `[เสร็จ]`
- **แก้บั๊กเทสต์บน Linux (`core/storage.py`):** เรียงผลลัพธ์ `self.groups_dir.iterdir()` ด้วย `sorted(..., key=lambda p: p.name.casefold())` ใน `ConfigStore._prune_order()` → `test_order_matches_disk_after_selfheal` ผ่านบน Linux ext4 (375 เทสต์ ผ่าน 100%, skipped 10 Windows-only)
- **จัดระเบียบ `docs/`:**
  - ย้าย `WORKLOG.md` (1,369 บรรทัด), `feedback.md` (~110 KB), `phase18-plan.md`, `windows-plan.md` ลง [`archive/`](archive/)
  - เริ่ม `docs/WORKLOG.md` และ `docs/feedback.md` ชุดใหม่สำหรับภาค `v0.3.0` ให้สั้นเบา ประหยัด token
  - อัปเดต `docs/README.md`, `docs/team.md`, `docs/roadmap.md` และ `AGENTS.md` ให้สะท้อนสถานะล่าสุด (`v0.2.0` ปล่อยแล้ว, workspace หลักบน Mint `/mnt/Backup/TaskbarNoob`, ทำงานร่วมกับเจนนี่)
- **ต่อไป:** เฟส **R1** — แยก Platform Backend เข้า `core/platform/{base,linux,win32}` + พับเก็บ `core/macos.py`
