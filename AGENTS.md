# Project Context — TaskbarNoob for Linux Mint

> "ความจำโปรเจกต์" — เปิดเซคชันใหม่ให้อ่านไฟล์นี้ก่อนเสมอ
> **ไฟล์นี้เก็บแค่ snapshot ปัจจุบัน** ให้สั้น — ประวัติอยู่ใน `docs/WORKLOG.md` · แผนที่เอกสาร: `docs/README.md`
> Last updated: 2026-10-13

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
- **v0.1.0 ขึ้น GitHub แล้ว (2026-10-12):** repo `github.com/Neafong/TaskbarNoob` (Public) ·
  Release แนบ `TaskbarNoob-x86_64.AppImage` + `taskbargroups_0.1.0_amd64.deb` · GPL-3.0 · README มี badge + Screenshots
- **โค้ดล่าสุด:** **v0.2-A/B/C เสร็จ + commit แล้ว** (2026-10-13) — ตัด "นำเข้ากลุ่ม (Windows)" ทั้งชุด
  (ปุ่ม + CLI `--import` + `core/importer.py`) · "กระเป๋าใส่ได้ทุกอย่าง" (launcher type-aware + flyout คลิกขวาเปิดที่อยู่)
  · UI polish (accent token · ไอคอน SVG ของเรา tint ตามธีม · swatch สี + ช่อง hex · แก้เมนู/ลาก)
  · **223 เทสต์** · import/export zip (P18) ยังอยู่ · ภาษา TH/EN + asset ตัวอย่าง `packaging/lang/ja.json`
- **git:** history เดิมกู้คืนจาก HDD backup แล้ว (`.git`/`.github`/`.gitignore` ครบ) · `main` ต่อเนื่องจาก `origin/main`
  · ยัง**ไม่ push** (รอเทสต์ local + ทำ Windows ก่อน) · **ยังไม่ออก tag v0.2.0 / ยังไม่ repackage รอบใหม่**
- **แผนต่อจากนี้:** ดู `docs/roadmap.md` + `docs/feedback.md` (งานถัดไป = เก็บฟีดแบ็กผู้ใช้ · Windows port เป้าหลัง)
- **ยังเทสต์บนเครื่องนี้ไม่ได้:** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น (hotkey/pin = Cinnamon-only)

## หมายเหตุเทคนิคสำคัญ (แก้โค้ดตรงส่วนนี้ ต้องอ่านก่อน!)

- **B2 (ไอค่อน panel หายหลัง reboot):** อย่าตั้ง `Icon=<path สัมบูรณ์>` ชี้ไฟล์บนไดรฟ์ที่ mount หลัง panel start
  · **ต้อง: ติดตั้งไอคอนเข้าระบบ hicolor แล้วตั้ง `Icon=<launcher_id>`** (`install_launcher_icon`/`launcher_id` ใน `core/desktop.py`)
  · มี self-heal `MainWindow._sync_pinned_launchers()` ตอนเปิดแอป (แก้ launcher เก่าที่ชี้ path)
- **hotkey schema (Cinnamon):** schema = `org.cinnamon.desktop.keybindings.custom-keybinding` (**เอกพจน์**)
  · path = `/org/cinnamon/desktop/keybindings/custom-keybindings/<slot>/` · `binding` เป็น **`as`** (array) → `['<Control><Alt>g']`
  · `name`/`command` เป็น `s` — ค่าที่มีช่องว่าง/เครื่องหมายคำพูด **ต้องห่อ GVariant literal** `'...'` (ไม่งั้น `expected end of input`)
  · `custom-list` เก็บเป็น **slot id** (ไม่ใช่ path) · **Cinnamon rebuild เฉพาะเมื่อ `custom-list` เปลี่ยน**
  → ตั้ง name/command/binding **ก่อน** แล้ว "แตะ" list (dummy `__dummy__` → ค่าจริง) ไม่งั้นกดคีย์ไม่ทำงาน
  · **ถอนคีย์:** `remove_custom_keybindings()` เก็บเฉพาะชื่อมีคำว่า `custom` → slot เรา (`taskbargroups-*`) ต้อง
  `set binding = []` **ตอนยังอยู่ใน list** + แตะ list ก่อนถอด · ตรวจ live: `gdbus call … org.Cinnamon.Eval "JSON.stringify([...bindings.values()].map(b=>b.name))"`
- **F1/F3 (ปักหมุด panel):** Grouped Window List applet config + `ReloadXlet` · **ต้องมี `Path=` ใน .desktop** ไม่งั้นคลิกเปิดไม่ขึ้น
- **F16/F17 (ไอคอนจาก AppImage):** แตก squashfs ผ่าน `--appimage-extract` → `.DirIcon`/`Icon=`
- **F19:** อย่าตั้ง `self.window=None` ใน `_on_closed` ระหว่าง closeEvent (GC ทำลาย popup กลางเหตุการณ์ → heap corruption) — ต้อง `deleteLater()`
- **B1 (ลากในกริดไอค่อนหาย):** Qt `clearOrRemove()` หลัง MoveAction ลบแถวที่ถูกเลือก → **แก้: `self.clearSelection()` ใน `dropEvent`**
- **F22:** ไฮไลท์ช่องกริดทำ custom (Qt IconMode ไม่มี drop indicator — มี FIXME ในซอร์ส Qt)
- **i18n:** `core/i18n.py` dict TH/EN built-in + overlay `config/lang/<code>.json` · `settings.json` key `language`
  · asset ภาษา: `packaging/lang/` (ตัวอย่าง `ja.json`) · ชื่อแสดงอ่านจาก key `_lang_name` (fallback = code)
- **packaging:** เครื่องไม่มี pip/python3-venv (venv `--without-pip`) · repo อยู่บน fuseblk (chmod ไม่ติด → สคริปต์ `.deb` สเตจ `/tmp`)
  · ไม่มี `libxcb-cursor0` → รันจากซอร์สต้องมี `lib/libxcb-cursor.so.0` แล้ว `__main__` re-exec ตั้ง `LD_LIBRARY_PATH`

## ที่เก็บไฟล์ (เครื่องนี้) — ข้อตกลง 🚩

> ตั้งขึ้นเพราะเดิมไฟล์เกลื่อนหลายที่ พอความจำหายแล้วสร้างใหม่ เลยหาไม่เจอ — **รวมที่เดียว**

- **โปรเจกต์ (ทำงาน):** `/home/noob/Desktop/TaskbarNoob` (SSD) = source หลัก
- **AppImage ที่ใช้จริง/เทสต์ = ที่เดียว:** `/home/noob/AppImage/Tool/TaskbarNoob-x86_64.AppImage`
  → หลัง `bash packaging/build_appimage.sh` **คัดลอกไฟล์ไปทับที่นี่เสมอ** · **อย่าเทสต์จาก `dist/` ตรง ๆ**
- **config จริง (portable):** `/home/noob/AppImage/Tool/config/` (อยู่ข้าง AppImage) — groups: Game · Production · Tool
  · รันจากซอร์สให้ชี้มาที่นี่: `TASKBARGROUPS_CONFIG=$HOME/AppImage/Tool/config`
- **build output:** `<repo>/dist/` = ที่พักผลลัพธ์ชั่วคราว (gitignored) — ไม่ใช่ที่ใช้ประจำ
- **HDD เก่า:** `/mnt/Backup/TaskbarGroups/` = **สำรองเท่านั้น** (มี `.git` history + สำเนา config) · อย่ารันจากที่นี่
- **กติกา:** AppImage มีที่เดียว · กลุ่มจริงมีที่เดียว · ถ้าเจอไฟล์ซ้ำที่อื่น = ให้ถือที่ตามข้างบนนี้

## วิธีรัน / Dev
- รันแอป: `.venv/bin/python -m taskbargroups`
- เปิด flyout: `... -m taskbargroups --open "<GroupDir>"` · list: `... --list`
- เทสต์: `.venv/bin/python tests/run.py` → **223 ผ่าน**
  · (ถ้ารัน `python -m unittest discover -s tests` ผลเทสต์เท่ากันแต่ตอนปิด PySide6 6.12 จะ segfault
    ใน `destroyQCoreApplication()` — บั๊กฝั่ง Qt · `tests/run.py` เรียก `os._exit()` เลี่ยงให้)
- แพ็ก: `bash packaging/build_appimage.sh` → `dist/TaskbarNoob-x86_64.AppImage`
  · **แล้วคัดลอกไปทับ `~/AppImage/Tool/TaskbarNoob-x86_64.AppImage`** (ที่ใช้จริง — ดูหัวข้อ "ที่เก็บไฟล์")
- แพ็ก `.deb`: `bash packaging/build_deb.sh` → `dist/taskbargroups_<ver>_amd64.deb`

## โครงไฟล์
```
README.md                          (ไทย + อังกฤษ · หน้าแรก repo) · LICENSE (GPL-3.0) · CHANGELOG.md (Keep a Changelog)
.github/                            FUNDING.yml (Ko-fi) · ISSUE_TEMPLATE/ · PULL_REQUEST_TEMPLATE.md · workflows/tests.yml (CI)
taskbargroups/
├── __main__.py                     (GUI + CLI --open/--list)
├── core/  models.py · storage.py · paths.py · launcher.py · desktop.py · hotkeys.py · panel.py
│          settings.py (config/settings.json · ธีม · ภาษา) · i18n.py (TH/EN + config/lang overlay)
│          icons.py (resolve/cache ไอคอน รวม .AppImage)
│          archive.py (export/inspect/import config zip · merge/replace · zip-slip guard)
└── gui/   main_window.py · group_editor.py (ShortcutGrid + _SystemIconDialog) · flyout.py (FlyoutController single-instance)
           theme.py · settings_dialog.py · icons.py · hotkey_dialog.py · about_dialog.py
packaging/  entrypoint.py · make_icon.py · render_icon.py (SVG→PNG) · build_appimage.sh · build_deb.sh · slim_bundle.sh
            lang/ (assets ภาษาให้ผู้ใช้ import เอง — ตัวอย่าง: ja.json) · assets/ (Logo TG.svg + .vectorcraft)
            appimage/ AppRun · taskbargroups.desktop · taskbargroups.png · taskbargroups.svg · .appdata.xml
tests/  test_* (models · storage · launcher · gui_smoke · desktop · hotkeys · icons · paths
        flyout · grid_drag · settings · group_editor · i18n · archive)
docs/   README.md (แผนที่เอกสาร) · roadmap.md (แผนเฟส/งานถัดไป) · WORKLOG.md (ประวัติ) · feedback.md
        data-model.md · upstream.md · phase18-plan.md · screenshots/
config/ (gitignored) — ข้อมูลกลุ่มจริงแบบ portable
```

## อนูเบ-ต่อไป (Next Actions)
1. **เฟสตามแผนครบ → v0.1.0 ขึ้น GitHub แล้ว** — งานต่อไป = **ลงมือ v0.2** (คลังไอเดียพร้อมแล้ว: `docs/feedback.md` รอบ #18–#21 + `docs/roadmap.md` ข้อ 3–5)
   · แบ่งเป็นเฟสย่อยทีหลัง · เริ่มเซคชันใหม่แล้วอ่าน snapshot นี้ + `docs/README.md` + ไฟล์แผนก่อนลงมือ
2. **จัดระเบียบเอกสาร (ระบบการเขียนแผน):** ✅ เฟส A–E + G เสร็จ (`docs/README.md` · `roadmap.md` · `release-process.md` · `CHANGELOG.md` · `.github/**` · `CONTRIBUTING.md`) — เหลือ **F `docs/windows-plan.md`** (เลื่อนไว้ทำตอนเริ่ม Windows จริง)
3. **Windows port** = เป้าหลัง (W0–W5 · `docs/windows-plan.md`)
4. เริ่มงานชุดใหญ่ใน **เซคชั่นใหม่** เสมอ (ประหยัด token) — อ่าน AGENTS.md + `docs/README.md` + ไฟล์แผนก่อนลงมือ
5. อย่าลืม: อัปเดต `docs/WORKLOG.md` เมื่อจบงาน + `docs/feedback.md` เมื่อปิดฟีดแบ็ก

## เอกสารอ้างอิง
- `docs/README.md` — แผนที่/ดัชนีเอกสาร + ลำดับเฟสจัดเอกสาร
- `docs/roadmap.md` — แผนภาพรวมทุกเฟส + งานถัดไป + แผน Windows
- `docs/WORKLOG.md` — ประวัติงานต่อเฟส (อ่านเมื่ออยากรู้ย้อนหลัง)
- `docs/feedback.md` — ฟีดแบ็กผู้ใช้ + งานค้าง
- `docs/data-model.md` — สกีมา + ฟอร์แมตเก็บกลุ่ม
- `docs/upstream.md` — ผลวิจัยต้นฉบับ Windows + ฟีเจอร์ค้างใน PR