# Pull Request

ขอบคุณที่ช่วยพัฒนา TaskbarNoob 🙏 ก่อนส่ง PR กรุณาเช็ค:

## รายละเอียด / Summary
- (PR นี้ทำอะไร · ปิด issue อะไร ถ้ามี — เช่น "Closes #12")

## ตรวจก่อนส่ง / Checklist
- [ ] รัน `python tests/run.py` แล้ว **ผ่านทั้งหมด**
- [ ] ตรวจ i18n: ถ้าเพิ่ม/แก้คีย์ใน `taskbarnoob/core/i18n/{th,en}.py` → อัปเดตทุกไฟล์ใน `packaging/lang/*.json` ให้ครบ parity
- [ ] ไม่มีไฟล์ build/config/binary หลุดเข้ามา (ดู `.gitignore`)
- [ ] อัปเดตเอกสารที่เกี่ยวข้อง (`docs/WORKLOG.md`, `README*.md`, `CONTRIBUTING.md`, `CHANGELOG.md` ตามความเหมาะสม)

## หมายเหตุ / Notes
- (อะไรที่ reviewer ควรรู้: จุดที่เทสต์ไม่ได้บนเครื่อง, ข้อจำกัด, snapshot)