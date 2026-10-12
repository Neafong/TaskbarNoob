# Pull Request

ขอบคุณที่ช่วยพัฒนา TaskbarNoob 🙏 ก่อนส่ง PR กรุณาเช็ค:

## รายละเอียด / Summary
- (PR นี้ทำอะไร · ปิด issue อะไร ถ้ามี — เช่น "Closes #12")

## ตรวจก่อนส่ง / Checklist
- [ ] รัน `.venv/bin/python tests/run.py` แล้ว **ผ่านทั้งหมด**
- [ ] ตรวจ i18n: ถ้าแก้คีย์ใน `core/i18n.py` (TH base) → อัปเดต `packaging/lang/ja.json` ให้ parity
- [ ] ไม่มีไฟล์ build/config/binary หลุดเข้ามา (ดู `.gitignore`)
- [ ] อัปเดต `docs/WORKLOG.md` (ถ้าเป็นงานชุดใหม่)

## หมายเหตุ / Notes
- (อะไรที่ reviewer ควรรู้: จุดที่เทสต์ไม่ได้บนเครื่อง, ข้อจำกัด, snapshot)