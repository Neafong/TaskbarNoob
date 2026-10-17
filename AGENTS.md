# Project Context — TaskbarNoob for Linux Mint

> "ความจำโปรเจกต์" — เปิดเซคชันใหม่ให้อ่านไฟล์นี้ก่อนเสมอ
> **ไฟล์นี้เก็บแค่ snapshot ปัจจุบัน** ให้สั้น — ประวัติอยู่ใน `docs/WORKLOG.md` · แผนที่เอกสาร: `docs/README.md`
> Last updated: 2026-10-17

## บทบาท / ผู้ช่วย
- ผู้ช่วยชื่อ **"น้องพริก"** — โปรแกรมเมอร์คู่ใจ เป็น **ผู้หญิง** → ลงท้าย **"ค่ะ / คะ"**
- โทน: เป็นกันเอง ขี้เล่นได้ แต่โฟกัสงาน

## กติกาทำงาน (กลั่นจาก karpathy-skills)
- **Think:** อย่าเดาเงียบๆ — เขียน assumption ก่อนลงมือ · มีหลายทางให้เสนอเทรดออฟ · งงให้หยุดถามค่ะ
- **Simple:** โค้ดน้อยสุดที่แก้ได้ · ไม่เพิ่ม feature/abstraction/config เผื่ออนาคต · ถ้า 200 บรรทัดลดเหลือ 50 ได้ ให้เขียนใหม่ค่ะ
- **Surgical:** แตะเฉพาะที่สั่ง · ไม่จัด format/refactor/ลบของข้างๆ ที่ไม่เกี่ยว (เจอให้แค่บอก) · เก็บขยะเฉพาะที่เราสร้างเอง · ทุก diff ต้องโยงถึง request ได้ค่ะ
- **Verify:** นิยาม done ก่อนทำ (เทสต์ไหนต้องผ่าน) · งานหลายขั้นให้แตก `1. step → verify` · รัน `.venv/bin/python tests/run.py` จนเขียว (307 เทสต์) ก่อนจบค่ะ
- **Tradeoff:** งานจิ๋ว (typo, one-liner ชัดๆ) ใช้วิจารณญาณ ไม่ต้องครบพิธีค่ะ

## วิธีรันงานยาว (สั่งครั้งเดียวจบ)
- วิธีเต็ม: `~/NoobWiki/guides/autonomous-th.md` (Win: `<vault>/guides/autonomous-th.md`) · ป้าย checkpoint: `~/NoobWiki/templates/task-state.md`
- วง: ซอยงานมี verify → ทำทีละขั้น แปะป้ายท้าย `docs/WORKLOG.md` + commit ทุกขั้น → จบด้วย DONE/STUCK/LIMIT พร้อมโน้ตค่ะ
- เปิดเซคชันใหม่แค่บอก "ต่อจากป้าย" · ลิมิตหมดส่งตามเชน `~/NoobWiki/team.md`ค่ะ
- **ถ้าเปิดไฟล์กลางไม่เจอ (ยังไม่ได้ clone):** หยุดแล้วเตือนพี่ให้ clone ก่อน `git clone git@github.com:Neafong/NoobWiki.git` (repo private ต้องใช้ SSH) · อย่าเดาเนื้อหาเองค่ะ

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
- **เป้าหลัก:** Linux Mint (Cinnamon) · **เป้ารอง:** Windows (alpha) · **macOS:** มีโค้ดแต่ยังไม่ทดสอบ
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
- **โค้ดล่าสุด:** **v0.2.0** = "กระเป๋าใส่ได้ทุกอย่าง" + UI polish + พอร์ตข้าม OS (alpha) (2026-10-17)
  · dispatch ข้าม OS (`launchers.py`/`taskbar.py` ชื่อเดิม) · `.lnk` ผ่าน PowerShell · `.command` + Dock pin
  · hotkey Windows (`RegisterHotKey` จำใน settings) · ไอคอน `.exe/.lnk/.app` ผ่าน Qt provider
  · **307 เทสต์** (mock ล้วน — ยังไม่ได้รันบน Windows จริง) · ไม่ทำ installer (portable ล้วน)
- **แพลตฟอร์ม:** Linux Mint (Cinnamon) = หลัก/ทดสอบแล้ว · **Windows = alpha** (กำลังทดสอบเครื่องจริง)
  · **macOS = มีโค้ด (`core/macos.py`) แต่ยังไม่ทดสอบ** — ไม่เปิด build · ประกาศชัดใน README/CHANGELOG (ทีมไม่มีเครื่อง Mac)
- **git:** tag `v0.2.0` ย้ายมาที่ HEAD (จาก commit เก่า `e245283` ตอนยังเป็น draft) · **ยังไม่ publish Release**
  · เหลือ: rebuild deb + AppImage → แนบใน draft Release → เทสต์ Windows → **publish**
  · ลบ AppImage เก่า 0.1.0 ที่ `/mnt/Backup/TaskbarGroups/dist/` **ยังไม่ได้** (MFT พัง — พักไว้ ดู `docs/WORKLOG.md` ท้าย)
- **แผนต่อจากนี้:** เทสต์ Windows จริง แล้ว publish v0.2.0 · ดู `docs/roadmap.md` + `docs/feedback.md`
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
- **flyout ตำแหน่ง "ตามเมาส์" อย่าแก้ด้วยการจับเร็วขึ้น:** คอขวดคือ AppImage cold start (~0.38 วิ) + โหลด Qt (~0.15 วิ)
  → อ่าน `QCursor.pos()` ตอน show สายไปแล้ว · **แก้ที่ราก: ตรึงตำแหน่ง** — โหมดปกติ `panel_anchor_position()`
  วางชิดขอบ panel (หา panel จากช่องว่าง `geometry` vs `availableGeometry`) + X ตามที่จับได้ · โหมดโฟกัส (hotkey) `--center` → `focus_position()` กลางจอ + ไอคอนใหญ่ตาม `Group.focus_scale` (**1.0–3.0** ค่าเริ่มต้น 2.0 · ตั้งใน `HotkeyDialog` slider) + `FOCUS_MIN_ICON`
  · `_run_flyout` จับ `QCursor.pos()` **ก่อน** `try_delegate` แล้วส่งผ่าน protocol JSON `{group,x,y,center}` (รับข้อความเปล่าแบบเก่าได้ด้วย)
- **ชื่อใต้ไอคอน = ต่อกลุ่ม + ค่าเริ่มต้นจากแอป:** `Group.show_labels` เป็น `bool | None` (**None = สืบทอด**)
  · ค่าระดับแอป `settings.json` key `flyout_labels` = ค่าเริ่มต้น (default ปิด) · flyout resolve `group.show_labels if not None else app_default`
  · checkbox ในแถบไอคอนกลุ่มของ `GroupEditor` (โชว์ค่าที่มีผลจริง, บันทึกเป็น bool ชัดเจน) · ปิด=ปุ่มจัตุรัส · เปิด=กว้างตาม `QFontMetrics` (`LABEL_MAX_WIDTH=168`)
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
- เทสต์: `.venv/bin/python tests/run.py` → **307 ผ่าน**
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
        data-model.md · upstream.md · phase18-plan.md · team.md (ทีมโมเดล/แบ่งสายงาน) · screenshots/
config/ (gitignored) — ข้อมูลกลุ่มจริงแบบ portable
```

## อนูเบ-ต่อไป (Next Actions)
1. **v0.2.0 ครบแล้ว — เหลือ publish:** tag `v0.2.0` = HEAD · เหลือ rebuild deb + AppImage → แนบใน draft Release
   → **เทสต์ Windows จริง** → publish · เริ่มเซคชันใหม่แล้วอ่าน snapshot นี้ + `docs/README.md` + ไฟล์แผนก่อนลงมือ
2. **จัดระเบียบเอกสาร (ระบบการเขียนแผน):** ✅ เฟส A–E + G เสร็จ (`docs/README.md` · `roadmap.md` · `release-process.md` · `CHANGELOG.md` · `.github/**` · `CONTRIBUTING.md`) — เหลือ **F `docs/windows-plan.md`** (เลื่อนไว้ทำตอนเริ่ม Windows จริง)
3. **Windows port** — alpha เสร็จ (โค้ดพร้อม · hotkey/pin/launcher/ไอคอน) · เหลือ **เทสต์บนเครื่องจริง** (เช็กลิสต์ใน `docs/windows-plan.md`)
4. เริ่มงานชุดใหญ่ใน **เซคชั่นใหม่** เสมอ (ประหยัด token) — อ่าน AGENTS.md + `docs/README.md` + ไฟล์แผนก่อนลงมือ
5. อย่าลืม: อัปเดต `docs/WORKLOG.md` เมื่อจบงาน + `docs/feedback.md` เมื่อปิดฟีดแบ็ก

## เอกสารอ้างอิง
- `docs/README.md` — แผนที่/ดัชนีเอกสาร + ลำดับเฟสจัดเอกสาร
- `docs/roadmap.md` — แผนภาพรวมทุกเฟส + งานถัดไป + แผน Windows
- `docs/WORKLOG.md` — ประวัติงานต่อเฟส (อ่านเมื่ออยากรู้ย้อนหลัง)
- `docs/feedback.md` — ฟีดแบ็กผู้ใช้ + งานค้าง
- `docs/data-model.md` — สกีมา + ฟอร์แมตเก็บกลุ่ม
- `docs/team.md` — รายชื่อทีมโมเดล + แบ่งสายงาน
- `docs/upstream.md` — ผลวิจัยต้นฉบับ Windows + ฟีเจอร์ค้างใน PR