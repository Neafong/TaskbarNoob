# Project Context — TaskbarNoob for Linux Mint

> "ความจำโปรเจกต์" — เปิดเซคชันใหม่ให้อ่านไฟล์นี้ก่อนเสมอ
> **ไฟล์นี้เก็บแค่ snapshot ปัจจุบัน** ให้สั้น — ประวัติอยู่ใน `docs/WORKLOG.md` · แผนที่เอกสาร: `docs/README.md`
> Last updated: 2026-11-23

## บทบาท / ผู้ช่วย
- ผู้ช่วยชื่อ **"เจนนี่"** (Gemini — รับช่วงต่อจาก "น้องพริก" Big Pickle) — โปรแกรมเมอร์คู่ใจ เป็น **ผู้หญิง** → ลงท้าย **"ค่ะ / คะ"**
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
- **config:** portable ใต้ `<app>/config/`, override ด้วย env `TASKBARNOOB_CONFIG` (รองรับ `TASKBARGROUPS_CONFIG` เก่า)
- **hotkey:** gsettings ของ **Cinnamon** เท่านั้น

## สถานะปัจจุบัน
- **v0.1.0 ขึ้น GitHub แล้ว (2026-10-12):** repo `github.com/Neafong/TaskbarNoob` (Public) · GPL-3.0-or-later
- **v0.2.0 ปล่อยขึ้น GitHub แล้ว (2026-11-23):** ครบทั้ง Linux Mint + Windows 11 (portable `TaskbarNoob.exe`, AUMID แยกต่อกลุ่ม/แอป, `.lnk` ผ่าน COM `IShellLinkW`, multi-res `.ico`, Hotkey Win32 + foreground focus + ย้ายคีย์ตามตอนเปลี่ยนชื่อ, ไอคอน MSIX/WindowsApps อัตโนมัติ, ตัวเลือกไอคอนระบบ 2 แหล่ง, Flyout เงามุมโค้ง)
  · โฟลเดอร์ใช้งานจริงบน Win: `D:\Portable\Tool\TaskbarNoob`
- **งานปัจจุบัน (`v0.3.0` — Full Architecture Refactor บน Linux Mint — เสร็จครบ R0–R4!):**
  · ✅ **R0 เสร็จแล้ว (2026-11-23):** จัดระเบียบ `docs/` ลง `docs/archive/` + แก้บั๊ก `storage._prune_order()`
  · ✅ **R1 เสร็จแล้ว (2026-11-23):** แยก `core/platform/{base,linux,win32}` (แตก `win32.py` เป็น 6 โมดูลย่อย) + พับเก็บ `core/macos.py` + ลด `sys.platform` ใน `gui/`
  · ✅ **R2 เสร็จแล้ว (2026-11-23):** แตก `gui/group_editor.py` → `icon_picker`/`shortcut_grid`/`shortcut_dialog`/`group_editor` และ `gui/main_window.py` → `group_list`/`app`/`main_window`
  · ✅ **R3 เสร็จแล้ว (2026-11-23):** แตก `core/icons/` (`cache`/`theme`/`appimage`/`steam`) + เลิก circular import ใน `gui/icons.py` + ตัวเลือกไอคอนแยกหมวดบน Mint (`categories`/`apps`/`all`) + Steam `steam://rungameid/<appid>` icon resolver ข้าม OS
  · ✅ **R4 เสร็จแล้ว (2026-11-23):** ลบ dead code PowerShell + แยก `core/i18n/` + รีแบรนด์ภายใน `taskbargroups` → `taskbarnoob` พร้อม Auto-Migration (panel pins + Cinnamon hotkeys + env/XDG fallback + `.deb` Replaces/Conflicts) + เครดิต `Noob & Jenny` + bump `0.3.0` → **385 เทสต์ ผ่าน 100% บน Mint (skipped=10 Windows-only)**
  · **ถัดไป:** ทดสอบ build AppImage/deb จริงบน Linux Mint แล้วค่อยทดสอบฝั่ง Windows 11 + ปล่อย Release `v0.3.0` · ดู [`docs/roadmap.md`](docs/roadmap.md)
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
  · **เพิ่ม key ใหม่ต้องแก้ `ja.json` ด้วย** ไม่งั้นเทสต์ `test_ja_asset_full_translation` fail
- **Windows: ปัก taskbar อัตโนมัติ = เป็นไปไม่ได้** (Win10 21H2 → Win11 ปิดหมด · เอกสาร MS:
  *"programmatic pinning by an application is not permitted"*) · ทดสอบแล้วหมด:
  `copy2` ไม่มีผล · Shell COM verb ถูกถอด · `IPinnedList3::Modify` (วิธีที่ Chromium/Firefox
  ใช้) คืน `S_OK` แต่ไม่มีผลจริง → **ทางเดียวคือผู้ใช้ลาก `.lnk` ไปวางเอง**
  · เมนู "Pin to taskbar" ไม่ขึ้นบนเครื่องที่ไม่มี `LayoutModification.xml` (Win11 ถือว่า taskbar ถูกล็อก
    → ปักเองไม่ได้แม้แต่แอปอื่น) · **ต้นฉบับ Taskbar Groups ก็ทำไม่ได้** (สั่ง user คลิกขวาเอง)
- **Windows: AUMID สำคัญ (ต้องมีทุกกลุ่ม)** — Windows รวมปุ่ม taskbar ตาม AppUserModelID
  ถ้าทุกกลุ่มใช้ AUMID เดียวกับตัวแอป ปุ่มจะ**ซ้อนกันเหลือปุ่มเดียว** (ต้นฉบับเขียนว่า
  *"tricks Windows to think they are from different applications"*)
  · ตั้งใน `.lnk` = ต้องใช้ COM `IShellLinkW` + `IPropertyStore` (ctypes, `core/win32_com.py`)
    → **PowerShell `WScript.Shell` ตั้ง AUMID ไม่ได้** (ของเดิมใช้ PowerShell = ต้องเปลี่ยนมา COM)
  · ตอนเปิด flyout ต้องเรียก `SetCurrentProcessExplicitAppUserModelID` ให้ตรงกับ `.lnk`
  · gotcha: `CoCreateInstance` ต้องเรียก `CoInitializeEx` **ก่อน** ไม่งั้นได้ `0x800401F0`
  · ระบุ "user ลากวางแล้วหรือยัง" = อ่าน AUMID จากไฟล์ใน `User Pinned\TaskBar`
    (ไฟล์นั้น Windows เป็นคนเขียนตอนผู้ใช้ลากวาง · **Windows เปลี่ยนชื่อไฟล์ให้เองได้**
    เช่นชนกับ `.lnk` ของแอปอื่น → `Game.lnk` กลายเป็น `Game (2).lnk`)
    → **ห้ามใช้ชื่อไฟล์เป็นตัวระบุ** · ต้องเอาชื่อกลุ่มจาก `list_groups()`
    มาเทียบ AUMID แล้วคืน `lnk_name(ชื่อกลุ่ม)`
- **Windows: ชื่อไฟล์ `.lnk` = ชื่อกลุ่ม** — Windows เอาชื่อไฟล์ไปแสดงบน taskbar/Start
  (`taskbargroups-game.lnk` → โชว์ยาวๆ, `Game.lnk` → โชว์ "Game")
  · เก็บ `.lnk` ไว้ที่ **`config/shortcuts/`** ไม่ใช่ Start Menu (portable เหมือนฝั่ง Linux)
- **Windows: UX ปุ่มสถานะต่างจาก Linux โดยเจตนา** — ปุ่มตา toggle ได้เฉพาะ Linux
  (ที่ปัก/ถอนจริง) ฝั่ง Windows เป็น **ปุ่มโฟลเดอร์** = เปิด Explorer ให้ผู้ใช้ลากวาง
  · สร้างกลุ่มแล้วสร้าง `.lnk` ให้อัตโนมัติ ไม่งั้น user ไม่มีไฟล์ให้ลาก
- **packaging:** เครื่องไม่มี pip/python3-venv (venv `--without-pip`) · repo อยู่บน fuseblk (chmod ไม่ติด → สคริปต์ `.deb` สเตจ `/tmp`)
  · ไม่มี `libxcb-cursor0` → รันจากซอร์สต้องมี `lib/libxcb-cursor.so.0` แล้ว `__main__` re-exec ตั้ง `LD_LIBRARY_PATH`

## ที่เก็บไฟล์ (เครื่องนี้) — ข้อตกลง 🚩

> ตั้งขึ้นเพราะเดิมไฟล์เกลื่อนหลายที่ พอความจำหายแล้วสร้างใหม่ เลยหาไม่เจอ — **รวมที่เดียว**

- **โปรเจกต์ (ทำงาน):** `/mnt/Backup/TaskbarNoob` = source หลัก (SSH remote · `core.fileMode false` · มี `.venv` + `lib/libxcb-cursor.so.0`)
- **AppImage ที่ใช้จริง/เทสต์ = ที่เดียว:** `/home/noob/AppImage/Tool/TaskbarNoob-x86_64.AppImage`
  → หลัง `bash packaging/build_appimage.sh` **คัดลอกไฟล์ไปทับที่นี่เสมอ** · **อย่าเทสต์จาก `dist/` ตรง ๆ**
- **config จริง (portable):** `/home/noob/AppImage/Tool/config/` (อยู่ข้าง AppImage) — groups: Game · Production · Tool
  · รันจากซอร์สให้ชี้มาที่นี่: `TASKBARGROUPS_CONFIG=$HOME/AppImage/Tool/config`
- **build output:** `<repo>/dist/` = ที่พักผลลัพธ์ชั่วคราว (gitignored) — ไม่ใช่ที่ใช้ประจำ
- **โฟลเดอร์เก่า (สำรอง):** `/mnt/Backup/TaskbarGroups/` = **สำรองเท่านั้น** (commit เก่าก่อน v0.2.0 + สำเนา config เก่า) · อย่ารันจากที่นี่
- **กติกา:** AppImage มีที่เดียว · กลุ่มจริงมีที่เดียว · ถ้าเจอไฟล์ซ้ำที่อื่น = ให้ถือที่ตามข้างบนนี้

## วิธีรัน / Dev
- รันแอป: `.venv/bin/python -m taskbargroups`
- เปิด flyout: `... -m taskbargroups --open "<GroupDir>"` · list: `... --list`
- เทสต์: `QT_QPA_PLATFORM=offscreen .venv/bin/python tests/run.py` → **375 เทสต์ ผ่าน 100% (skipped=10 Windows-only)**
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
│          launchers.py + taskbar.py (dispatch ข้าม OS · ชื่อฟังก์ชันเดียวกันทุก OS)
│          win32.py + win32_com.py (COM IShellLinkW · AUMID · PNG→ICO)
│          macos.py · win32_hotkey อยู่ฝั่ง gui
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

## งานถัดไป (Next Actions — v0.3.0)
1. **R1:** แยก Platform Backend เข้า `core/platform/{base,linux,win32}` + พับเก็บ `core/macos.py` + ลด `sys.platform` ใน `gui/`
2. **R2:** แตกไฟล์ยักษ์ (`gui/main_window.py`, `gui/group_editor.py`, `core/win32.py`) เป็นโมดูลย่อยหน้าที่เดียว
3. **R3:** รวม icon pipeline เป็นจุดเดียว (เลิก circular import) + ตัวเลือกไอคอนระบบแบบแยกหมวดบน Mint + Steam `steam://rungameid/<appid>` icon resolver ข้าม OS
4. **R4:** เก็บกวาด Dead Code / แยก `i18n` + รีแบรนด์ชื่อภายใน `taskbargroups` → `taskbarnoob` พร้อม Auto-Migration + เปลี่ยนเครดิตเป็น `Noob & Jenny`
5. อย่าลืม: อัปเดต `docs/WORKLOG.md` และรันเทสต์ให้เขียว 100% ทุกเฟสก่อน commit

## เอกสารอ้างอิง
- `docs/README.md` — แผนที่/ดัชนีเอกสาร (รวม `docs/archive/`)
- `docs/roadmap.md` — แผนภาพรวมทุกเฟส + แผน `v0.3.0` (R0–R4)
- `docs/WORKLOG.md` — ประวัติงานภาค `v0.3.0+` (ภาคเก่าอยู่ที่ `docs/archive/WORKLOG-v0.1-v0.2.md`)
- `docs/feedback.md` — งานค้างและฟีดแบ็กที่ยังไม่ปิด
- `docs/data-model.md` — สกีมา + ฟอร์แมตเก็บกลุ่ม
- `docs/team.md` — บทบาทและแนวทางการทำงานร่วมกัน
- `docs/upstream.md` — ผลวิจัยต้นฉบับ Windows + ฟีเจอร์ค้างใน PR