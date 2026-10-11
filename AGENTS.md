# Project Context — TaskbarGroups for Linux Mint

> "ความจำโปรเจกต์" — เปิดเซคชันใหม่ให้อ่านไฟล์นี้ก่อนเสมอ
> **ไฟล์นี้เก็บแค่ snapshot ปัจจุบัน** ให้สั้น — ประวัติงานอยู่ใน `docs/WORKLOG.md`
> Last updated: 2026-10-11

## บทบาท / ผู้ช่วย
- ผู้ช่วยชื่อ **"น้องพริก"** — โปรแกรมเมอร์คู่ใจ เป็น **ผู้หญิง** → ลงท้าย **"ค่ะ / คะ"**
- โทน: เป็นกันเอง ขี้เล่นได้ แต่โฟกัสงาน

## แบรนด์ (Noob) — ที่มาของชื่อแอป
- **ชื่อแอป: "TaskbarNoob"** (ชื่อที่แสดง) · คง `APP_ID = taskbargroups` ไว้ก่อน (พิน/config ไม่พัง)
- **ความหมาย "Noob" ของผู้ใช้ (ไม่ใช่เชิงลบ):** มือใหม่ = **น้ำไม่เต็มแก้ว** ถ่อมตน ไร้อีโก้ เรียนรู้/Level Up
  ได้ตลอด · ตั้งใจแจกฟรีและเป็น **เกราะกันดราม่า** ถ้ามีบั๊ก · ได้แรงบันดาลใจจาก **เดกุ (My Hero Academia)**
  = "ไอ้กากที่พยายามจนเป็นฮีโร่ที่สุด"
- แบรนด์ส่วนตัว: https://neafong.wixsite.com/noob-photo · https://www.flickr.com/photos/neafong/
  · จะมีช่อง YouTube **"NoobGreaner"**

## เป้าหมายโปรเจกต์
แอปคล้าย [Taskbar Groups](https://github.com/tjackenpacken/taskbar-groups):
จัดกลุ่ม shortcut แล้วกดครั้งเดียวเปิดกลุ่มนั้นได้
- **เป้าหลัก:** Linux Mint (Cinnamon) · **เป้ารอง:** Windows (เฟสหลังๆ)
- **Portable:** config อยู่ในโฟลเดอร์แอป (`<app>/config/`)

## Stack ที่ล็อกแล้ว
- **GUI:** Qt/PySide6 (ข้าม OS Win/Linux) — ติดตั้งใน `.venv`
- **Data:** JSON ต่อกลุ่ม (`group.json`, มี `schema_version`)
- **สถาปัตยกรรม:** แยก `core/` (Python ล้วน ข้าม OS) ออกจาก `gui/` (Qt)
- **config:** portable ใต้ `<app>/config/`, override ด้วย env `TASKBARGROUPS_CONFIG`
- **hotkey:** gsettings ของ **Cinnamon** เท่านั้น

## สถานะปัจจุบัน
- **ขั้น: Phase 18 (import/export config zip) ✅ build แล้ว (2026-10-11 · 240 เทสต์) — เฟสตามแผนเสร็จครบ**
  · ปุ่ม "ส่งออกทั้งหมด…"/"นำเข้าทั้งหมด…" ใน Settings · `core/archive.py` · i18n TH/EN + asset ตัวอย่าง `packaging/lang/ja.json`
  · **พร้อมขึ้น GitHub (2026-10-12):** `README.md` (TH+EN) · `LICENSE` = **GPL-3.0** · โลโก้ย้าย `packaging/assets/` · ยังไม่มี commit
  → **รอบ #16 = ผู้ใช้ยืนยัน export/import ทั้งชุดใช้ได้ + เพิ่มภาษาตัวอย่าง (ญี่ปุ่น) ให้ทดสอบ i18n → 238 เทสต์ · build แล้ว**
  → **รอบ #17 (✅ build แล้ว · 240 เทสต์):** ผู้ใช้เจอ `config.bak-*` ค้างจาก replace import →
    เพิ่มปุ่ม **"ลบสำรองเก่า…"** ใน Settings (`archive.list_backups`/`delete_backups` · ยืนยัน+รายละเอียด) · ja.json อัปเดตครบ
  → **Phase 16e + P19 Rebrand ✅ build แล้ว (2026-10-11 04:02–04:03 · 186 เทสต์)**
  · U4 เฟือง 28px · U5 ตั้ง window/app icon (เลิกเฟือง fallback) · ชื่อที่แสดง = **"TaskbarNoob"** (ไอค่อนวงกลมฟ้า TG)
  · AppImage `TaskbarNoob-x86_64.AppImage` (61M) + `.deb` (51M)
  → **P17a/b/d/f ✅ (213 เทสต์) · fix ไอค่อน panel หายหลัง reboot ✅ · fix hotkey (schema + GVariant) ✅ · P17e build แล้ว (2026-10-11 12:47 · 213 เทสต์)**
  · **ยืนยันหลัง reboot ✅ ผ่าน**: B2 (ไอค่อน panel) · B3 (hotkey `Ctrl+Shift+G`, กดซ้ำไม่ซ้อน) · ตา toggle ตรง panel · แก้ไอค่อน/ชื่อกลุ่มที่ปักแล้ว reboot = refresh เอง
  → **รอบ #10 (✅ build แล้ว 2026-10-11 18:26 · 215 เทสต์):** A1 About TH `credits_note` = **"นู๊บ"/"น้องพริก"** (บรรทัด `credits` คงเดิม) ✅ · E1 alignment ชื่อกลุ่ม ✅ · E2 ปุ่มเพิ่ม/แก้ไข/ลบ = **ไอคอนธีมระบบ** (fallback อีโมจิ) ✅ · A2 ปุ่มโดเนท **"สนับสนุน ☕"** ใน About → **Ko-fi `ko-fi.com/neafong`** (`Settings.get_donate_url` default) ✅ · **ตัด open-all** (คง field `allow_open_all` ไว้ import compat) ✅
  → **รอบ #11 (✅ build แล้ว 2026-10-11 19:22 · 218 เทสต์):** ย้าย "ที่เก็บ config" จากหน้าหลัก → Settings เป็นปุ่มคลิกเปิดโฟลเดอร์ (file manager) ✅ · **สลับภาษาทันที** ไม่ต้องปิดเปิดแอป (`i18n.setup` + `MainWindow.retranslate()` + `SettingsDialog._retranslate()`, ลบ restart note) ✅ · i18n ใหม่ `settings.config_dir`/`settings.open_config_dir`, ลบ `main.config_dir`/`settings.lang_restart_note` · AppImage **51M** + `.deb` **43M**
  → **รอบ #12 (✅ build แล้ว · 218 เทสต์):** tagline About ใหม่ **"รวบรวมทางลัด เรื่อง shortcut เราช่วยจัด"** (EN "Gather your shortcuts, we do the rest") · ตัด "(ทั้งแอป)" จาก `settings.theme` → "ธีม"/"Theme" · เก็บตกคำเก่าใน `appdata.xml`/`.desktop`/docstring/CLI · ไม่เพิ่มลิงก์แบรนด์ (เก็บแค่ Ko-fi)
  → **รอบ #13 (✅ build แล้ว · 221 เทสต์):** เก็บบั๊ก cleanup ก่อนเฟสใหม่ — ลบกลุ่มที่ปัก = unpin + ลบ `.desktop`/ไอคอน (`_cleanup_launcher`) ✅ · เปลี่ยนชื่อกลุ่มที่ปัก = ย้ายหมุดตามชื่อใหม่ (`_install_and_pin`) ✅ · ชื่อซ้ำ = เติม ` 2`/` 3` อัตโนมัติ + เด้งกล่องบอก (`_unique_group_name`) ✅
  → **รอบ #14 (✅ build แล้ว · 223 เทสต์):** pre-v1 hardening — ยืนยัน quit exit 0 ✅ · first-run/read-only ผ่าน ✅ · XML import ปฏิเสธ `DOCTYPE/ENTITY` (กัน entity attack) ✅ · ลบ constants ซ้ำ `paths.py` ✅
    · **ยังเทสต์บนเครื่องนี้ไม่ได้:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น (hotkey/pin = Cinnamon-only)
  → **Phase 18 / รอบ #15 (✅ build แล้ว 2026-10-11 · 235 เทสต์):** Import/Export ทั้งชุด config (zip) ครบตามแผน —
    `core/archive.py` (export/inspect/import · merge/replace · zip-slip guard · dry-run) ✅ ·
    `ConfigStore.unique_group_name` ใช้ร่วม importer/GUI ✅ · ปุ่ม **"ส่งออกทั้งหมด…"/"นำเข้าทั้งหมด…"**
    ใน Settings (import = 3 ปุ่ม merge/replace/ยกเลิก + replace ถามซ้ำ) ✅ · i18n TH/EN ✅ ·
    ทดสอบกับสำเนา `dist/config` จริง (export→replace/merge) ผ่าน ✅ · **เฟสตามแผนเสร็จครบ**
  → **รอบ #16 (✅ build แล้ว · 238 เทสต์):** ฟีดแบ็กผู้ใช้ — ส่งออกทั้งหมด→ลบกลุ่มหมด→นำเข้าทั้งหมด **ใช้ได้** ✅
    · ทำภาษา**ตัวอย่างแบบ asset** = ญี่ปุ่น `packaging/lang/ja.json` (แปลครบทุกคีย์ + `_lang_name` = "日本語")
    ให้ผู้ใช้รายอื่นโหลดไป import เอง · วางสำเนาที่ `dist/config/lang/ja.json` เทสต์ dropdown 3 ภาษาได้ทันที ·
    `available_languages()` อ่านชื่อแสดงจาก `_lang_name` (fallback = code) · import ภาษาโชว์ชื่อถูกต้อง ✅
  → **Phase 18 (import/export zip) = เสร็จแล้ว**
- **มี `docs/feedback.md`** — ฟีดแบ็ก F1–F24 + รอบ #8–#10 (B1 · 2.x–4.x ปิดครบ · #10 = reboot ผ่าน + สเปก UI ใหม่ + มติตัด open-all/พักคลิกขวา flyout) + สถานะ + ไอเดียเสนอเพิ่มเติม
- หมายเหตุ **B2 (ไอค่อน panel หายหลัง reboot):** launcher เดิมตั้ง `Icon=<path สัมบูรณ์>` ชี้ไฟล์บนไดรฟ์ (`/mnt/Backup` NTFS USB `nofail`)
  ที่ mount **หลัง** panel เริ่มทำงาน → ตอน boot หาไอคอนไม่เจอ · **แก้: ติดตั้งไอคอนเข้า hicolor icon theme แล้วตั้ง `Icon=<launcher_id>`**
  (`install_launcher_icon`/`launcher_id` ใน `core/desktop.py`) · มี self-heal `MainWindow._sync_pinned_launchers()` ตอนเปิดแอป
  (แก้ launcher เก่าที่ชี้ path → reload applet)
- หมายเหตุ **hotkey schema (Cinnamon):** schema ที่ถูกคือ `org.cinnamon.desktop.keybindings.custom-keybinding` (**เอกพจน์**)
  · path = `/org/cinnamon/desktop/keybindings/custom-keybindings/<slot>/` · key `binding` เป็นชนิด **`as`** (array) ต้อง set `['<Control><Alt>g']`
  · key `name`/`command` เป็น `s` — ค่าที่มีช่องว่าง/เครื่องหมายคำพูด **ต้องห่อเป็น GVariant literal** `'...'` (ไม่งั้นขึ้น `expected end of input`)
  · `custom-list` เก็บเป็น **slot id** (ไม่ใช่ path) · **Cinnamon rebuild เฉพาะเมื่อ `custom-list` เปลี่ยน** (`changed::custom-list`)
  → ต้อง set name/command/binding **ก่อน** แล้ว "แตะ" list (dummy `__dummy__` แล้วตั้งค่าจริง) ไม่งั้นกดคีย์ไม่ทำงาน
  · **ถอนคีย์:** `remove_custom_keybindings()` ของ Cinnamon ลบเฉพาะชื่อที่มีคำว่า `custom` → slot เรา (`taskbargroups-*`) ไม่ถูกลบ
  → ต้อง `set binding = []` **ตอนที่ slot ยังอยู่ใน list** + แตะ list (ให้ Cinnamon เรียก `remove_keybinding`) ก่อนถอดออกจาก list
  · ตรวจ live ได้ด้วย `gdbus call … org.Cinnamon.Eval "JSON.stringify([...imports.ui.main.keybindingManager.bindings.values()].map(b=>b.name))"`
- หมายเหตุ F1/F3: ปักหมุดลง panel จริงได้แล้วผ่าน Grouped Window List applet config + `ReloadXlet`
  · ต้องมี `Path=` ใน .desktop (แก้แล้ว) ไม่งั้นคลิกแล้วเปิดไม่ขึ้น
- หมายเหตุ F16/F17: ดึงไอคอนจริงจาก `.AppImage` ได้แล้ว (แตก squashfs ผ่าน `--appimage-extract` → `.DirIcon`/`Icon=`)
- หมายเหตุ F22: ไฮไลท์ช่องกริดทำ **custom** (Qt IconMode ไม่มี drop indicator — มี FIXME ในซอร์ส Qt)
- หมายเหตุ F19: อย่าตั้ง `self.window=None` ใน `_on_closed` ระหว่าง closeEvent (GC ทำลาย popup กลางเหตุการณ์ →
  heap corruption) — ต้อง `deleteLater()`
- หมายเหตุ **B1**: ไอค่อนที่ลากในกริดหาย = Qt `clearOrRemove()` หลัง `MoveAction` (dropEventMoved=false เพราะ
  override dropEvent เอง) ลบแถวที่ถูกเลือก → **แก้: `self.clearSelection()` ใน `dropEvent`** · เทสต์ guard selection ว่าง
- **i18n:** `core/i18n.py` dict TH/EN built-in + overlay `config/lang/<code>.json` · `settings.json` key `language`
  · สลับภาษาที่ Settings (ผลใช้ตอนเปิดแอปถัดไป) · ส่งออก/นำเข้าภาษา JSON
- หมายเหตุ F23/F24: `core/settings.py` + `gui/theme.py` + `gui/settings_dialog.py` + `core/i18n.py` = ใหม่จาก Phase 14/15
- `dist/` = build ล่าสุด (รอบ #14: pre-v1 hardening, ล่าสุด) ·
  AppImage **51M** · .deb **43M** (slim แล้วด้วย `packaging/slim_bundle.sh`) · `dist/config` (กลุ่มจริง) intact
- git repo ยังไม่มี commit แรก (ผู้ใช้ยังไม่สั่ง commit)

## แผนงานแบบเฟส
`[x]` เสร็จ · `[ ]` รอทำ
- `[x]` P0 Brainstorm/สเปก · `[x]` P1 data model + โครงไฟล์
- `[x]` P2 MVP (จัดการกลุ่ม + grid + เปิดแอป)
- `[x]` P3 panel (`.desktop` launcher + hotkey)
- `[x]` P4 เก็บงาน: cache ไอคอน, ธีม/opacity/open-all, importer จาก Windows
- `[x]` P5 Packaging: AppImage + `.deb` (PyInstaller → appimagetool / dpkg-deb)
- `[x]` P6 Settings & Flyout polish (slider opacity/ขนาดไอคอน · flyout โปร่งแสง · dblclick แก้ไข · จัดปุ่ม + เฟือง Setup · ปุ่มปักหมุด)
- `[x]` P7 Shortcut editor เป็น Grid + drag & drop + reorder
- `[x]` P8 UI polish รอบ 2 (Pin ต่อแถว · สลับลำดับกลุ่ม · ไอคอน grid ใหญ่+ดึงจริง · รวมสี · พิมพ์ตัวเลขได้)
- `[x]` P9 Cinnamon panel: ปักหมุดจริง (Grouped Window List) + คลิกเปิด flyout
- `[x]` P10 Pin toggle (ปัก/ถอน) + โชว์สถานะปักบนแถวกลุ่ม
- `[x]` P11 Repackage: rebuild AppImage + `.deb` (Phase 8/9/10)
- `[x]` P12 Fix F16–F18: extract ไอคอนใน AppImage + ลากสลับลำดับกลุ่มบันทึกจริง + ไอคอนไม่เล็ก
- `[x]` P13 Repackage: rebuild AppImage + `.deb` (รวม Phase 12)
- `[x]` P14a Flyout UX: single-instance ข้าม process + ตำแหน่งกึ่งกลางเมาส์ + ปิดเมื่อคลิกที่อื่น (F19/F20)
- `[x]` P14b Grid drag UX: แก้ตำแหน่งปล่อย + ไฮไลท์ช่องเป้าหมาย (custom — Qt IconMode ไม่เวิร์ก) (F21/F22)
- `[x]` P14c Theme (light/dark/auto) + Settings dialog จากปุ่มเฟือง (F23/F24)
- `[x]` P14d Repackage: rebuild AppImage + `.deb` (Phase 14) แล้วให้ผู้ใช้ทดสอบ
- `[x]` P15a Fix B1: ลากในกริดไอค่อนหาย (Qt `clearOrRemove` — แก้ `clearSelection`) + เทสต์
- `[x]` P15b GroupEditor UI: ลบ labels เดิม · พรีวิวแถวเดียวกับปุ่ม · ปุ่มเลือกไอค่อนระบบ · สไลด์เดอร์คุมกริด
- `[x]` P15c Width compact: label "แถว" + ย้ายแถวเดียวกับชื่อกลุ่ม
- `[x]` P15d i18n: ไทย/Eng + `config/lang` JSON + สลับ/ส่งออก/นำเข้าภาษา
- `[x]` P15e Repackage: rebuild AppImage + `.deb` แล้วให้ผู้ใช้ทดสอบ
- `[x]` P16a Auto-refresh ไอค่อน Taskbar หลังแก้กลุ่ม (N1): `_refresh_pinned_icon` + 182 เทสต์
- `[x]` P16b ✅ U3 = **ตาเปิด/ปิด** · P16c ✅ U1 เฟืองใหญ่ + U2 สีธีม-aware + tooltip แสดง/ซ่อน (184 เทสต์)
- `[x]` P16d Repackage (รวม 16a–16c): AppImage (61M) + `.deb` (51M) 01:57 · boot/PYZ ตรวจแล้ว
- `[x]` P16e ✅ U4 เฟือง 28px + U5 ตั้ง app/window icon (186 เทสต์)
- `[x]` P19 Rebrand ✅: ชื่อแสดง = **"TaskbarNoob"** (คง APP_ID `taskbargroups` — พิน/config ไม่พัง)
  · ไอค่อนใหม่จาก `packaging/assets/Logo TG.svg` (`render_icon.py` rasterize → png) · รวม build กับ 16e (04:02–04:03)
- `[x]` P17a Context menu กลุ่ม (คลิกขวา: เปิด/แก้ไข/ปัก-ถอน/hotkey/ทำสำเนา/ลบ) · `[x]` P17d Duplicate (`ConfigStore.duplicate_group`)
- `[x]` P17b hotkey ข้างชื่อ (อ่าน gsettings custom-list + binding → `cinnamon_to_display`) + **ถอนคีย์ลัด** (ปุ่มใน dialog · ลบกลุ่ม = ลบคีย์) · `[x]` P17f Credits "Noob & Pickle" (Settings + About dialog + appdata)
  · เอาปุ่มซ้ำ "ติดตั้ง launcher"/"ตั้ง hotkey" ออกจากเฟือง ⚙ (ใช้คลิกขวาต่อกลุ่มแทน — กันสับสนว่าตั้งให้กลุ่มบนสุด)
- `[x]` P17e Repackage ✅ (2026-10-11 12:47): AppImage (61M) + `.deb` (51M) · PYZ ตรวจ symbol ใหม่ครบ (รวม hotkey fix) · `dist/config` intact
  · ~~P17c ค้นหา/กรอง~~ ตัดออก (ผู้ใช้ตัดสิน 2026-10-11)
- `[x]` P18 Import/Export ทั้งชุด config (zip/zip) + repackage สุดท้าย ✅ รอบ #15

## วิธีรัน / Dev
- รันแอป: `.venv/bin/python -m taskbargroups`
- เปิด flyout: `... -m taskbargroups --open "<GroupDir>"` · list: `... --list`
- นำเข้ากลุ่มจาก Windows: `... -m taskbargroups --import "<โฟลเดอร์ที่มี ObjectData.xml>"`
- เทสต์: `.venv/bin/python tests/run.py` → **240 ผ่าน**
  · (ถ้ารัน `python -m unittest discover -s tests` ผลเทสต์เท่ากัน แต่ตอนปิดโปรเซส PySide6 6.12
    จะ segfault ใน `destroyQCoreApplication()` — บั๊กฝั่ง Qt · `tests/run.py` เรียก `os._exit()` เลี่ยงให้)
- แพ็ก: `bash packaging/build_appimage.sh` → `dist/TaskbarNoob-x86_64.AppImage`
- แพ็ก `.deb`: `bash packaging/build_deb.sh` → `dist/taskbargroups_<ver>_amd64.deb`
- หมายเหตุ: เครื่องไม่มี pip/python3-venv → venv ทำด้วย `--without-pip` + get-pip.py
- หมายเหตุ: repo อยู่บน fuseblk (chmod ไม่ติด) — สคริปต์ `.deb` สเตจใน `/tmp` ให้แล้ว
- หมายเหตุ: เครื่องไม่มี `libxcb-cursor0` → รันจากซอร์สต้องมี `lib/libxcb-cursor.so.0` (gitignored)
  แล้ว `__main__` จะ re-exec ตั้ง `LD_LIBRARY_PATH` ให้เอง · แพ็กเกจจัดการเองอยู่แล้ว

## โครงไฟล์
```
README.md                          (ไทย + อังกฤษ · หน้าแรก repo)
taskbargroups/
├── __main__.py                     (GUI + CLI --open/--list/--import)
├── core/  models.py · storage.py · paths.py · launcher.py · desktop.py · hotkeys.py · panel.py
│          settings.py (config/settings.json · ธีม auto/light/dark · ภาษา) · i18n.py (TH/EN + config/lang overlay)
│          icons.py (resolve/cache ไอคอน รวม .AppImage) · importer.py (ObjectData.xml → group.json)
│          archive.py (export/inspect/import config zip · merge/replace · zip-slip guard)
└── gui/   main_window.py · group_editor.py (ShortcutGrid + _SystemIconDialog) · flyout.py (FlyoutController single-instance)
           theme.py · settings_dialog.py · icons.py · hotkey_dialog.py · about_dialog.py
packaging/  entrypoint.py · make_icon.py · render_icon.py (SVG→PNG) · build_appimage.sh · build_deb.sh · slim_bundle.sh
            lang/ (assets ภาษาให้ผู้ใช้ import เอง — ตัวอย่าง: ja.json ญี่ปุ่น)
            assets/ (`Logo TG.svg` ซอร์สไอค่อน + `Logo TG.vectorcraft`)
            appimage/ AppRun · taskbargroups.desktop · taskbargroups.png · taskbargroups.svg · .appdata.xml
tests/  test_models · test_storage · test_launcher · test_gui_smoke · test_desktop · test_hotkeys · test_icons
        test_importer · test_paths · test_flyout · test_grid_drag · test_settings · test_group_editor · test_i18n
        test_archive
docs/   data-model.md · worklog → WORKLOG.md · upstream.md
config/ (gitignored) — ข้อมูลกลุ่มจริงแบบ portable
```

## ขั้นตอนถัดไป (Next Actions)
1. **รอบ #17 ✅ build แล้ว (240 เทสต์)** — ปุ่ม **"ลบสำรองเก่า…"** ใน Settings (`archive.list_backups`/`delete_backups`)
   · ผู้ใช้ยืนยัน export/import + สลับภาษา (asset ญี่ปุ่น) ใช้ได้
2. **เตรียมขึ้น GitHub (กำลังทำ):** ✅ `README.md` (TH+EN) · ✅ ย้ายโลโก้ → `packaging/assets/` · ✅ ลบ backup ค้าง ·
   ✅ `.gitignore` กัน `*.AppImage/*.deb/*.zip` · ✅ **LICENSE = GPL-3.0** (ผู้ใช้เคาะ: อยากให้ต่อยอด/ขายต้องเปิดโค้ด) +
   เติมหัวข้อ License ใน README แล้ว · ⏳ เหลือ **commit แรก + remote + GitHub Release (แนบ AppImage/.deb)**
   · ยังไม่มี commit แรก + ยังไม่มี remote · binary ให้แนบเป็น GitHub **Release** ไม่ commit เข้า repo
3. **เฟสตามแผนครบแล้ว** — งานต่อไป = เก็บฟีดแบ็กหลังผู้ใช้ลอง v1 / งานค้างที่ระบุใน `docs/feedback.md`
4. เริ่มงานชุดใหญ่ใน **เซคชั่นใหม่** เสมอ (ประหยัด token) — อ่าน AGENTS.md + ไฟล์แผนก่อนลงมือ
5. อย่าลืม: อัปเดต `docs/WORKLOG.md` เมื่อจบงาน + `docs/feedback.md` เมื่อปิดฟีดแบ็ก
6. i18n: asset ภาษาอยู่ที่ `packaging/lang/` · ถ้าแปลเพิ่ม ทำ JSON ใหม่ (คีย์ = `core/i18n.py` TH, มี `_lang_name`
   สำหรับชื่อแสดง) แล้ววาง/import ลง `config/lang/<code>.json` เพื่อทดสอบ

## เอกสารอ้างอิง
- `docs/WORKLOG.md` — ประวัติงานต่อเฟส (อ่านเมื่ออยากรู้ย้อนหลัง)
- `docs/feedback.md` — ฟีดแบ็กผู้ใช้ + แผนเฟสถัดไป/งานค้าง
- `docs/phase18-plan.md` — แผน Phase 18 (import/export zip) — อ่านก่อนเริ่มเฟสนี้
- `docs/data-model.md` — สกีมา + ฟอร์แมตเก็บกลุ่ม
- `docs/upstream.md` — ผลวิจัยต้นฉบับ Windows + ฟีเจอร์ค้างใน PR
