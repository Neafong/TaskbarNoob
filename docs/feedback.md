# Feedback & Backlog — TaskbarGroups (Linux Mint)

> โน้ตฟีดแบ็กจากการใช้งานจริง + แผนเฟสถัดไป (ยังไม่เริ่มทำ)
> AGENTS.md เก็บ snapshot · docs/WORKLOG.md เก็บประวัติที่ทำเสร็จแล้ว · ไฟล์นี้เก็บ **งานค้าง/แผน**

## รอบทดสอบ #1 — AppImage (2026-10-10)
ผู้ใช้รัน `dist/TaskbarGroups-x86_64.AppImage` แล้วลองเพิ่มกลุ่ม

### ฟีดแบ็ก (F = feedback)
- **F1.** อยาก pin กลุ่มลง **Taskbar** ได้ทันทีตอนสร้างเสร็จ — หรือเพิ่มปุ่ม **"Pin"** ด้านขวาของแต่ละกลุ่มในหน้าต่างหลัก
- **F2.** อยาก **ดับเบิลคลิกไอคอนกลุ่ม** ในหน้าต่างหลัก → เข้าแก้ไขได้เลย (ตอนนี้ดับเบิลคลิก = เปิด flyout, มีปุ่ม "แก้ไข" แยก)
- **F3.** บน **Taskbar** อยากมีไอคอนของกลุ่มที่ pin ไว้ → **คลิกครั้งเดียว** เปิด popup (flyout) แสดงแอปในกลุ่ม
- **F4.** ค่า **ความโปร่งใส (opacity) default ควรเป็น 10%** (ตอนนี้ default 0)
- **F5.** UI ของ flyout:
  - พื้นหลังรอบนอกตอนนี้เป็น "4 เหลี่ยมสีขาว" → ควร **โปร่งแสง 100%** (เห็นทะลุ)
  - ข้างในมีสี่เหลี่ยม **มุมมน** เป็นพื้นหลังของ grid ไอคอน (มีอยู่แล้ว แต่ต้องให้เป็น BG เดียวกับที่โปร่ง)
  - **ขนาดไอคอนปรับได้** — default = ขนาดไอคอน taskbar จริง — มีตัวเลข/สไลเดอร์ปรับในหน้าต่างแก้ไขกลุ่ม

### หมายเหตุจากโค้ดปัจจุบัน (เช็กแล้ว)
- `core/models.py` `Group`: มี `width` (คอลัมน์ grid), `opacity`, `color_mode`, `custom_color`, `allow_open_all` — **ยังไม่มีฟิลด์ `icon_size`**
- `gui/flyout.py`: `WA_TranslucentBackground=False`, ไอคอน `setIconSize(48,48)` + ปุ่ม fix 84×84 (hardcode)
- `gui/main_window.py`: `itemDoubleClicked → on_open()` (flyout) · ปุ่มแถวล่างมี "แก้ไข" แล้ว · `install_launcher()` ติดตั้ง `.desktop` ได้
- `gui/group_editor.py`: มี spinbox `width` / `opacity` / สี / `allow_open_all` อยู่แล้ว → เพิ่ม `icon_size` ได้ง่าย
- Cinnamon: การ pin จริงลง panel ต้องผ่าน gsettings ของ applet (เช่น `org.cinnamon panel-launchers launchers`) หรือเขียน applet — ยังไม่ยืนยัน

## รอบ #2 — feedback เพิ่ม (2026-10-10)
- **F6.** ใช้ **สไลเดอร์** กับ **ความโปร่งใส** ด้วย (0–100 %) · default ยัง **10 %**
- **F7.** หน้าต่างแก้ไขกลุ่ม → "รายการ shortcut": ตอน Add อยาก **ลากวาง (drag & drop) จาก App** ที่เลือกได้เลย
- **F8.** "รายการ shortcut" ควรเป็น **Grid**:
  - เอาเมาส์ชี้ → โชว์ Path (tooltip)
  - **ดับเบิลคลิกไอคอน → แก้ไข**
  - **จัดลำดับ (reorder)** ของ App ได้
- **F9.** หน้าต่างหลัก (TaskbarGroups) จัดปุ่มใหม่:
  - **F9.1** ลบปุ่ม **"เปิดกลุ่ม"** ทิ้ง
  - **F9.2** ย้าย **"นำเข้ากลุ่ม"** ไปแทนตำแหน่งเดิมของ "เปิดกลุ่ม"
  - **F9.3** เพิ่มปุ่มรูป **เฟือง (Setup ⚙)** → ย้าย "ติดตั้ง launcher" + "ตั้ง hotkey" เข้าไปข้างใน

## รอบ #3 — feedback เพิ่ม (2026-10-10)
- **F10.** ปุ่มปักหมุด → เป็น **รูป Pin อยู่ท้ายสุดของแต่ละแถวกลุ่ม** (ด้านขวาสุด) แยกปุ่มต่อกลุ่ม (คลิกง่าย)
- **F11.** หน้าต่างหลัก → **สลับลำดับกลุ่ม** แต่ละแถวได้
- **F12.** ไอคอนใน "รายการ shortcut" (ที่ลากวาง):
  - **F12.1** ขนาด **เล็กเกินไป** → ขยายให้ใหญ่ขึ้น
  - **F12.2** ยัง **ดึงไอคอนจริงจากแอปที่ลากวางไม่ได้** → ต้องดึงไอคอนจริงมาแคช
- **F13.** หน้าต่างแก้ไข: **สีพื้นหลัง (mode) + สีกำหนดเอง รวมเป็นแถวเดียวกัน** แบ่งครึ่ง 2 คอลัมน์
- **F14.** ช่อง **ความโปร่งใส** และ **ขนาดไอคอน** ควร **พิมพ์ตัวเลข** ลงไปตรง ๆ ได้ (ไม่ใช่ลากสไลเดอร์อย่างเดียว)

## รอบ #4 — รายงานซ้ำ F10–F14 + ของใหม่ (2026-10-10)
ผู้ใช้ทดสอบ **AppImage** แล้วรายงานว่า F10–F14 ยังไม่เห็นผล + ปุ่ม pin ยังใช้ไม่ได้
- **สาเหตุ:** AppImage ที่ทดสอบเป็น build เก่า (16:59) ก่อนโค้ด Phase 8/9 (18:04+) →
  ฟีเจอร์มีครบในซอร์สแล้ว แต่ยังไม่ถูก repackage (แก้ที่ Phase 11)
- **F15.** ปุ่ม Pin ควรเป็น **toggle**: ปัก ↔ ถอนได้จากแถวเดียวกัน และโชว์สถานะให้เห็นทันที
  ว่าแถวไหนปัก/ยังไม่ปัก (ต่อยอด F10)

## รอบ #5 — ทดสอบหลัง Phase 11 (2026-10-10)
ผู้ใช้ทดสอบ AppImage ที่ rebuild แล้ว (Phase 11) — งานส่วนใหญ่ผ่าน (พิมพ์ opacity/ขนาด · สีรวม 2 คอลัมน์ · ปุ่ม pin toggle)
เหลือ 3 เรื่อง:
- **F16.** **ดึงไอคอนจริงจากแอป AppImage ไม่ได้** — ไฟล์ `.AppImage` ที่ลากวางยังไม่ขึ้นไอคอนจริง (ต่อยอด F12.2)
- **F17.** ไอคอนในตัวแก้ไขของกลุ่ม **Production** (ผูก `.AppImage`) **เล็ก** กว่ากลุ่ม **Game** (ผูก ELF) — ลบ/สร้างใหม่กี่รอบก็เล็กเท่าเดิม
- **F18.** **ลากสลับลำดับกลุ่ม** ในหน้าต่างหลักแล้ว **ไม่จำ** (เปิดใหม่ลำดับกลับเดิม — ต่อจาก F11)

## รอบ #6 — หลัง Phase 12 (2026-10-10)
ผู้ใช้ทดสอบ build หลัง Phase 12:
- ✅ **F18 ผ่าน** — ลากสลับลำดับกลุ่มในหน้าต่างหลักใช้ได้แล้ว
- ✅ **F17 ผ่าน** — ไอคอนกลุ่ม Production (ที่ผูก `.AppImage`) ขนาดใช้ได้แล้ว

ยังเจอ:
- **F19.** ไอคอนกลุ่มบน **Taskbar** (เช่น Game) → คลิกแล้ว **flyout ค้างซ้อนกัน 2–3 อัน**
  → ต้องเปิดได้ทีละอัน (single instance): ถ้ามีอยู่แล้วให้ปิด/เอากลับมาใช้ใหม่ ไม่สร้างซ้อน
- **F20.** ตำแหน่ง **flyout** ควรอยู่ **กึ่งกลางแนวนอน เหนือไอคอนกลุ่มที่คลิก** (ตอนนี้ไม่ตรง)
- **F21.** **ลากสลับไอเทมในกริด** (ตัวแก้ไขกลุ่ม): ตำแหน่งที่ปล่อย **เด้งไปมามั่ว คาดเดาไม่ได้**
  และ **วางแล้วไม่ตรงที่ปล่อย**
- **F22.** อยากให้ **ไฮไลท์ช่องกริดเป้าหมาย** ตอนลาก (ทั้งลากสลับในกริด + ลากไฟล์จาก file manager)
  → อยากได้แบบ **ไฮไลท์ทับช่องเป้าหมาย** · สี `Highlight` ธีม + มุมมน
- **F23.** แอปตอนนี้โทน **สีขาว** → อยากได้ **ตัวเลือกรูปแบบธีม** (อยู่ในปุ่มเฟือง Setup)
- **F24.** ปุ่ม **เฟือง (Setup)** ควรเด้ง **popup/หน้าต่างตั้งค่าใหม่** (รวม ธีม + ติดตั้ง launcher + ตั้ง hotkey)

**คำตอบเคาะเลือก (2026-10-10):**
- **F22 → เริ่มจากแนวทาง A** (ของ Qt ที่มีในตัว, `setDropIndicatorShown`) ก่อน — ยังไม่เห็นหน้าตา
  ถ้า UX ไม่ดีค่อยอัปเป็น custom ทีหลัง
- **F22 → ทั้งคู่** (ลากสลับในกริด + ลากไฟล์ข้างนอก) · **ไฮไลท์ทับช่องเป้าหมาย** · สี `Highlight` + มุมมน
- **F23/F24 → ธีมย้ายเข้า popup ของปุ่มเฟือง Setup**

**คำตอบเคาะเลือก รอบละเอียด (2026-10-10):**
- **F19.1 → ก.** คลิกกลุ่มเดิมซ้ำ = **โฟกัสอันเดิม ไม่เปิดใหม่** (กันกดรัวแล้วบั๊กค้าง)
- **F19.2 → ข.** เปิด**ทีละอัน** (เปิดกลุ่มใหม่ → ปิดอันเก่า)
- **F19.3 →** flyout **ปิดเองเมื่อคลิกที่อื่น** (focus-out)
- **F20.4 →** ใช้ **ตำแหน่งเมาส์ตอนคลิก** เป็นจุดอ้างอิง (กึ่งกลางแนวนอนเหนือจุดนั้น)
- **F20.5 →** ถ้าติดขอบจอให้ **เลื่อนหนีขอบ** (clamp ให้อยู่ในจอ)
- **F21 →** อาการเด้งมั่วเกิดตอน **สลับไอเทมในกริด** (internal reorder)
- **F23.6 →** โหมดธีม = **สว่าง / เข้ม / ตามระบบ (auto)** เท่านั้น
- **F23.7 →** ธีมมีผลกับ **ทั้งแอป** (หน้าต่างหลัก + แก้ไข + flyout) แต่ **ไม่ครอบคลุมไอคอน/ปุ่มบน Taskbar** (แยกส่วนกัน)
- **F24.8 →** คงฟังก์ชันเดิม + ทำ **หน้าต่างตั้งค่าใหม่** ที่มีตัวเลือก (ธีม / ติดตั้ง launcher / ตั้ง hotkey)
- **F24.9 →** เลือกธีมแล้ว **apply ทันที**

**ข้อสังเกตเชิงเทคนิค (F19):** ตอนเปิดจาก panel/launcher แอปถูกเรียกเป็น **process ใหม่ทุกครั้ง**
(`--open <group>`) → คลิกหลายครั้ง = หลาย process → flyout ซ้อนกันจริง
ดังนั้นการทำ "โฟกัสอันเดิม/ปิดอันเก่า" ต้องอาศัย **single-instance ข้าม process** (เช่น `QLocalServer`/`QLocalSocket`)
ไม่ใช่แค่เก็บ reference ใน object เดียว

**คำตอบสุดท้าย (2026-10-10) — เริ่มลงมือ:**
- **F19 → กันซ้อน 100%** (single-instance ข้าม process บังคับ) · คลิกกลุ่มเดิม = คงไว้/ยกขึ้น · เปิดทีละอัน · คลิกที่อื่นปิด
- **F20 → ระยะห่างเหนือเมาส์ 5–10px** (ใช้ ~6px) · กึ่งกลางแนวนอนที่ตำแหน่งเมาส์ · clamp ขอบจอ (ถ้าที่ไม่พอก็พลิกไปด้านล่าง)
- **F23.1 → default ธีม = auto (ตามระบบ)**
- **F23.2 → เก็บค่าไว้ใน `config/settings.json`** (portable)

## รอบ #7 — หลัง Phase 14 (2026-10-10)
ผู้ใช้ทดสอบ build หลัง Phase 14:
- ✅ **F19 ผ่าน** — flyout เป็น **single-instance ข้าม process** แล้ว (`QLocalServer`/`QLocalSocket`):
  คลิกไอคอนกลุ่มบน Taskbar ซ้ำๆ ไม่เกิดซ้อน · เปิดกลุ่มใหม่ → ปิดอันเก่า · คลิกกลุ่มเดิม = ยกขึ้น · คลิกที่อื่นปิด
- ✅ **F20 ผ่าน** — flyout จัดกึ่งกลางแนวนอนเหนือตำแหน่งเมาส์ (~6px) · clamp ไม่ล้นจอ (ไม่พอ → พลิกใต้)
- ✅ **F21 ผ่าน** — ลากสลับไอเทมในกริดวางตรงตำแหน่งที่ปล่อย (แทรกก่อน/หลังช่อง) · ลากทิ้งว่าง = ต่อท้าย
- ✅ **F22 ผ่าน** — ไฮไลท์ช่องกริดเป้าหมายทับช่องตามตำแหน่งปล่อยจริง (สี `Highlight` ธีม + มุมมน 10px)
- ✅ **F23 ผ่าน** — ธีม สว่าง/เข้ม/ตามระบบ (auto = default) มีผลทั้งแอป (หน้าต่างหลัก + แก้ไข + flyout) · ไม่รวมไอคอน/ปุ่มบน Taskbar
- ✅ **F24 ผ่าน** — ปุ่มเฟืองเปิด **หน้าต่างตั้งค่าใหม่** (ธีม apply ทันที + ติดตั้ง launcher + ตั้ง hotkey)

**เบี่ยงเบนจากสเปก (สำคัญ):**
- **F22:** เริ่มด้วยแนวทาง A ของ Qt (`setDropIndicatorShown`) — แต่พบว่า Qt มี `FIXME: Until we can provide a
  proper drop indicator in IconMode` → ไอคอนโหมด (IconView) **ไม่มี** drop indicator built-in ที่ใช้ได้
  จึง implement **ไฮไลท์ช่องเป้าหมายแบบ custom** ให้ตรงกับตำแหน่งปล่อยจริง (ตอนนี้ไม่พึ่ง Qt built-in)

**หมายเหตุเทคนิค:**
- F19: ห้ามตั้ง `self.window=None` ใน `_on_closed` ระหว่าง `closeEvent` — ปล่อย GC ทำลาย popup กลางเหตุการณ์
  → heap corruption (`Malloc: unaligned fastbin chunk`) · ต้อง `deleteLater()` แทน (ทำลายแบบ Qt-controlled ปลอดภัย)
- `dist/` rebuilt แล้ว (22:42 AppImage 61M · 22:43 .deb 51M) รวม Phase 14 ทั้งหมด
- เทสต์รวม **157 ผ่าน** (129 → +28: flyout 9 · grid drag 8 · settings/theme/dialog 11)

## รอบ #8 — หลัง Phase 14 (2026-10-10) — ธีมผ่าน ✅ + บั๊ก 1 ตัว + ฟีดแบ็ก UI + ไอเดีย i18n

> ✅ **ปิดครบแล้วใน Phase 15** — สเปกเต็ม & รายละเอียดที่ทำจริงอยู่ใน "ผลสรุป" ด้านล่าง

### 🐞 B1 — ลากสลับไอค่อนในกริด แล้วไอค่อนที่ลาก**หายไป** (ไม่สลับ)
- อาการ: กดไอค่อนแรกแล้วลากไปปล่อย → ไอค่อนที่ลาก **หายไปจากกริด** ไม่เกิดการสลับตำแหน่ง
- จุดทำงาน: `gui/group_editor.py` `ShortcutGrid.startDrag/dropEvent/_move_item` (โค้ด P14b)
- สาเหตุที่สงสัย (ยังไม่ยืนยัน): `_move_item` ทำ `takeItem(source)`+`insertItem` ด้วยตัวเอง แล้ว
  `event.acceptProposedAction()` (= MoveAction) → ตอน drag จริง Qt มี internal cleanup หลัง
  `drag.exec` (ใน `QAbstractItemViewPrivate::startDrag`) ที่อาจ remove source ซ้ำ → ไอค่อนหาย
- ⚠️ **เทสต์ปัจจุบันจับไม่ได้**: `tests/test_grid_drag.py` เรียก `dropEvent` ตรงๆ ไม่ผ่าน `super().startDrag`
  เลยไม่เห็นพฤติกรรมของ Qt ใน drag จริง (พยายามจำลองบน xcb แล้ว แต่ modal drag loop บังคับเหตุการณ์จริง)
- ทางแก้ที่ลอง: (A) ใน `dropEvent` ใช้ `source=self.currentRow()` อัปเดตล่าสุดแทนค่าเก่าที่เก็บไว้ใน `startDrag`
  หรือ (B) ให้ Qt จัดการ move เองทั้งหมดแล้วเอา manual ออก — ต้องลองบนเครื่องจริงแล้วล็อกตัวที่เสถียร
- เพิ่มเทสต์ให้แช่ `dropEvent` ผ่าน `startDrag` จริง (จำลองเหตุการณ์กด-ลาก-ปล่อยใน widget) ให้จับบั๊กนี้ได้ในครั้งหน้า

### หน้า "แก้ไขกลุ่ม" (GroupEditor) — ปรับ UI
- **2.1** ลบคำว่า **"ตัวอย่างไอคอน"** (แถว preview ที่เป็น QLabel) และ **"(ยังไม่ตั้ง)"** (label ข้อความของแถวไอคอนกลุ่ม)
- **2.2** ย้าย **รูปไอคอนโฟลเดอร์เหลือง (preview)** ไปไว้**แทนตำแหน่ง "(ยังไม่ตั้ง)"** →
  ยุบเป็นแถวเดียว: [พรีวิวไอคอน] [ปุ่มเลือก...] · ตัดแถวว่าง "ตัวอย่างไอคอน" ทิ้ง
- **2.3** ไอเดียผู้ใช้: เพิ่มปุ่ม **"เลือกไอคอนพื้นฐานของระบบ"** ให้รูปโฟลเดอร์เหลืองได้เปลี่ยนเป็นไอคอนธีมของระบบ
  → **ความเห็นน้องพริก: เห็นด้วย** — ทำเป็น dialog เลือกไอค่อนจากธีม (อ่านจาก `/usr/share/icons/...` /
  `QIcon.fromTheme` + ใช้กริดไอค่อนที่ reuse style เดียวกับ drag-highlight ของกริด) → ตั้งเป็น `group.icon` เหมือนเลือกไฟล์ปกติ
- **2.4** สไลด์เดอร์ "ขนาดไอคอน" ตอนนี้ขยายแค่**พรีวิวไอคอนกลุ่ม** → ควรควบคุม**ขนาดไอค่อนในกริด** (`ShortcutGrid`) ด้วย
  (มีอยู่แล้วเป็น field `group.icon_size` — แค่ยังไม่ผูกกับ grid)

### "จำนวนต่อแถว (width)" → ยุบ/ย้ายที่
- **3.1** เปลี่ยนชื่อ label เป็น **"แถว"** (สั้นดี)
- **3.2** พอ label สั้น คอลัมน์ฟอร์ม (ตั้งแต่ "ชื่อกลุ่ม" ถึง "ไอคอนกลุ่ม") จะได้พื้นที่ว่าง → ขยับ layout ได้
- **3.3** ถ้าจัดได้ ลองย้าย "แถว" **ขึ้นไปแถวเดียวกับ "ชื่อกลุ่ม"** (แถวบนหัวฟอร์มแบบ compact 2 คอลัมน์)

### Setup (เฟือง ⚙) — ภาษา (i18n)
- **4.1** เพิ่มฟังก์ชัน **สลับภาษา** เช่น ไทย ↔ English ในหน้าต่างตั้งค่า
- **4.2** **Export/Import ไฟล์ภาษา** ให้ผู้ใช้ใส่ภาษาเองได้ — ใช้ **JSON** เก็บค่า (ง่ายกว่า txt/ง่ายต่อโครงสร้าง)
- สถานะโค้ด: UI strings ไทยฮาร์ตโค้ดจจะทุกไฟล์ (`main_window/group_editor/flyout/settings_dialog/hotkey_dialog...`)
  → ต้องทำ pass รวบรวม key ทุกจุด → **งานใหญ่สุดของรอบนี้** · แนะนำทำเป็นชุด:
  `core/i18n.py` (dict `{key: {th, en}}` + `current()` + `tr(key)`) + `config/lang/` ให้อิมพอร์ต-เอ็กพอร์ต
  · ตั้งค่าใน SettingsDialog · เริ่มจาก UI ที่เห็นบ่อย 4 จอ (หน้าต่างหลัก · แก้ไขกลุ่ม · ตั้งค่า · flyout)

### ✅ ผลสรุป (Phase 15 เสร็จ 2026-10-10)
- **B1 ✅** — **ราก bug ล็อกชัดเจน** จากซอร์ส Qt 6.12 (รันจริง):
  `QIconModeViewBase::filterStartDrag` = `dropEventMoved=false` แล้ว `drag->exec(...)` → ถ้า
  `MoveAction && !dropEventMoved && (dragDropMode != InternalMove || target==viewport)` → **`clearOrRemove()`**
  ลบแถวที่**ถูกเลือก** (จะตั้ง `dropEventMoved=true` เฉพาะใน `QListView::dropEvent` ของ Qt — แต่ override เอง ไม่เรียก)
  · `_move_item` จบท้ายด้วย `setCurrentItem` = สร้าง selection → ถูก `clearOrRemove()` ลบ → ไอค่อนที่ลากหาย
  - **วิธีแก้:** ใน `dropEvent` หลัง `_move_item` เรียก `self.clearSelection()` → `clearOrRemove()` เห็น selection ว่าง = ไม่ลบอะไร
  - เพิ่มเทสต์ `test_internal_drop_leaves_selection_empty` (**บั๊กนี้จับได้จริง** — ยืนยัน pre-fix: selection ค้าง `['i0']` แล้ว fail, post-fix ว่าง)
    + หมายเหตุ: เทสต์พาดผ่าน `startDrag` จริงไม่ได้ (modal drag.exec บังคับเหตุการณ์จริง) → เทสต์ guard เงื่อนไข (selection-empty) ที่ทำให้ `clearOrRemove()` เป็น no-op
- **2.x ✅** — GroupEditor: ลบ "ตัวอย่างไอค่อน"(แถว preview) + "(ยังไม่ตั้ง)" · ยุบแถวไอค่อนเดียว
  [พรีวิว] [เลือกไอคอน...] [เลือกจากระบบ...] · พรีวิวโฟลเดอร์เหลืองย้ายมาแทนที่ "(ยังไม่ตั้ง)"
- **2.3 ✅** — ปุ่ม **"เลือกจากระบบ..."** เปิด `_SystemIconDialog`: กริดไอค่อนจากธีมระบบ (สแกน `/usr/share/icons`
  + `QIcon.themeSearchPaths`) + ช่องค้นหา (cap สแกน 4000 · แสดง 1000 — ชนิดเพื่อค้นหาเพิ่ม) · ดับเบิลคลิก/ปุ่มเลือก
  → ตั้งเป็น `group.icon` ผ่าน `icon_source()` เดิม (นำเข้าไปโฟลเดอร์กลุ่มจริง)
- **2.4 ✅** — สไลด์เดอร์ "ขนาดไอคอน" คุม **ขนาดกริด** ด้วย (`items_list.setIconSize` + `setGridSize` ตามค่า) ใช้ได้ทันที ไม่ต้องรอ reboot editor
- **3.x ✅** — label → **"แถว"** + ยกขึ้น**แถวเดียวกับ "ชื่อกลุ่ม"** (form แถวบน compact [ชื่อกลุ่ม][ชื่อ][แถว][n]) · ลบคอลัมน์ว่างทิ้ง
- **4.x ✅** — i18n:
  - `core/i18n.py`: dict `TH`/`EN` built-in + overlay `config/lang/<code>.json` + `tr(key, **fmt)` · `setup(lang)` เรียกใน `run()`
  - `settings.json` → key `language` (`Settings.get_language/set_language`)
  - `SettingsDialog`: แถว "ภาษา/Language" (ไทย/English/ภาษาผู้ใช้) + "ส่งออกภาษา..." (JSON) + "นำเข้าภาษา..." (JSON) ·
    เปลี่ยนภาษาแล้วเตือน "ใช้ภาษาถัดไปตอนเปิดแอปครั้งหน้า"
  - แปลครบ UI หลัก 5 จอ: หน้าต่างหลัก · แก้ไขกลุ่ม(+ShortcutDialog/+เลือกไอค่อนระบบ) · ตั้งค่า · flyout · hotkey
- **15e ✅** — repackage (ดูประวัติ/WORKLOG)

---

## รอบ #9 — หลัง Phase 15 (2026-10-11)

- ✅ **4.x ภาษา** — สลับภาษาได้แล้ว (ไทย ↔ English)
- ✅ **2.3 ไอค่อนจากระบบ** — เลือก/เปลี่ยนไอค่อนธีมได้แล้ว แต่...
  - 🐞 **N1 (ใหม่):** เปลี่ยนไอค่อน**ของกลุ่มที่ปักบน Taskbar อยู่** → ไอค่อนบน panel **ไม่ refresh** จนกว่าจะ**ถอนหมุดแล้วปักใหม่**
  - **สาเหตุ (ตรวจโค้ดแล้ว):** `install_launcher` เขียน Icon ใน `.desktop` เป็น **พาธไฟล์ไอค่อนตอนปัก**
    (`build_desktop_entry` → `store.resolve_relative(dir_name, group.icon)`) · พอแก้กลุ่ม → `import_group_icon`
    **ลบไฟล์เก่า (glob `group_icon.*`) แล้วเขียนไฟล์ใหม่** (นามสกุลอาจเปลี่ยน png→svg) → พาธเดิมใน .desktop ไม่มีจริง
    + applet จำ cache ไอค่อนเก่าไว้ → ต้องถอน/ปักใหม่ถึงสด
  - **แนวทางแก้ (ทำแล้ว — Phase 16a):** ใน `main_window._persist` ถ้ากลุ่มนี้**ถูกปักอยู่** (`desktop_id in pinned_desktop_ids()`)
    → หลังบันทึกไอค่อนใหม่ให้ **`install_launcher` ใหม่ (รีเจน Icon/Name)** + `reload_grouped_window_applet()` ผ่าน DBus
    · ข้อความ `MainWindow._refresh_pinned_icon` · เทสต์ +2 (regenerate launcher / skip เมื่อไม่ปัก) · **182 ผ่าน**
    · repackage รอรวมปลาย Phase 16 (16d)
  - (หมายเหตุ: เรื่องเดียวกันนี้ยังส่งผลตอน**เปลี่ยนชื่อกลุ่ม** — .desktop เก่า/พาธ dir เปลี่ยน → ควรปักใหม่ให้ applet ตามด้วย)
- ✅ **B1 ลากสลับกริดไอค่อน** — ใช้ได้แล้ว

### UI ยิบย่อย (จดเพิ่ม รอบ #9)
- **U1:** ไอค่อน**เฟือง (ปุ่ม Setup)** ในหน้าต่างหลักเล็กเกินไป → ขอใหญ่ขึ้นอีกนิด
  (ตอนนี้ `QPushButton("⚙")` = อักษรยูนิโค้ดขนาดตามฟอนต์ · วิธีแก้: ตั้งฟอนต์ตัวใหญ่ขึ้น + ปรับ `setFixedWidth(40)` →
  `48` หรือใช้ QIcon ธีมแก้สัดส่วน)
- **U2:** ไอค่อน**พินตอนปัก = สีฟ้า (`palette.Highlight`)** แถมไม่สวย เวลา**ไฮไลท์เลือกกลุ่ม (สีฟ้าเหมือนกัน) มันกลืน**
  → ขอธีม-aware: **ธีมดำ → สีขาว · ธีมขาว → เทาเข้ม** (ไม่แยกตาม Selected แต่แยกตาม Window ความสว่าง)
  - (`_paint_pin_shape` line 150-154 main_window.py: ตอนนี้ pinned=`Highlight`, unpinned=`Text@120`)
- **U3 (ตัดสินใจแล้ว 2026-10-11 — น้องพริกฟันธง + ผู้ใช้โอเค):** เปลี่ยนไอค่อนพินเป็น**รูปลูกตา (เปิด/ปิดตา)**
  - **ตาเปิด (เติมจอ) = ถูกปัก/โชว์บนทาสก์บาร์ · ตามิด (ขีดเปลือกตา) = ไม่ปัก/ซ่อน**
  - tooltip (th/en) เปลี่ยนเป็น "**แสดงบนทาสก์บาร์ / ซ่อนจากทาสก์บาร์**" สอดคล้องคำพูด (ไม่ใช้คำ "ปักหมุด")
  - วาดเองด้วย QPainter เหมือนเดิม (ต่อจาก `_draw_pin`/`_paint_pin_shape`) + สีธีม-aware (U2)
- หมายเหตุ U2/U3: ไอค่อนทั้งสองวาดเองด้วย QPainter (`_draw_pin`/`_paint_pin_shape`) แก้ได้ ไม่พึ่งไฟล์ธีม
- **U4 (ต่อ):** เฟืองยังอยากใหญ่ขึ้นอีก → **ตัดสิน: 28px** (จาก 20) · กว้าง 48 → 52 · **โค้ดทำแล้ว (16e)**
  · ขนาดเดิม `font.setPixelSize(20)` + `setFixedWidth(48)` (Phase 16c) แก้ที่เดียว `main_window.py` ปุ่ม `setup_button`
- **U5 (ใหม่):** ไอค่อน**แอป** TaskbarGroups ตอนโผล่บน Taskbar ยังเป็น**เฟือง (fallback)**
  - **สาเหตุ:** โค้ดไม่เคยตั้ง window/app icon เลย — ไม่มี `QApplication.setApplicationName` / `setDesktopFileName` /
    `setWindowIcon` → Cinnamon หา .desktop ไม่เจอเลยใช้ fallback (เฟือง) ทั้งที่ไฟล์จริง
    `packaging/appimage/taskbargroups.png` = **กรอบเขียว + ตาราง 6 ช่องขาว** (`packaging/make_icon.py`)
  - **แนวทางแก้:** ตั้ง `setApplicationName("TaskbarGroups")` + `setDesktopFileName("taskbargroups")`
    + `app.setWindowIcon()` (โหลด png ที่พกในแพ็กเกจผ่าน `--add-data` → `taskbargroups/assets/`)
    · โหลดด้วย helper ใน `core/paths.py` (source mode ใช้ `app_dir()/packaging/appimage/*.png`)
  - **สถานะ:** โค้ดทำแล้ว (Phase 16e) — `core/paths.app_icon_path()` + `setDesktopFileName` + `setWindowIcon` + `--add-data`
    · ยังไม่ build (รอรวม rebrand) · เทสต์ 186 ผ่าน
- **U5 ต่อ — ไอค่อนแอป/ชื่อแอป:** ผู้ใช้เป็นดีไซเนอร์จะออกแบบไอค่อนเอง
  - ~~ชื่อ "TaskGroup"~~ → **ผู้ใช้เสนอ "TaskbarNoob"** (Noob = แบรนด์ส่วนตัวของผู้ใช้) · **น้องพริกเช็คแล้วชื่อว่าง**
    (ค้น GitHub/PyPI/npm ไม่เจอโปรเจกต์ชื่อนี้)
  - **ความหมายแบรนด์ "Noob" (ผู้ใช้ยืนยัน):** ไม่ใช่เชิงลบ = **มือใหม่/น้ำไม่เต็มแก้ว** ถ่อมตน ไร้อีโก้ เรียนรู้/Level Up
    ได้ตลอด · ตั้งใจแจกฟรี + เป็น **เกราะกันดราม่า** ถ้ามีบั๊ก · แรงบันดาลใจจาก **เดกุ (My Hero Academia)**
    = "ไอ้กากที่พยายามจนเป็นฮีโร่" · แบรนด์ส่วนตัว: neafong.wixsite.com/noob-photo · flickr.com/photos/neafong
    · จะมี YouTube **"NoobGreaner"**
  - **มติเบื้องต้น:** ใช้ **"TaskbarNoob" เป็นชื่อที่แสดง (display name)** · **คง APP_ID = "taskbargroups" ไว้** ก่อน
    → พิน/`config` เดิมไม่พัง (`.desktop` ใช้ `setDesktopFileName` แยกจากชื่อแสดง) · จะเปลี่ยน id จริงค่อยทำ migration เฟสหลัง
  - **ไฟล์ที่ต้องการ:** **SVG** (พื้นโปร่งใส, อาร์ตบอร์ดจัตุรัส 512/1024) — rasterize เป็น 256/512/ไอคอนหน้าต่างได้เอง
    · ถ้า PNG → **1024×1024 โปร่งใส** · วาง `packaging/appimage/<appid>.png` (+ `.svg`)
  - **รอ SVG จากดีไซเนอร์** แล้วทำ Phase 19 (ชื่อ+ไอค่อน) รวม build กับ 16e ทีเดียว

### เบรนสตอร์มรอบ #9 — ผู้ใช้ขอเห็นด้วย **โดดทั้งหมด (ซื้อหมดเลย)**
- ✅ ไอเดียจดไว้ (รอแบ่งเฟส):
  1. **เมนูคลิกขวาที่กลุ่ม** (เปิด · แก้ไข · ปัก/ถอน · ตั้ง hotkey · ทำสำเนา · ลบ)
  2. **โชว์ hotkey ข้างชื่อกลุ่ม** (ในแถวกลุ่ม ถ้ามี)
  3. **ช่องค้นหา/กรองกลุ่ม**
  4. **ทำสำเนากลุ่ม (Duplicate)**
  5. **import/export ทั้งชุด config** (สำรอง/ย้ายเครื่อง)
- คำสั่งผู้ใช้: **จด + จัดลำดับงานให้ดี** แล้วขึ้นเซคชันใหม่ (Phase 17 เป็นต้นไป)

---

## รอบ #10 — หลัง P17e · ยืนยันหลัง reboot + สเปก UI รอบใหม่ (2026-10-11)

> ผู้ใช้ทดสอบ build หลัง P17e แล้วรายงาน + สั่งงาน UI เพิ่ม

### ✅ ยืนยันหลัง reboot (ปิดงานค้าง)
- **B2 ไอค่อน panel หายหลัง reboot** — ✅ ผ่าน (แก้ + self-heal ทำงาน)
- **B3 hotkey** — ✅ `Ctrl+Shift+G` ใช้ได้ · กด `Ctrl+Shift+P` ซ้ำ → **flyout กลุ่มเดิมยังอยู่ ไม่ซ้อน/ไม่หาย** (= F19 ยังดี)
- **ตาทoggle (U3)** — ✅ สถานะหลัง reboot ตรงกับ panel จริง
- **แก้ไอค่อน/ชื่อกลุ่มที่ปักอยู่ แล้ว reboot** — ✅ panel refresh เองถูกต้อง

### 🎨 งาน UI ที่สั่งเพิ่ม (ยังไม่ทำ)
- **A1 (About/TH) ✅ ทำแล้ว:** บรรทัดเครดิต **คงไว้ "สร้างโดย Noob & Pickle"** (ไม่แตะ) ·
  แก้แค่ `about.credits_note` (ฝั่ง TH) ให้เป็น **"ไอเดีย/ดีไซน์: นู๊บ · โค้ด: น้องพริก · แจกฟรี ทำด้วยใจ"**
  (ไทยล้วนเฉพาะบรรทัดนี้) · `settings.credits` คงเดิม
- **A2 (โดเนท) ✅ ทำแล้ว (2026-10-11):** ปุ่ม **"สนับสนุน ☕"** ในหน้าต่าง "เกี่ยวกับ" → เปิดเบราว์เซอร์ไปหน้า Ko-fi
  · ลิงก์ผู้ใช้: **https://ko-fi.com/neafong** (ชื่อเพจ "Noob" · ยืนยันเปิดได้แล้ว) · เก็บเป็น
  `Settings.get_donate_url()` (default `DEFAULT_DONATE_URL` ใน `core/settings.py`) — ถ้าว่าง = ซ่อนปุ่ม
  · เปิดผ่าน `QDesktopServices.openUrl`
- **E1 (Alignment):** ในหน้าต่างแก้ไขกลุ่ม — ช่อง **"ชื่อกลุ่ม" ควรชิดซ้ายตรงกับ** "สีพื้นหลัง / ความโปร่งใส /
  ขนาดไอคอน" (ปัจจุบันไม่ตรง เพราะ label "ชื่อกลุ่ม" ไปอยู่ในคอลัมน์ field ของแถวบนที่ compact
  `group_editor.py` ~479–487) · **น้องพริกเห็นด้วย = ควรจัดให้ตรง** (ย้าย label เข้าคอลัมน์ label ของ QFormLayout)
  · **✅ แก้แล้ว (2026-10-11)** — ย้าย label "ชื่อกลุ่ม" เข้าคอลัมน์ label ของ `QFormLayout`
- **E2 (ปุ่มมีไอคอน) ✅ ทำแล้ว (2026-10-11):** ผู้ใช้เคาะ = ใช้ **ไอคอนธีมระบบ** (`QIcon.fromTheme`) แทนอีโมจิ
  · ➕ เพิ่ม (`list-add`) · 📝 แก้ไข (`document-edit`) · 🗑️ ลบ (`edit-delete`) · ถ้าธีมไม่มีไอคอน → **fallback เป็นอีโมจิ**
  (ปุ่มเพิ่ม/แก้ไข/ลบ ในหน้าต่างแก้ไขกลุ่ม)

### 📌 มติรอบนี้
- **ตัดฟีเจอร์ "อนุญาตเปิดทั้งหมดพร้อมกัน" (open-all)** ✅ **ตัดแล้ว (2026-10-11)** — เพราะเปิดทุกแอปในกลุ่มพร้อมกันจริง =
  เครื่องสเปคต่ำจะหนัก · ขัดปรัชญา "เรียบง่ายที่สุด" · เป็นฟีเจอร์ยกจาก Windows ต้นฉบับ
  - **หมายเหตุเทคนิค:** Ctrl+Enter **ไม่ใช่ global hotkey** → ไม่ชนกันข้ามกลุ่ม (ทำงานเฉพาะตอน flyout เปิด)
  - แนวทาง: เอา checkbox/pุ่ม/"เปิดทั้งหมด"/Ctrl+Enter + i18n `editor.open_all`/`flyout.open_all*` ออก
    · **คง field `allow_open_all`** ใน `models.py`/`importer.py` ไว้ (config import จาก Windows เก่าโหลดได้)
- **คลิกขวา shortcut ใน flyout** (เปิดตำแหน่งไฟล์/แก้ไข) → **พักไว้** รอฟีดแบ็กผู้ใช้ที่โหลดไปใช้จริง
- **ดับเบิลคลิกว่างใน flyout → เปิดแก้ไขกลุ่ม** → **❌ ตัดออก** (ดูเยอะเกิน แอปควรเรียบง่าย)
- **ลำดับงาน:** ทำ **UI + แก้บั๊กให้ครบก่อน** → **Phase 18 (import/export zip) = งานหิน ทำหลังสุด**

---

## แผนเฟส (อัปเดต 2026-10-11 — U1–U3 + ไอเดียซื้อหมดแล้ว)

### Phase 6 — Settings & Flyout polish ✅ เสร็จ
(F2, F4, F5, F6, F9 + ปุ่ม "ปักหมุด" เบื้องต้น)

### Phase 7 — Shortcut editor เป็น Grid ✅ เสร็จ
(F7, F8 — grid + tooltip + dblclick แก้ไข + reorder + drag & drop)

### Phase 8 — UI polish รอบ 2 (Qt ล้วน) ✅ เสร็จ
(F10, F11, F12, F13, F14)
- **F10** ✅ ปุ่ม Pin ต่อแถว: ไอคอนเข็มหมุดท้ายสุดของแต่ละแถวในหน้าต่างหลัก (คลิกเปิด/ปักหมุด)
- **F11** ✅ สลับลำดับกลุ่มในหน้าต่างหลัก (ลากเรียง + `order.json`)
- **F12** ✅ ไอคอน shortcut ใน grid: F12.1 ใหญ่ขึ้น 64 px · F12.2 ดึงไอคอนจริงจากแอปที่ลากวางมาแคช
- **F13** ✅ รวมสีพื้นหลัง (mode) + สีกำหนดเอง เป็นแถวเดียว 2 คอลัมน์
- **F14** ✅ ช่อง opacity + icon size พิมพ์ตัวเลขได้ (spinbox ควบคู่สไลเดอร์)

### Phase 9 — Cinnamon panel integration (F1/F3 ของจริง) ✅ เสร็จ
เป้าหมาย: ไอคอนกลุ่มอยู่บน panel จริง → คลิกเดียวเปิด flyout
- **แนวทาง A (เบา):** `panel-launchers` ผ่าน gsettings ❌ ใช้ไม่ได้ (ค่าเป็น `['DEPRECATED']` แล้ว)
- **แนวทางที่ใช้จริง:** เขียน config JSON ของ **Grouped Window List applet**
  (`~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/<instance>.json` → key `pinned-apps`)
  แล้วสั่ง `org.Cinnamon.ReloadXlet <uuid> APPLET` ผ่าน DBus
- แก้ race + แก้ `Path=` ใน .desktop ให้คลิกแล้วเปิด flyout ได้จริง (ยืนยันบน Cinnamon 6.6.9)

### Phase 10 — Pin toggle & state (F15) ✅ เสร็จ
- `core/panel.py`: `pinned_desktop_ids()` · `is_pinned()` · `remove_grouped_window_pin()` · `unpin_from_panel()`
- `gui/main_window.py`: แถวกลุ่มโชว์สถานะปัก (ไอคอนเข็มหมุดติดสี Highlight) · คลิกเดียว = **toggle ปัก/ถอน** · tooltip บอกสถานะ
- เทสต์: เพิ่ม pin state/unpin (panel) + refresh ตั้งสถานะแถว (gui) → รวม **121 ผ่าน**

### Phase 11 — Repackage (F10–F15 ทั้งหมด) ✅ เสร็จ
- rebuild AppImage + `.deb` จากโค้ดล่าสุด (Phase 8/9/10) แล้วให้ผู้ใช้ทดสอบ
- `dist/TaskbarGroups-x86_64.AppImage` (61M) + `dist/taskbargroups_0.1.0_amd64.deb` (51M)

### Phase 12 — AppImage icon + group order fix (F16/F17/F18) ✅ เสร็จ
- **F16/F17** `core/icons.py`: เพิ่ม `is_appimage()` · `icon_from_appimage()` · `_extract_appimage_icon()`
  - แตกไฟล์ผ่าน `--appimage-extract` (ไม่ต้อง mount/FUSE) → หาไอคอนจาก `.DirIcon` → `Icon=` ใน `.desktop`
    ใน squashfs-root → ไฟล์รูปที่ใหญ่สุด · แคชใน temp (key = path+mtime+size)
  - ต่อเข้า `resolve_icon_source()` + `icon_from_executable()` → ลากวาง `.AppImage` = ได้ไอคอนจริง 256px
  - `gui/group_editor.py`: `_icon_for()` resolve ไอคอน AppImage ให้ item เดิมที่ยังไม่มีไอคอนด้วย
- **F18** `gui/main_window.py`: `GroupListWidget` เดิมต่อ `model().rowsMoved` — แต่ **QListWidget InternalMove
  ไม่ยิง rowsMoved** (ยิงแค่ `rowsInserted`/`rowsRemoved`) → ลำดับไม่ถูกบันทึก
  - เปลี่ยนเป็น override `dropEvent()` + `Signal orderChanged` → `MainWindow._on_rows_moved` บันทึก `order.json`
  - เพิ่ม `setDragEnabled`/`setDropIndicatorShown`/`setMovement(Snap)`
- เทสต์: +8 (AppImage detect/extract/resolve + orderChanged + save order) → รวม **129 ผ่าน**

### Phase 13 — Repackage (หลัง Phase 12) ✅ เสร็จ
- rebuild AppImage + `.deb` จากโค้ด Phase 12 (20:22–20:23) แล้วให้ผู้ใช้ทดสอบ
- หมายเหตุ: รอบ #6 มาจาก build นี้

### Phase 14 — Flyout & drag UX + ธีม (F19–F24) ✅ เสร็จ (2026-10-10)
- **14a — Flyout UX (F19/F20) ✅** `gui/flyout.py`:
  - `FlyoutController`: single-instance ข้าม process (`QLocalServer`/`QLocalSocket` + `default_server_name`)
  - เปิดกลุ่มใหม่ → ปิดอันเก่า · คลิกกลุ่มเดิม = ยกขึ้น · ปิดเมื่อคลิกที่อื่น (focus-out/hide → `flyout_position`)
  - จัดกึ่งกลางแนวนอนเหนือตำแหน่งเมาส์ ~6px (`MOUSE_OFFSET`) + clamp ขอบจอ / พลิกใต้เมื่อไม่พอ
- **14b — Grid drag UX (F21/F22) ✅** `gui/group_editor.py` `ShortcutGrid` เขียนใหม่:
  - custom reorder: `_target_row(pos)`, `_move_item(source, target)` → วางตรงตำแหน่งปล่อย · ลากทิ้งว่าง = ต่อท้าย
  - `_DropHighlightDelegate` **ไฮไลท์ช่องเป้าหมาย** สี `Highlight` + มุมมน 10px (ตามตำแหน่งปล่อยจริง)
  - ⚠️ **แนวทาง A ของ Qt ไม่เวิร์ก** (Qt source มี `FIXME: no proper drop indicator in IconMode`)
    → ทำ custom แทน (ดูรายละเอียดในรอบ #7)
- **14c — Theme + Settings dialog (F23/F24) ✅** `core/settings.py` (config/settings.json · auto/light/dark):
  - `gui/theme.py` `resolve_theme()`/`apply_theme()` ผ่าน QPalette (auto อ่าน `styleHints().colorScheme()`)
  - `gui/settings_dialog.py` `SettingsDialog`: ธีม apply ทันที + ปุ่มติดตั้ง launcher/ตั้ง hotkey (ต่อฟังก์ชันเดิม)
  - `run()` ใช้ธีมตั้งแต่บูต · เฟือง ⚙ เปิด dialog แทน QMenu
- **14d — Repackage ✅** rebuild AppImage + `.deb` (22:42–22:43) แล้วให้ผู้ใช้ทดสอบ → ผ่านทั้งหมด

### Phase 15 — Bug + UI compact + i18n (B1 · 2.x · 3.x · 4.x) ✅ เสร็จ (2026-10-10)
- **15a — Fix B1 ✅** ราก bug = Qt `clearOrRemove()` หลัง `MoveAction` เมื่อ `dropEventMoved=false` (เพราะ override dropEvent)
  ลบแถวที่ถูกเลือก → แก้โดย `clearSelection()` ใน `dropEvent` + เทสต์ guard ใหม่ (รายละเอียดใน "ผลสรุป" รอบ #8)
- **15b — Group editor UI ✅** ลบ "ตัวอย่างไอค่อน"/"(ยังไม่ตั้ง)" · พรีวิวแถวเดียวกับปุ่มเลือก ·
  ปุ่ม **"เลือกจากระบบ..."** (`_SystemIconDialog` — กริดธีม + ค้นหา) · สไลเดอร์ขนาดไอคอนคุมขนาดกริดจริง
- **15c — Width compact ✅** label → "แถว" · ย้ายขึ้นแถวเดียวกับ "ชื่อกลุ่ม"
- **15d — i18n ✅** `core/i18n.py` (TH/EN built-in + `config/lang/*.json` overlay) · `settings.json` key `language` ·
  SettingsDialog: สลับภาษา + ส่งออก/นำเข้าภาษา JSON · แปลครบ 5 จอ UI
- **15e — Repackage ✅** rebuild AppImage + `.deb` แล้วให้ผู้ใช้ทดสอบ
  · เทสต์ **180 ผ่าน** (157 → +23: group editor UI 9 · grid drag selection 1 · i18n 13)

### Phase 16 — UI ยิบย่อย + auto-refresh pin (N1 · U1 · U2 · U3)
- **16a — N1 auto-refresh ✅ เสร็จแล้ว** (ทำในรอบ #9): `MainWindow._refresh_pinned_icon`
  = ถ้ากลุ่มถูกปัก → `install_launcher` ใหม่ + `reload_grouped_window_applet()` · เทสต์ +2 → **182 ผ่าน**
- **16b — U3 ตัดสินใจ ✅ "ตาเปิด/ปิด"** (ฟันธง 2026-10-11) + tooltip th/en = "แสดง/ซ่อนบนทาสก์บาร์"
- **16c — U1 + U2 + U3 วาดจริง ✅ เสร็จ (2026-10-11):**
  - U3 `_paint_pin_shape` → ตาเปิด (ม่านตา)/ตามิด (ขีด) · U2 `_status_color` = Base สว่าง→เทาเข้ม / มืด→ขาว (ไม่ใช้ Highlight)
  - U1 เฟือง pixel 20 + กว้าง 48 · tooltip "กำลังแสดงบนทาสก์บาร์ / ซ่อนจากทาสก์บาร์" (th/en) · เทสต์ +2 → **184 ผ่าน**
- **16d — Repackage ✅ เสร็จ (2026-10-11, 01:57):** rebuild AppImage (61M) + `.deb` (51M) · boot `--list` OK ·
  ตรวจ PYZ มี `_refresh_pinned_icon`/`_status_color`/`drawEllipse` + tooltip ใหม่ครบ · `dist/config` intact
- **16e + Phase 19 Rebrand — build ✅ เสร็จ (2026-10-11, 04:02–04:03):**
  - **16e:** U4 เฟือง 28px (กว้าง 52) · U5 `app_icon_path()` + `setApplicationName/DisplayName` + `setDesktopFileName`
    + `setWindowIcon` + `--add-data` ฝัง png · เทสต์ 186 ผ่าน
  - **19 (rebrand):** ชื่อที่แสดง = **"TaskbarNoob"** (i18n `app.title` TH/EN · `.desktop` `Name=`/`StartupWMClass` · appdata)
    · **คง APP_ID `taskbargroups`** (พิน/`config` เดิมไม่พัง) · ไอค่อนใหม่จาก `Logo TG.svg` —
    เพิ่ม `packaging/render_icon.py` (SVG→PNG ด้วย Qt) + `taskbargroups.svg` + build script rasterize อัตโนมัติ
  - **ผลลัพธ์:** `dist/TaskbarNoob-x86_64.AppImage` (61M) + `dist/taskbargroups_0.1.0_amd64.deb` (51M) ·
    boot `--list` OK · md5 ไอค่อนตรงกับโลโก้ · PYZ มี `TaskbarNoob`/`app_icon_path`/`setWindowIcon` · `dist/config` intact
  - หมายเหตุ: APP_ID ข้างในยัง `taskbargroups` (`.deb`/โฟลเดอร์/`Exec=`) — ยังไม่ rename ตัว id

### Phase 17 — เมนูคลิกขวา + hotkey ข้างชื่อ + เครดิต
- **17a — Context menu ที่กลุ่ม ✅ เสร็จ (2026-10-11):** `GroupListWidget.contextMenuEvent` → สัญญาณ
  `contextMenuRequested(globalPos)` → `MainWindow._group_context_menu(dir_name)` (เปิด · แก้ไข · ปัก/ถอน ·
  ตั้ง hotkey · ทำสำเนา · ลบ) · คลิกขวาเลือกแถวนั้นอัตโนมัติ · กดที่ว่างไม่ทำอะไร
- **17b — โชว์ hotkey ข้างชื่อกลุ่ม ✅ เสร็จ (2026-10-11):** อ่าน gsettings custom-list + `binding` ของแต่ละ slot
  (`core/hotkeys.py` `hotkey_slot`/`group_hotkeys`/`cinnamon_to_display`) → ต่อท้ายชื่อกลุ่มเป็น "· คีย์: Ctrl+Alt+T"
  · `MainWindow.refresh` อัปเดตทุกครั้ง · `HotkeyDialog` ใช้ `hotkey_slot` ร่วมกัน
- ~~**17c — ช่องค้นหา/กรองกลุ่ม**~~ **❌ ตัดออก (ผู้ใช้ตัดสิน 2026-10-11):** คนใช้จริงมีกลุ่มไม่ถึง ~10
  และอยากให้ Taskbar ดูสะอาด → ช่องค้นหามีไว้ก็รกเกินจำเป็น
- **17d — Duplicate กลุ่ม ✅ เสร็จ:** `ConfigStore.duplicate_group(src, new_name?)` (copytree + ตั้งชื่อใหม่ +
  ต่อท้าย order + unique กันชน) · เมนูคลิกขวาเรียกผ่าน `MainWindow.on_duplicate`
- **17f — เครดิต "Noob & Pickle" ✅ เสร็จ (2026-10-11):** `gui/about_dialog.py` (โลโก้+ชื่อ+เวอร์ชัน+เครดิต) ·
  ปุ่มเฟืองเป็นเมนู (ตั้งค่า/เกี่ยวกับ) · ป้ายเครดิตท้าย `settings_dialog.py` ·
  `<developer><name>Noob &amp; Pickle</name>` ใน appdata · i18n `menu.*`/`about.*`/`settings.credits`
- **17e — Repackage ✅ เสร็จ (2026-10-11, 12:47):** AppImage (61M) + `.deb` (51M) · boot `--list` OK ·
  PYZ มี `about_dialog`/`_sync_pinned_launchers`/`hotkey_slot`/`set_binding_command`/`_format_gvariant_string`/`_touch_custom_list`/`set_bindings_command`/`install_launcher_icon` + "Noob & Pickle" ครบ ·
  **fix B3 hotkey ทั้งหมด (schema · GVariant · ordering · ถอนคีย์ไม่จริง)** รวมในบิลด์นี้ · `dist/config` intact

### Phase 18 — Import/Export ทั้งชุด config (สำรอง/ย้ายเครื่อง) — **งานหิน · ทำหลังสุด**
- export: zip {groups/*, order.json, settings.json} → `.taskbargroups` ย้ายเครื่องได้
- import: สแกน + backup ของเดิมก่อน (ไม่ควรชนข้อมูลจริงบน dist/config) · UI ใน Settings/หน้าต่างหลัก
- repackage สุดท้าย + อัปเดต docs
- **มติ 2026-10-11 (รอบ #10):** ให้ทำ **UI + แก้บั๊กทั้งหมดให้ครบก่อน** แล้วค่อยปิดท้ายด้วย Phase 18

---

## ไอเดียเพิ่มเติม (น้องพริกเสนอ — ยังไม่ยืนยัน)
- ✅ *5 รายการแรกถูกผู้ใช้ "ซื้อหมดเลย" แล้วที่รอบ #9 (ย้ายไปแผนเฟส Phase 17/18)*
- **เมนูคลิกขวาที่กลุ่ม** ในหน้าต่างหลัก (เปิด/แก้ไข/ปักหมุด/ตั้ง hotkey/ทำสำเนา/ลบ) — ช่วยเรื่อง F2/F9 และลดปุ่มบนหน้าจอ ✅ → P17a
- **โชว์ hotkey ข้างชื่อกลุ่ม** ในลิสต์ (เห็นปุ๊บรู้ว่ากลุ่มไหนผูกคีย์อะไร) ✅ → P17b
- ~~**ช่องค้นหา/กรองกลุ่ม** เมื่อมีกลุ่มเยอะ~~ ❌ **ตัดออก** (ผู้ใช้ตัดสิน 2026-10-11: กลุ่มไม่ถึง 10 อยากให้ Taskbar สะอาด)
- **ทำสำเนากลุ่ม (Duplicate)** ไว้ตั้งหลายๆ variant ✅ → P17d
- **ใส่เครดิตผู้สร้าง "Noob & Pickle"** (About/ท้าย Settings) ✅ → P17f
- **Import/Export ทั้งชุด config** (สำรอง/ย้ายเครื่อง — ต่อยอดความ portable) ✅ → P18 **(งานหิน — ทำหลังสุด)**
- **โหมดธีมตามระบบ (auto light/dark)** เพิ่มจาก dark/light/custom
- **ใน flyout คลิกขวา shortcut** → เปิดตำแหน่งไฟล์ / แก้ไข — ⏸️ **พักไว้** (รอฟีดแบ็กผู้ใช้จริง) (รอบ #10)
- ~~**ดับเบิลคลิกว่างๆ ใน flyout** → เปิดตัวแก้ไขกลุ่ม~~ ❌ **ตัดออก** (แอปควรเรียบง่าย — รอบ #10)
- **ปุ่มโดเนทในหน้าต่าง About** (รอบ #10 — ✅ ทำแล้ว · Ko-fi `ko-fi.com/neafong`)
- **ไอคอนหน้าปุ่ม** (➕เพิ่ม/📝แก้ไข/🗑️ลบ) — ใช้ไอคอนธีมระบบ ✅ ทำแล้ว (รอบ #10)

---

## Decisions (ยืนยันแล้ว 2026-10-10)
- **F2 → ดับเบิลคลิก = แก้ไข** และ **เก็บปุ่ม "แก้ไข" ไว้ด้วย**
- **F5 ขนาดไอคอน → fix default 32 px** ไปก่อน (ค่อยมาดึง gsettings ทีหลังถ้าต้องการ)
- **F1/F3 Pin → ลอง pin อัตโนมัติ** ผ่าน Cinnamon gsettings + ถ้าล้มเหลว fallback เป็น "ติดตั้ง launcher ให้ลากเอง"
- **F4/F6 → ใช้สไลเดอร์** กับ opacity (0–100 %) · default **10 %**
- **F9 → จัดปุ่มหน้าต่างหลักตามที่ระบุ** (ลบ "เปิดกลุ่ม" · ย้ายนำเข้า · เพิ่มเฟือง Setup)
- **F9.1 → หน้าต่างหลักไม่ต้องมีปุ่มเปิด flyout** — flyout เปิดจาก **ปุ่มกลุ่มที่ pin บน taskbar** แทน (ปุ่ม Pin อยู่ Phase 6, ตัวเปิดจาก panel อยู่ Phase 8)
  - ⚠️ ช่วงก่อน Phase 8 เสร็จ: เปิด flyout ทดสอบได้ทาง CLI `--open` / hotkey ไปก่อน
- **F7 → drag & drop จาก file manager** (ลากไฟล์/ไอคอนเข้ามาเพิ่ม shortcut อัตโนมัติ) ยืนยันแล้ว
- **F22 → เริ่มแนวทาง A (ของ Qt)** `setDropIndicatorShown` ก่อน — ยังไม่เห็นหน้าตา ถ้า UX ไม่ดีค่อยทำ custom
  · ใช้ทั้งลากในกริด + ลากไฟล์จากข้างนอก · ไฮไลท์ทับช่องเป้าหมาย (ไม่ใช่เส้นแทรก) · สี `Highlight` ธีม + มุมมน
  · ⚠️ **แล้วต้องทำ custom ตามที่วางแผนไว้** (Qt IconMode ไม่มี drop indicator ที่ใช้ได้ — มี FIXME ในซอร์ส Qt)
    — ทำใน Phase 14b แล้ว
- **F23/F24 → ธีม + เมนูตั้งค่า ย้ายเข้า popup ของปุ่มเฟือง Setup**

## ลำดับที่เสนอ (ปรับ 2026-10-10)
- **Phase 6 → 7 (เสร็จ) → 8 (UI polish F10–F14) → 9 (Cinnamon panel + เปิด flyout ท้ายสุด)**
- หมายเหตุเดิม: flyout เปิดจาก taskbar (F3) จะยังทดสอบทาง GUI ไม่ได้จนถึง Phase 9 → ใช้ CLI `--open` / hotkey ไปก่อน

---

## สถานะความคืบหน้า
- ✅ **F2** ดับเบิลคลิก = แก้ไข (Phase 6)
- ✅ **F4 / F6** opacity default 10 % + สไลเดอร์ 0–100 % (Phase 6)
- ✅ **F5** flyout โปร่งแสงรอบนอก + สี่เหลี่ยมมุมมน + สไลเดอร์ขนาดไอคอน (default 32 px) + preview (Phase 6)
- ✅ **F9** จัดปุ่มหน้าต่างหลัก (ลบ "เปิดกลุ่ม" · ย้าย "นำเข้ากลุ่ม" · เพิ่มเฟือง ⚙ Setup) (Phase 6)
- ✅ **F7** drag & drop ไฟล์จาก file manager เข้ามาเพิ่ม shortcut (Phase 7)
- ✅ **F8** "รายการ shortcut" เป็น Grid + tooltip path + dblclick แก้ไข + ลากสลับลำดับ (Phase 7)
- ✅ **F10** ปุ่มปักหมุดเป็นไอคอนเข็มหมุดท้ายสุดของแต่ละแถว (Phase 8)
- ✅ **F11** สลับลำดับกลุ่มในหน้าต่างหลัก + บันทึก `order.json` (Phase 8)
- ✅ **F12** ไอคอน grid ใหญ่ขึ้น 64 px + ดึงไอคอนจริงจากแอปที่ลากวางมาแคช (Phase 8)
- ✅ **F13** รวมสีพื้นหลัง (mode) + สีกำหนดเอง เป็นแถวเดียว 2 คอลัมน์ (Phase 8)
- ✅ **F14** ช่อง opacity/icon size พิมพ์ตัวเลขได้ (spinbox ควบคู่สไลเดอร์) (Phase 8)
- ✅ **F1** ปุ่ม "ปักหมุด" + ปักหมุดลง **Grouped Window List จริง** บน Mint (Phase 9)
  · แก้ `pinned-apps` ของ applet + `ReloadXlet` · แก้ `Path=` ให้คลิกเปิด flyout ได้
- ✅ **F3** ไอคอนกลุ่มบน taskbar คลิกเดียวเปิด flyout (Phase 9 — ยืนยันบน Cinnamon 6.6.9)
- ✅ **F15** ปุ่ม Pin เป็น toggle ปัก/ถอน + โชว์สถานะปักบนแถวกลุ่ม (Phase 10)
- ✅ **F16** ดึงไอคอนจริงจาก `.AppImage` (แตก squashfs → `.DirIcon`/`Icon=` → แคช) (Phase 12)
- ✅ **F17** ไอคอนกลุ่มที่ผูก `.AppImage` ได้ไอคอนจริง 256px ไม่เล็กอีก (แก้คู่กับ F16) (Phase 12)
- ✅ **F18** ลากสลับลำดับกลุ่มแล้วบันทึกจริง (override `dropEvent`, เลิกพึ่ง `rowsMoved`) (Phase 12)
- ✅ **F19** flyout single instance ข้าม process (`QLocalServer`) — ไม่ซ้อน ไม่ค้าง (Phase 14)
- ✅ **F20** flyout กึ่งกลางแนวนอนเหนือไอคอนที่คลิก ~6px + clamp/พลิกใต้ (Phase 14)
- ✅ **F21** ลากในกริดวางตรงตำแหน่งปล่อย (แทรกก่อน/หลังช่อง · ว่าง = ต่อท้าย) (Phase 14)
- ✅ **F22** ไฮไลท์ช่องกริดเป้าหมาย — custom (สี Highlight + มุมมน 10px) (Phase 14)
- ✅ **F23** ธีม สว่าง/เข้ม/ตามระบบ (auto = default) มีผลทั้งแอป (Phase 14)
- ✅ **F24** หน้าต่างตั้งค่าจากปุ่มเฟือง Setup (ธีม apply ทันที + launcher + hotkey) (Phase 14)
- ✅ **B1** ลากสลับไอค่อนในกริดไม่หายอีก (ราก = Qt `clearOrRemove` — แก้ `clearSelection` ใน dropEvent) (Phase 15)
- ✅ **2.x** แก้ไขกลุ่ม UI: ลบ label ตัวอย่าง/(ยังไม่ตั้ง) · พรีวิวแถวเดียวกับปุ่ม · ปุ่มเลือกไอค่อนระบบ · สไลเดอร์คุมกริด (Phase 15)
- ✅ **3.x** label "แถว" + ย้ายแถวเดียวกับ "ชื่อกลุ่ม" (Phase 15)
- ✅ **4.x** i18n ไทย/อังกฤษ + export/import ภาษา JSON (`config/lang/`) (Phase 15)
- ✅ **B2** ไอค่อนกลุ่มบน Taskbar หายหลัง reboot (ราก = `Icon=<path>` ชี้ไดรฟ์ที่ mount ทีหลัง →
  ติดตั้งไอคอนเข้า hicolor theme + `Icon=<launcher_id>` + self-heal `_sync_pinned_launchers`) (หลัง Phase 16e)
- ✅ **B3** กดตั้ง hotkey แล้วขึ้น "ไม่มี schema" (ราก = schema ผิดพหูพจน์ + `binding` เป็น type `as` ไม่ใช่ string) —
  แก้เป็น `org.cinnamon.desktop.keybindings.custom-keybinding` + set `['<binding>']` · **ต่อมาเจอ `expected end of input`**
  เพราะ `name`/`command` ไม่ได้ห่อ GVariant string literal → เพิ่ม `_format_gvariant_string` ·
  **ต่อมาเจอ "คีย์โชว์แต่กดไม่ทำงาน"** เพราะ set ค่าก่อน/หลังสลับกัน — Cinnamon rebuild เฉพาะตอน `custom-list` เปลี่ยน
  → set name/command/binding ก่อน แล้ว "แตะ" list (dummy) ทีหลัง
- ✅ **ถอนคีย์ลัด** (ผู้ใช้ขอ): ปุ่ม "ถอนคีย์ลัด" ใน dialog (โหลดคีย์เดิมมาโชว์) · ลบกลุ่ม = ลบคีย์อัตโนมัติ ·
  **"ถอนแล้วยังกดได้"** เพราะ `remove_custom_keybindings()` ของ Cinnamon ลบเฉพาะชื่อที่มี `custom`
  (slot เรา `taskbargroups-*` ไม่เข้าเงื่อนไข) → แก้: set `binding=[]` ขณะ slot ยังอยู่ใน list แล้วแตะ list
  ให้ Cinnamon สั่ง `remove_keybinding` จริง ก่อนถอดออกจาก list (ตรวจ live ผ่าน `org.Cinnamon.Eval` แล้ว)

---

## ประวัติ
- 2026-10-10 — รับฟีดแบ็กชุดแรกจาก AppImage (F1–F5) · ยังไม่เริ่มแก้
- 2026-10-10 — เคาะ Decisions 3 ข้อแล้ว (F2 dblclick=แก้ไข · F5 default 32px · F1/F3 ลอง pin อัตโนมัติ) · รอเริ่ม Phase 6
- 2026-10-10 — รับฟีดแบ็กเพิ่ม F6–F9 (สไลเดอร์ opacity · drag&drop · shortcut เป็น Grid · จัดปุ่มหน้าต่างหลัก + เฟือง Setup) · ปรับแผนเป็น Phase 6/7/8 + เพิ่มไอเดียน้องพริก
- 2026-10-10 — เคาะ F9.1 (flyout เปิดจากปุ่มกลุ่มบน taskbar ไม่ต้องมีในหน้าต่างหลัก) · F7 = ลากจาก file manager · พร้อมเริ่ม Phase 6
- 2026-10-10 — Phase 6 เสร็จ (สไลเดอร์/โปร่งแสง/จัดปุ่ม/ปุ่มปักหมุด)
- 2026-10-10 — Phase 7 เสร็จ (shortcut เป็น Grid + drag & drop + reorder)
- 2026-10-10 — รับฟีดแบ็ก F10–F14 (Pin ต่อแถว · สลับลำดับกลุ่ม · ไอคอน grid ใหญ่+ดึงจริง · รวมสี 2 คอลัมน์ · พิมพ์ตัวเลขได้)
  · **เลื่อน Cinnamon panel ไปท้ายสุด (Phase 9)** · เพิ่ม **Phase 8 = UI polish รอบ 2** · ยังไม่เริ่มแก้
- 2026-10-10 — **Phase 8 เสร็จ** (F10–F14) · เหลือ **Phase 9 (Cinnamon panel + เปิด flyout ท้ายสุด)**
- 2026-10-10 — **Phase 9 เสร็จ** (F1/F3) · ปักหมุดลง Grouped Window List จริง + คลิกเปิด flyout ได้
  · แก้ `Path=` ใน .desktop + bundling libxcb-cursor สำหรับรัน source · ฟีดแบ็ก F1–F14 ครบทั้งหมด
- 2026-10-10 — รายงานซ้ำ F10–F14 จากผู้ใช้ · พบว่าเกิดจาก **AppImage เป็น build เก่า** (ยังไม่ repackage)
  · เพิ่ม **F15 = ปุ่ม Pin toggle + โชว์สถานะ** · **Phase 10 เสร็จ** · เหลือ **Phase 11 = rebuild แพ็กเกจ**
- 2026-10-10 — **Phase 11 เสร็จ** (rebuild AppImage + .deb)
- 2026-10-10 — ทดสอบหลัง Phase 11 · เจอ F16–F18 (ไอคอน AppImage · ไอคอนเล็ก · ลากสลับลำดับกลุ่มไม่จำ)
  · **Phase 12 เสร็จ** (extract ไอคอนใน AppImage + override `dropEvent` บันทึกลำดับ) · เทสต์ 129 ผ่าน
- 2026-10-10 — **Phase 13 เสร็จ** (repackage หลัง Phase 12) · รอบ #6: F17/F18 ผ่าน
  · เจอ F19–F24 (flyout ซ้อน · ตำแหน่ง flyout · ลากในกริดเด้งมั่ว · อยากไฮไลท์ช่องกริด · ธีม · popup ตั้งค่า)
  · เคาะเริ่มไฮไลท์แนวทาง A ของ Qt · ยังไม่ลงมือ (Phase 14 ร่าง)
- 2026-10-10 — **Phase 14 เสร็จ** (F19–F24) · 14a flyout single-instance + จัดตำแหน่ง · 14b แก้ drop + ไฮไลท์ช่อง
  (ทำ custom เพราะ Qt IconMode ไม่มี drop indicator — FIXME ในซอร์ส Qt) · 14c ธีม (auto/light/dark) + หน้าต่างตั้งค่า
  · 14d repackage (AppImage 61M · .deb 51M) · เทสต์ **157 ผ่าน** · F19–F24 ปิดครบ
- 2026-10-10 — รับฟีดแบ็ก **รอบ #8**: B1 (ไอค่อนที่ลากในกริดหาย) + 2.x/3.x (UI แก้ไขกลุ่ม) + 4.x (i18n)
  · เบรนสตอร์มสเปก วางเป็น **Phase 15a–e** (รวมทำเป็นชุด + repackage ครั้งเดียวท้ายสุด)
- 2026-10-10 — **Phase 15 เสร็จ** (B1 · 2.x · 3.x · 4.x) · B1 รากจาก Qt `clearOrRemove` (แก้ `clearSelection`) ·
  GroupEditor UI ใหม่ (พรีวิว/ปุ่มเลือกระบบ/สไลด์เดอร์คุมกริด) · "แถว" รวมหัวฟอร์ม ·
  i18n (TH/EN + `config/lang/*.json` + สลับ/ส่งออก/นำเข้า) · เทสต์ **180 ผ่าน** · 15e = repackage รอ rebuild
- 2026-10-11 — **P16 (U1–U5/N1) + P19 Rebrand + P17a/b/d/e/f + B2/B3 fix เสร็จ & build แล้ว** ·
  reboot ยืนยันผ่าน (B2/B3/hotkey/ตา toggle) · เทสต์ 213 ผ่าน
- 2026-10-11 — รับฟีดแบ็ก **รอบ #10**: ยืนยันหลัง reboot ✅ · สั่งงาน About TH (นู๊บ/น้องพริก) · E1 alignment ชื่อกลุ่ม ·
  ไอเดียปุ่มโดเนท (A2) + อีโมจิปุ่ม (E2) · **มติ: ตัด open-all** · พักคลิกขวา flyout · ตัดดับเบิลคลิกว่าง ·
  **Phase 18 = งานหิน ทำหลังสุด** (ปิด UI + bug ก่อน)
- 2026-10-11 — รับฟีดแบ็ก **รอบ #11** (จากคำถาม): ย้าย "ที่เก็บ config" เข้าหน้าตั้งค่า + คลิกเปิดโฟลเดอร์ ·
  ช่องเลือกภาษาควรอัปเดตข้อความ/ทั้งแอป **ทันที** ไม่ต้องปิดเปิดใหม่ · **ทำเสร็จ** (218 เทสต์) · รอ repackage
- 2026-10-11 — **รอบ #12:** แก้ tagline About ให้ตรงจริง (ตัด "เปิดทั้งกลุ่มด้วยคลิกเดียว") → "รวบรวมทางลัด เรื่อง shortcut เราช่วยจัด" ·
  ตัด "(ทั้งแอป)" จากป้ายธีม · เก็บตกคำเก่าใน appdata/desktop/docstring · ไม่เพิ่มลิงก์แบรนด์ · 218 เทสต์ · build แล้ว
- 2026-10-11 — **รอบ #13:** เช็คก่อนเฟสใหม่ เจอบั๊กลบ/เปลี่ยนชื่อกลุ่มที่ปัก (launcher/หมุดค้าง) + ชื่อซ้ำทับกัน
  → แก้ครบ (cleanup launcher/ย้ายหมุด/เติมเลขชื่อซ้ำ) · 221 เทสต์ · build แล้ว
- 2026-10-11 — **รอบ #14:** pre-v1 hardening — ยืนยัน quit=exit 0, first-run/read-only ผ่าน, ปิดช่อง XML entity attack,
  เก็บกวาด constants · 223 เทสต์ · ที่เหลือ (Wayland/หลายจอ/DE อื่น) ยังเทสต์ไม่ได้ · build แล้ว
- 2026-10-11 — **Phase 18 (รอบ #15) เสร็จ:** Import/Export ทั้งชุด config (zip) ครบตามแผน ·
  `core/archive.py` (export/inspect/import · merge/replace · zip-slip guard · dry-run) ·
  ปุ่ม "ส่งออกทั้งหมด…"/"นำเข้าทั้งหมด…" ใน Settings (3 ปุ่ม merge/replace/ยกเลิก) · i18n TH/EN ·
  ทดสอบกับสำเนา config จริงผ่าน · **235 เทสต์** · build แล้ว
  → เฟสตามแผนเสร็จครบ เหลือเฝ้าฟีดแบ็กหลัง v1
- 2026-10-11 — ฟีดแบ็กผู้ใช้ **ท้าย Phase 18**: ลองจริงแล้ว — "ส่งออกทั้งหมด" → ลบกลุ่มทั้งหมด → "นำเข้าทั้งหมด" **ใช้งานได้** ✅
  · ผู้ใช้ผูกใจกับการทดสอบภาษาว่าทดสอบยากเพราะมีแค่ TH/EN → เสนอให้ทำภาษาเพิ่มแบบ **asset** (ให้ผู้ใช้รายอื่นไปลงกันเอง)
  → **รอบ #16:** ทำ asset ตัวอย่าง = ญี่ปุ่น `packaging/lang/ja.json` แปลเต็มชุด + วางที่ `dist/config/lang/ja.json`
  ให้ทดสอบทันที + `available_languages` โชว์ชื่อแสดงจาก `_lang_name` (dropdown = "日本語") · **238 เทสต์** · build แล้ว
