# Feedback & Backlog — TaskbarNoob (v0.3.0+)

> งานค้าง/ฟีดแบ็กที่ยังไม่ปิด · ประวัติฟีดแบ็กภาค v0.1–v0.2 ถูกเก็บไว้ที่ [`archive/feedback-v0.1-v0.2.md`](archive/feedback-v0.1-v0.2.md)

## งานในรอบ v0.3.0 (ดูแผนเต็มใน [`roadmap.md`](roadmap.md))
- [ ] **R1:** แยก Platform Backend เข้า `core/platform/{base,linux,win32}` และพับเก็บ `core/macos.py`
- [ ] **R2:** แตกไฟล์ยักษ์ (`main_window.py`, `group_editor.py`, `win32.py`) ให้เล็กและมีหน้าที่เดียว
- [ ] **R3:** รวม Icon Pipeline เป็นจุดเดียว (ลบ circular import) + ตัวเลือกไอคอนระบบแบบแยกหมวดบน Linux Mint + Steam `steam://rungameid/<appid>` icon resolver ข้าม OS
- [ ] **R4:** เก็บกวาด Dead Code / แยก `i18n` + รีแบรนด์ชื่อภายใน `taskbargroups` → `taskbarnoob` พร้อม Auto-Migration + อัปเดตเครดิตเป็น `Noob & Jenny`

## รายการค้างระยะยาว (หลัง v0.3.0)
- **ไอคอน default ของกลุ่มที่ไม่ได้ตั้งไอคอน:** ปัจจุบันใช้ไอคอนโฟลเดอร์จากธีมระบบ (พี่ยังไม่ตัดสินใจว่าจะเปลี่ยนเป็นโลโก้แอปไหม — คงเดิมไว้ก่อน)
- **Linux DE / Display อื่น:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่นนอกเหนือจาก Cinnamon
- **macOS:** พับเก็บโค้ดออกก่อน — กลับมาพิจารณาเมื่อมีเครื่อง Mac จริงสำหรับพัฒนาและทดสอบ
- **คลิกขวา shortcut ใน flyout:** พักไว้ก่อน รอฟีดแบ็กจากผู้ใช้จริง
- **Windows `--list` จาก exe:** build เป็น `--windowed` ไม่มี stdout console — พิจารณาภายหลังถ้าจำเป็น
