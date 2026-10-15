# Work Log — TaskbarGroups (Linux Mint)

> บันทึกงานย้อนหลังต่อเฟส (append-only). AGENTS.md เก็บแค่ snapshot ปัจจุบัน
> ดูรายละเอียดสเปกที่ docs/data-model.md · ต้นฉบับที่ docs/upstream.md

## 2026-10-10 — Phase 0: Brainstorm / สรุปสเปก `[เสร็จ]`
- เป้าหมาย: ทำแอปคล้าย Taskbar Groups บน Linux Mint (Cinnamon) + รองรับ Windows ทีหลัง
- ไล่เปรียบเทียบ 4 แนวทาง: Wine / Cinnamon applet / Qt-Python / rofi
- ตัดสินใจ: **ไม่เอา rofi** (อยากได้ grid ไอคอน) → **เลือก Qt/PySide6** เพราะข้าม OS
  (GTK/PyGObject ตกเพราะติดตั้งบน Windows ยาก)
- กำหนดให้ **config เป็น Portable** ในโฟลเดอร์แอป
- ตั้งชื่อผู้ช่วย: "น้องพริก"

## 2026-10-10 — Phase 1: Data model + โครงไฟล์ `[เสร็จ]`
- ออกแบบ `group.json` (มี `schema_version`) + โครง `config/groups/<GroupName>/`
- สถาปัตยกรรม: แยก `core/` (Python ล้วน) ออกจาก `gui/` (Qt)
- เขียน `core/models.py` (Group/Shortcut/ColorMode + validation)
  `core/storage.py` (ConfigStore) `core/paths.py` (portable path + env override)
- เอกสาร: `docs/data-model.md`
- เทสต์: test_models + test_storage → รวม 22 ผ่าน

## 2026-10-10 — Phase 2: MVP `[เสร็จ]`
- venv + ติดตั้ง PySide6 6.12.0 (เครื่องไม่มี pip → venv `--without-pip` + get-pip.py)
- `core/launcher.py` — เปิด shortcut ข้าม OS (Linux `gio`/Popen, Windows `os.startfile`, macOS `open`)
- `gui/main_window.py` — list + เพิ่ม/แก้/ลบ/เปิดกลุ่ม
- `gui/group_editor.py` — แก้ไขกลุ่ม + จัดการรายการ shortcut
- `gui/flyout.py` — grid ไอคอน, hotkey 1-0, Ctrl+Enter, สี/opacity
- `gui/icons.py` — ไอคอนจาก cache/ไฟล์/ธีม
- เทสต์: test_launcher + test_gui_smoke → รวม 31 ผ่าน

## 2026-10-10 — Phase 3: ผูก panel `[เสร็จ]`
- `core/desktop.py` — สร้าง/ติดตั้ง/ลบ `.desktop` launcher (`~/.local/share/applications/`)
- `core/hotkeys.py` — ตั้ง global hotkey ผ่าน gsettings ของ Cinnamon + parse GVariant
- CLI: `--open <GroupDir>`, `--list`
- GUI: ปุ่ม "ติดตั้ง launcher" + "ตั้ง hotkey" (แปลง QKeySequence → รูปแบบ Cinnamon)
- เทสต์: test_desktop + test_hotkeys + gui conversion → รวม 46 ผ่าน
- หมายเหตุ: ยังไม่มีการแตะ keybinding จริงของผู้ใช้ (เทสต์ใช้ runner ปลอม)

## 2026-10-10 — Phase 4: เก็บงาน `[เสร็จ]`
- `core/icons.py` — resolve ไอคอน (ไฟล์รูป, `.desktop` อ่าน `Icon=`, ชื่อในธีม)
  + แคชลง `icons/` ของกลุ่ม (Python ล้วน ไม่ผูก Qt)
- `core/importer.py` — อ่าน `ObjectData.xml` ต้นฉบับ (.NET XmlSerializer: `Category`/`ProgramShortcut`)
  → `Group` + `import_group()` คัดลอก `GroupImage.png`/`GroupIcon.ico` และไอคอนใน `Icons/`
  (เข้าใจ path แบบ Windows, ตั้งชื่อกลุ่มอัตโนมัติถ้าซ้ำ)
- GUI: ShortcutDialog เลือก/ดึงไอคอนอัตโนมัติ + แคชตอบ Save · ปุ่ม "นำเข้ากลุ่ม..."
- Flyout: ปุ่ม "เปิดทั้งหมด" · สีตัวอักษรตามความสว่างพื้นหลัง · hover เข้าธีม light/dark
- CLI: `--import "<โฟลเดอร์ ObjectData.xml>"`
- เทสต์: test_icons + test_importer + gui smoke เพิ่ม → รวม **82 ผ่าน**
- หมายเหตุ: opacity/สี map ตรงกับต้นฉบับ (dark `#1F1F1F`, light `#E6E6E6`, opacity = `1 - v/100`)

## 2026-10-10 — Phase 5: Packaging `[เสร็จ]`
- `core/paths.py` — `app_dir()` อิง `$APPIMAGE` / frozen / source ; `default_config_dir()`
  เลือก `<app>/config/` แบบ portable ถ้าเขียนได้ ไม่ได้ก็ fallback `~/.config/taskbargroups`
- `core/desktop.py` — `build_exec()` รองรับ 4 โหมด (python=, `$APPIMAGE`, frozen, source)
- `packaging/entrypoint.py` + `make_icon.py` (วาดไอคอนแอปด้วย Qt, cross-OS)
- `packaging/build_appimage.sh`: PyInstaller (onedir, `--collect-submodules`) → AppDir
  → bundle `libxcb-cursor.so.0` (apt download + dpkg-deb -x) + `AppRun` ตั้ง `LD_LIBRARY_PATH`
  → `appimagetool --no-appstream` → `dist/TaskbarGroups-x86_64.AppImage` (~61 MB)
- `packaging/build_deb.sh` → `dist/taskbargroups_<ver>_amd64.deb` (~51 MB)
  ติดตั้งที่ `/usr/lib/taskbargroups` + wrapper `/usr/bin/taskbargroups`
- บทเรียน: AppImage รันใน env นี้ต้อง `APPIMAGE_EXTRACT_AND_RUN=1` (FUSE mount ไม่ได้)
  · Qt ≥6.5 ต้องมี `libxcb-cursor.so.0` ไม่งั้น xcb plugin โหลดไม่ขึ้น
  · repo อยู่บน fuseblk (chmod ไม่ติด) → `.deb` ต้องสเตจใน `/tmp` ก่อน `dpkg-deb --build`
- เทสต์: test_paths ใหม่ + test_desktop เพิ่ม (APPIMAGE exec) → รวม **89 ผ่าน**
- รันทดสอบจริง: GUI บน `DISPLAY=:0` (X-Cinnamon) ผ่าน (โหลด xcb ได้หลัง bundle) · CLI `--list`/`--import` ผ่าน

## 2026-10-10 — รับฟีดแบ็ก #1 (จาก AppImage) `[รอทำ]`
- ผู้ใช้รัน AppImage แล้วเสนอ 5 ข้อ: F1 pin ลง taskbar · F2 ดับเบิลคลิกแก้ไข ·
  F3 ไอคอนบน taskbar คลิกเปิด popup · F4 opacity default 10% ·
  F5 flyout โปร่งแสง 100% + ปรับขนาดไอคอน (default = ขนาด taskbar)
- บันทึกละเอียด + แผน Phase 6 (Qt ล้วน) / Phase 7 (Cinnamon panel) ที่ `docs/feedback.md`
- ยังไม่เริ่มแก้โค้ด (รอ confirm)
- 2026-10-10 — รับฟีดแบ็กเพิ่ม F6–F9: สไลเดอร์ opacity (default 10%) · shortcut list เป็น Grid
  (tooltip path, dblclick แก้ไข, reorder) · drag & drop เพิ่ม shortcut · จัดปุ่มหน้าต่างหลักใหม่
  (ลบ "เปิดกลุ่ม" ย้าย "นำเข้า" แทน + เฟือง Setup เก็บ launcher/hotkey)
  → ปรับแผนเป็น Phase 6 (settings/flyout) · Phase 7 (shortcut editor) · Phase 8 (Cinnamon panel)
  + เพิ่มไอเดียเสนอใน docs/feedback.md · ยังไม่เริ่มแก้

## 2026-10-10 — Phase 6: Settings & Flyout polish `[เสร็จ]`
- **F4/F6** `Group.opacity` default `0 → 10` + เปลี่ยนช่องความโปร่งใสใน `group_editor.py`
  เป็น **สไลเดอร์ 0–100 %** (โชว์ตัวเลข)
- **F5** เพิ่มฟิลด์ `Group.icon_size` (default 32 px, ช่วง 16–128) + validate/round-trip
  · flyout เปิด `WA_TranslucentBackground` (พื้นรอบนอกโปร่ง ไม่มี 4 เหลี่ยมขาวแล้ว)
  · ขนาดไอคอน/ปุ่มใน flyout คำนวณจาก `icon_size`
  · เพิ่ม **สไลเดอร์ขนาดไอคอน + preview** ในหน้าต่างแก้ไขกลุ่ม
- **F2** ดับเบิลคลิกไอคอนกลุ่มในหน้าต่างหลัก → เปิดแก้ไข (เก็บปุ่ม "แก้ไข" ไว้)
- **F9** จัดปุ่มหน้าต่างหลักใหม่: ลบ "เปิดกลุ่ม" · ย้าย "นำเข้ากลุ่ม..." มาแทน ·
  เพิ่มปุ่ม **เฟือง ⚙ Setup** (เก็บ "ติดตั้ง launcher" + "ตั้ง hotkey" ในเมนู)
- **F1 (บางส่วน)** เพิ่มปุ่ม "ปักหมุด": ติดตั้ง `.desktop` แล้วเรียก `core/panel.py` ลองปักหมุด
  อัตโนมัติ (grouped-window-list JSON → fallback `org.cinnamon panel-launchers`) ถ้าไม่ได้ให้ลากเอง
  · **หมายเหตุ:** บน Mint ปัจจุบัน `org.cinnamon panel-launchers` = `['DEPRECATED']` และไม่พบ
    ไฟล์ config ของ grouped-window-list ในเครื่องทดสอบ → ยังปักหมุดอัตโนมัติไม่ได้จริง (จะเก็บจริง Phase 8)
- เทสต์: เพิ่ม `tests/test_panel.py` + อัปเดต `test_models`/`test_gui_smoke` → รวม **101 ผ่าน**

## 2026-10-10 — Phase 7: Shortcut editor เป็น Grid `[เสร็จ]`
- **F8** `group_editor.py` เปลี่ยน "รายการ shortcut" เป็น **Grid** (`ShortcutGrid` = QListWidget IconMode)
  · tooltip = target (path) · **ดับเบิลคลิกไอคอน = แก้ไข** · **ลากสลับลำดับ (InternalMove)** → sync `Group.items`
- **F7** รับ **drag & drop จาก file manager** (`dragEnter/Move/dropEvent` จับ `hasUrls()`)
  → `core/desktop.shortcut_from_path()` สร้าง Shortcut (`.desktop` อ่าน `Name=` · ไฟล์อื่นใช้ชื่อไฟล์)
  · ไอคอน resolve/cache ผ่าน flow เดิม (`resolve_icon_source` + `pending_icons`)
- เพิ่ม helper: `core/desktop.read_desktop_name()`, `shortcut_from_path()`
- เทสต์: เพิ่ม grid drop/reorder (gui smoke) + shortcut_from_path → รวม **107 ผ่าน**
- 2026-10-10 — รับฟีดแบ็ก F10–F14: Pin ต่อแถว (ไอคอนเข็มหมุดท้ายสุด) · สลับลำดับกลุ่มในหน้าต่างหลัก ·
  ไอคอน grid ใหญ่ขึ้น + ดึงไอคอนจริงจากแอปที่ลากวาง · รวมสี mode+custom เป็น 2 คอลัมน์ ·
  ช่อง opacity/icon size พิมพ์ตัวเลขได้
  → เลื่อน Cinnamon panel ไป **Phase 9 (ท้ายสุด)** · เพิ่ม **Phase 8 = UI polish รอบ 2** · ยังไม่เริ่มแก้

## 2026-10-10 — Phase 8: UI polish รอบ 2 `[เสร็จ]`
- **F11** สลับลำดับกลุ่มในหน้าต่างหลัก: `GroupListWidget` (QListWidget `InternalMove`)
  + `_on_rows_moved` → `ConfigStore.save_order` (เก็บ `order.json`) · `list_groups()` เรียงตาม order
- **F10** ปุ่มปักหมุดย้ายเป็น **ต่อแถว**: วาดรูปเข็มหมุดท้ายสุดของแต่ละแถว
  (ใช้ธีม `view-pin`/`pin` ก่อน ถ้าไม่มีวาดรูปเอง) · คลิกโซนขวาสุดของแถว = ปักหมุดกลุ่มนั้น
  · เอาปุ่ม "ปักหมุด" global ออก · เก็บ hover highlight
- **F12.1** ไอคอน grid ในตัวแก้ไขขยาย 48 → **64 px** (grid 112×108)
- **F12.2** ดึงไอคอนจริงจากแอปที่ลากวาง: `resolve_icon_source` (.desktop/ไฟล์รูป)
  + `icon_from_executable` (จับ Exec= ใน .desktop) → เก็บเป็น pending แล้วแคชตอน save
- **F13** รวม "สีพื้นหลัง (mode)" กับ "สีกำหนดเอง" เป็นแถวเดียว แบ่งครึ่ง **2 คอลัมน์**
- **F14** ช่อง opacity + icon size มีทั้งสไลเดอร์และ **spinbox พิมพ์ตัวเลข** ผูกสองทาง
- แก้ import ที่ค้าง (`QAbstractItemView`) จาก session ก่อนหน้าที่ค้างกลางทาง
- เทสต์: เพิ่ม pin click (ยิง/ไม่ยิง) + drop `.desktop` แคชไอคอน → รวม **110 ผ่าน**

## 2026-10-10 — Phase 9: Cinnamon panel integration (F1/F3 ของจริง) `[เสร็จ]`
- **ปักหมุดจริงลง panel:** `panel-launchers` ใช้ไม่ได้แล้ว (ค่า `['DEPRECATED']`) → ใช้
  **Grouped Window List applet** แทน โดยแก้ไฟล์ config JSON ของ applet
  - path ที่ถูกต้อง: `~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/<instance>.json`
    (เคารพ `XDG_CONFIG_HOME`) · path เก่า `~/.cinnamon/configs/...` เป็น fallback
  - เพิ่ม desktop id เข้า key `pinned-apps.value`
- `core/panel.py`: เพิ่ม `grouped_window_config_dirs()` · `_grouped_window_config_files()` ·
  `add_grouped_window_pin()` · `reload_grouped_window_applet()` (gdbus `org.Cinnamon.ReloadXlet`
  `<uuid> APPLET` — **ต้องเป็น "APPLET" ตัวพิมพ์ใหญ่**) · `pin_to_panel(..., refresh=True)`
- **race ตอนแอปใหม่:** applet reload รอบแรกอาจ resolve `lookup_app()` ไม่เจอ (app system ยังไม่รู้จัก
  .desktop ที่เพิ่งสร้าง) → favorites ได้ `app: null` → `main_window.on_pin` จึงตั้ง
  `QTimer.singleShot(2500, reload_grouped_window_applet)` ให้ reload ซ้ำอีกรอบ
- **แก้บั๊กคลิกไอคอนบน panel แล้วไม่เปิด flyout:** Cinnamon รัน .desktop ด้วย CWD ไม่ใช่ repo →
  `python -m taskbargroups` หาโมดูลไม่เจอ (exit 1) → เพิ่ม `Path=<app_dir>` ใน .desktop
  (`core/desktop.py`) ให้ GAppInfo ตั้ง working directory ถูกต้อง
- **รันจากซอร์สบนเครื่องที่ไม่มี `libxcb-cursor0`:** Qt xcb plugin โหลดไม่ได้ → `__main__._ensure_bundled_libs()`
  re-exec ตัวเองพร้อม `LD_LIBRARY_PATH=<app_dir>/lib` ถ้าพบ `lib/libxcb-cursor.so.0` (โหมด source เท่านั้น;
  AppImage/.deb จัดการเอง) · โฟลเดอร์ `lib/` gitignore
- เทสต์: เพิ่ม `test_panel` (reload gdbus, config dirs, pin idempotent) + assert `Path=` ใน .desktop → รวม **115 ผ่าน**
- **ยืนยันจริงบน Cinnamon 6.6.9:** pin → เขียน config → ReloadXlet → ไอคอนกลุ่มขึ้น panel จริง →
  คลิกครั้งเดียวเปิด flyout สำเร็จ (ทดสอบแล้วเก็บ pin/launcher/กลุ่มทดสอบออกเรียบร้อย)

## 2026-10-10 — Phase 10: Pin toggle & state (F15) `[เสร็จ]`
- **บริบท:** ผู้ใช้รายงานซ้ำ F10–F14 หลังทดสอบ AppImage — พบว่า AppImage เป็น build เก่า (16:59)
  ก่อนโค้ด Phase 8/9 (18:04+) → ฟีเจอร์มีในซอร์สครบแต่ยังไม่ repackage (ไปทำ Phase 11)
- **F15** ปุ่มปักหมุดเป็น **toggle**: ปักถ้ายังไม่ปัก / ถอนถ้าปักอยู่แล้ว
- `core/panel.py`: เพิ่ม `grouped_window_pinned_ids()` · `pinned_desktop_ids()` · `is_pinned()` ·
  `remove_grouped_window_pin()` · `remove_panel_launcher()` · `unpin_from_panel()` (reload applet เมื่อถอด)
- `gui/main_window.py`: `GroupListWidget` วาดไอคอนเข็มหมุดตามสถานะ — ปักแล้วทึบสี `Highlight`,
  ยังไม่ปักสีจาง · `refresh()` ตั้ง `PINNED_ROLE` + tooltip บอกสถานะ · `on_pin` แยก `_pin`/`_unpin`
- เทสต์: +6 (panel pinned ids/remove/unpin, gui refresh ตั้งสถานะ) → รวม **121 ผ่าน**

## 2026-10-10 — Phase 11: Repackage `[เสร็จ]`
- rebuild `dist/TaskbarGroups-x86_64.AppImage` (61M) + `dist/taskbargroups_0.1.0_amd64.deb` (51M)
  จากโค้ดล่าสุด (Phase 8/9/10) · ทดสอบ AppImage: `--list` เห็นกลุ่ม · GUI บูตผ่าน

## 2026-10-10 — Phase 12: AppImage icon + group order fix (F16–F18) `[เสร็จ]`
- **บริบท:** ผู้ใช้ทดสอบหลัง Phase 11 · งานส่วนใหญ่ผ่าน แต่เจอ 3 บั๊ก (ไอคอน AppImage · ไอคอนเล็ก · ลากสลับลำดับกลุ่มไม่จำ)
- **F16/F17 — ดึงไอคอนจริงจาก `.AppImage`:**
  - `core/icons.py` เพิ่ม `is_appimage()` (ตรวจ ELF magic `AI\x02` หรือ suffix `.AppImage`) ·
    `icon_from_appimage()` · `_extract_appimage_icon()` / `_find_appimage_icon()` / `_icon_from_appimage_desktop()`
  - แตกไฟล์ด้วย `subprocess [target, "--appimage-extract"]` ใน temp (ไม่ต้อง mount/FUSE) →
    หาไอคอนจาก `.DirIcon` → `Icon=` ใน `.desktop` ที่ root → ไฟล์รูปที่ใหญ่สุดใน squashfs-root
  - แคชที่ `$TMP/taskbargroups-appimage-icons/<sha1(path+mtime+size)>.<ext>` (รอบสองเร็วมาก)
  - ต่อเข้า `resolve_icon_source()` + `icon_from_executable()` → ลาก `.AppImage` ได้ไอคอนจริง 256px
  - `gui/group_editor.py` `_icon_for()`: resolve ไอคอน AppImage ให้ item เดิมที่ยังไม่มีไอคอน (โชว์ใหญ่ทันที)
  - **ยืนยันจริง:** Photocraft/Vectorcraft ได้ PNG 256×256 (61K/56K), 0.5s ครั้งแรก, cache hit 0.0006s
- **F18 — ลากสลับลำดับกลุ่มไม่จำ:**
  - ต้นเหตุ: `GroupListWidget` ต่อ `model().rowsMoved` แต่ **QListWidget InternalMove ยิงแค่
    `rowsInserted`/`rowsRemoved` ไม่ยิง `rowsMoved`** → `_on_rows_moved` ไม่เคยถูกเรียก → ไม่บันทึก `order.json`
  - แก้: `GroupListWidget` override `dropEvent()` → `super().dropEvent()` แล้ว emit `Signal orderChanged`;
    `MainWindow` ต่อ `orderChanged → _on_rows_moved` · เพิ่ม `setDragEnabled`/`setDropIndicatorShown`/`setMovement(Snap)`
- เทสต์: +8 (`AppImageTests` 6 · `test_group_list_emits_order_changed_on_drop` · `test_main_window_saves_group_order_on_change`) → รวม **129 ผ่าน**

## 2026-10-10 — Phase 14: Flyout & drag UX + ธีม (F19–F24) `[เสร็จ]`
แบ่งเป็น 4 sub-phase (14a–14d) ตามแผน · เคาะสเปกรอบละเอียด + คำตอบสุดท้ายใน `docs/feedback.md`

### 14a — Flyout single-instance + ตำแหน่ง (F19/F20)
`gui/flyout.py`:
- `FlyoutController(QObject)`: single-instance **ข้าม process** —
  `QLocalSocket` พยายาม `try_delegate()` (ส่ง `--open <group>` ให้ primary) → ไม่มี primary → `start_primary()`
  (`QLocalServer` + `removeServer` + `newConnection`) · `default_server_name()` = `taskbargroups-<uid>`
- เปิดกลุ่มใหม่ → `deleteLater()` อันเก่า · คลิกกลุ่มเดิม → คงไว้ (ไม่สร้างใหม่) · ปิดเมื่อคลิกที่อื่น (`hideEvent`)
- `FlyoutWindow.closed = Signal()` — close/hide ยิงครั้งเดียว (`_emit_closed`) → controller ตั้ง quit timer (`QUIT_GRACE_MS=4000`)
- `show_at_cursor()` → `flyout_position(cursor_pos, size, screen, offset=6)`:
  กึ่งกลางแนวนอนเหนือเมาส์ · clamp ขอบจอ · พื้นที่ไม่พอ → พลิกใต้ (`MOUSE_OFFSET=6`)
- `main_window.py` `_run_flyout` → ใช้ controller, `controller.shutdown()` หลัง `app.exec()`
- **บั๊กหนักที่เจอและแก้:** ตั้ง `self.window=None` ใน `_on_closed` ระหว่าง `closeEvent` → Python GC ทำลาย popup
  กลางเหตุการณ์ → heap corruption (`Malloc: unaligned fastbin chunk`) → แก้เป็น `window.deleteLater()`
- **Cross-process verify:** 2 processes offscreen — secondary delegate ผ่าน QLocalSocket ออก 0.49s (exit 0)
  · primary ยังอยู่ · `DELEGATE_TIMEOUT_MS=350` fallback เป็น primary เอง

### 14b — Grid drag precision + ไฮไลท์ช่องเป้าหมาย (F21/F22)
`gui/group_editor.py` — เขียน `ShortcutGrid` (QListWidget IconMode) ใหม่ทั้งหมด:
- **ก่อนแก้:** `dropEvent` ของ IconMode วางมั่ว (เด้งไปมา ไม่ตรงที่ปล่อย) · Qt built-in
  `setDropIndicatorShown` **ใช้ไม่ได้ใน IconMode** — ซอร์ส Qt มี `FIXME: Until we can provide a proper
  drop indicator in IconMode` → ต้องทำ **custom** ทั้ง reorder + ไฮไลท์ (เบี่ยงตามแผนแนวทาง A)
- `_target_row(pos)`: `indexAt` → ช่องเป้าหมาย (ครึ่งแรก=ก่อน, ครึ่งหลัง=หลังช่อง) · ตำแหน่งว่างเกิน item
  สุดท้าย → **ต่อท้าย** · ไม่เจอเลย → ช่อง nearest
- `_move_item(source, target)` ใช้ `model().moveRow()` · ยิง `orderChanged` → บันทึกลำดับได้
- `_DropHighlightDelegate(QStyledItemDelegate)` วาดไฮไลท์ **ทับช่องเป้าหมาย** สี `palette.Highlight`
  (alpha 80) + pen 2px + มุมมน 10px — ตำแหน่งเดียวกับที่ปล่อยจริง · override
  `startDrag`/`dragEnter`/`dragMove`/`dragLeave`/`dropEvent` + `drop_highlight_row`
- ลากไฟล์จาก file manager ยังได้ (urlsDropped) + เห็น highlight ตอน hover เป้าหมาย

### 14c — ธีม (auto/light/dark) + หน้าต่างตั้งค่า (F23/F24)
- `core/settings.py` (ใหม่): `Settings(config_dir=None)` อ่าน/เขียน `config/settings.json`
  · `get_theme()/set_theme()` · `VALID_THEMES=("auto","light","dark")` · `DEFAULT_THEME="auto"`
  · ค่าไม่ถูกต้อง/JSON เสีย → fallback auto
- `gui/theme.py` (ใหม่): `resolve_theme(setting, app)` — auto อ่าน `app.styleHints().colorScheme()`
  (Qt.ColorScheme.Dark/Light) · `apply_theme(app, theme)` ผ่าน **QPalette** (ไม่แตะ Taskbar/ชุด Cinnamon):
  dark = window `#2b2b2b`, base `#1e1e1e`, button `#3c3c3c`, highlight `#2f5d8a` … · light = standard palette
- `gui/settings_dialog.py` (ใหม่): `SettingsDialog` — combo ธีม (ตามระบบ/สว่าง/เข้ม) เปลี่ยนแล้ว
  `set_theme()` + `apply_theme()` **ทันที** · ปุ่ม "ติดตั้ง launcher" → `on_install_launcher` ·
  "ตั้ง hotkey" → `on_set_hotkey` (ใช้ฟังก์ชันเดิม ย้ายจาก QMenu) · เฟือง ⚙ เปิด dialog นี้แทน
- `main_window.py` `run()`: อ่าน `Settings().get_theme()` → `apply_theme` ตั้งแต่บูตก่อนโชว์หน้าต่าง

### 14d — Repackage + ทดสอบรวม `[เสร็จ]`
- เทสต์ใหม่: `tests/test_flyout.py` (9: flyout_position clamp/พลิก · closed signal · controller delegate/reuse/switch) ·
  `tests/test_grid_drag.py` (8: _move_item, dropEvent memory ของ QMimeData, urlsDropped, _target_row, ว่าง=ต่อท้าย) ·
  `tests/test_settings.py` (10: settings.json roundtrip/corrupt/fallback · resolve_theme · apply_theme palette ·
  SettingsDialog เปลี่ยนธีมบันทึก) → รวม **157 ผ่าน** (129 → +28)
- rebuild `dist/TaskbarGroups-x86_64.AppImage` (61M, 22:42) + `dist/taskbargroups_0.1.0_amd64.deb` (51M, 22:43)
- ตรวจ PYZ ใน AppImage: มี `core.settings` / `gui.theme` / `gui.settings_dialog` / `gui.flyout` / `gui.group_editor` ครบ
- บูตจริง offscreen: หน้า GUI รันได้ (exit 124 = timeout ฆ่า) · `dist/config` (ข้อมูลกลุ่มจริง) ยัง intact
- หมายเหตุ: เทสต์ชุดรวมมี heap crash ตอน teardown แบบ flaky บน offscreen — เป็นของเดิมก่อนโค้ดใหม่
  (รันโมดูลเติมที่ยังไม่แก้อีก 9 โมดูลก็ยังคราช 2/5) ไม่กระทบผลเทสต์

## 2026-10-10 — Phase 15: Bug + UI compact + i18n (B1 · 2.x · 3.x · 4.x) `[เสร็จ]`
แบ่ง 15a–15e · เบรนสตอร์มสเปกเต็ม (รอบ #8) + วิธีแก้ B1 พิสูจน์จากซอร์ส Qt แล้วใน `docs/feedback.md`

### 15a — B1: ไอค่อนที่ลากในกริดหาย (ตอน reorder ผ่าน drag จริง)
- **ราก bug (ล็อกจากซอร์ส Qt 6.12 ที่รันจริง):** หลัง `QAbstractItemView::startDrag` / `QIconModeViewBase::filterStartDrag`
  ตั้ง `dropEventMoved=false` → `drag->exec(...)` คืน `MoveAction` → ถ้า `!dropEventMoved` และ
  (`dragDropMode != InternalMove` หรือ `target==viewport`) → เรียก **`clearOrRemove()`** ซึ่งลบแถวที่**ถูกเลือก**
  - `dropEventMoved` จะถูกตั้ง `true` เฉพาะใน `QListView::dropEvent` (สาขา icon-mode moveRow) — แต่
    `ShortcutGrid` override `dropEvent` เอง (ไม่เรียก super) จึงไม่เคยตั้ง → ครบเงื่อนไขเสมอ
  - ท้าย `_move_item` มี `setCurrentItem(item)` = สร้างการเลือก → `clearOrRemove()` รันแล้วลบไอเทมที่เพิ่งย้าย → **ไอค่อนหาย**
- **แก้:** ใน `ShortcutGrid.dropEvent` หลัง `_move_item(source, target)` เรียก **`self.clearSelection()`** —
  `clearOrRemove()` เห็น selection ว่าง → ไม่ลบอะไร (ตัว drag เองก็เลิก highlight หลังปล่อยพอดี)
- **เทสต์:** `test_internal_drop_leaves_selection_empty` guard เงื่อนไขนี้โดยตรง —
  **ยืนยัน pre-fix**: จำลอง dropEvent แบบไม่ clear selection → order ถูกแต่ `selectedItems()=['i0']` (จะโดนลบควับ)
  → เทสต์ fail · post-fix selection ว่าง → pass
- ⚠️ จำกัดขอบเขต: เทสต์พาดผ่าน `startDrag()` จริงไม่ได้ (modal `drag.exec` บังคับเหตุการณ์จริง — ลอง synthesize บน xcb แล้วค้าง)
  → เทสต์ guard เงื่อนไข (selection ว่าง) ที่ทำให้ cleanup ของ Qt เป็น no-op

### 15b — Group editor UI (2.x)
`gui/group_editor.py`:
- ลบแถว QLabel "ตัวอย่างไอค่อน" + label "(ยังไม่ตั้ง)" · ยุบแถวไอค่อนเป็นแถวเดียว:
  **[พรีวิว QLabel] [เลือกไอคอน...] [เลือกจากระบบ...]** (พรีวิวโฟลเดอร์เหลืองย้ายมาแทนที่ "(ยังไม่ตั้ง)")
- **`_SystemIconDialog` (ใหม่):** กริดไอค่อนสีธีมของระบบ — สแกน `QIcon.themeSearchPaths()` + `/usr/share/icons`
  (theme → ขนาด → หมวด) เอา `*.svg/*.png/*.xpm/*.jpg` (cap 4000 · เพิ่ม priority: svg > png, ใหญ่ > เล็ก, apps > อื่น)
  · ช่องค้นหา (lower ตรงกัน) · กลุ่มแสดง cap 1000 (พิมพ์เพื่อค้นหาเพิ่ม) · ดับเบิลคลิก/ปุ่ม "เลือก"
  → คืน path → ตั้ง `_icon_source` → เพิ่มกลุ่ม icon ผ่าน `store.import_group_icon` (ไหลต่อกับ flow เดิม)
- **สไลด์เดอร์ "ขนาดไอคอน" คุมกริดจริง:** `_refresh_icon_ui()` ตั้ง `icon_preview` pixmap + `items_list.setIconSize(v,v)`
  + `setGridSize(QSize(max(72,v+52), max(72,v+44)))` · เปลี่ยนแล้วเห็นผลทันที (บันทึก `group.icon_size` เท่าเดิม)

### 15c — Width compact (3.x)
- label "จำนวนต่อแถว (width)" → **"แถว"** · ย้ายขึ้น **แถวเดียวกับ "ชื่อกลุ่ม"** —
  form แถวบนเป็น `[ชื่อกลุ่ม][name␣01][แถว][n]` (compact 2 คอลัมน์) → พื้นที่คอลัมน์ว่างหาย ฟอร์มสว่างขึ้น

### 15d — i18n ไทย/อังกฤษ + export/import (4.x)
- **`core/i18n.py` (ใหม่):** dict `TH`/`EN` built-in (ภาษาแม่ = ไทย — fallback ของทุกภาษา) +
  overlay **`config/lang/<code>.json`** · `tr(key, **fmt)` (str.format เฉพาะเมื่อมี args) · `setup(lang, config_dir)` เรียกใน `run()`
  · `available_languages()` = th/en + ไฟล์ใน config/lang · `export_language()` แปลง dict ปัจจุบันเป็น JSON ·
  `import_language()` ตรวจว่าเป็น dict<str,str> แล้วเก็บที่ config/lang/<stem>.json
- **`core/settings.py`:** `get_language()/set_language()` — `settings.json` key `language` (default `th`)
- **`gui/settings_dialog.py`:** แถว "ภาษา/Language" (combo จาก available_languages) — เปลี่ยนภาษา = บันทึก + โชว์
  "จะใช้ภาษาใหม่ในครั้งเปิดแอปถัดไป" · ปุ่ม **"ส่งออกภาษา..."** (บันทึก JSON ปัจจุบัน) + **"นำเข้าภาษา..."** (อ่าน JSON → เพิ่ม combo)
- แปลครบ **5 จอ UI**: หน้าต่างหลัก · แก้ไขกลุ่ม (+ShortcutDialog +_SystemIconDialog) · ตั้งค่า · flyout · hotkey
  (docstring/หมายเหตุในโค้ด + file filter ยังเป็นค่าเทคนิค ไม่ผ่าน tr)
- **ภาษาในตัว: TH (ปิดเผื่อ) / EN** · ผู้ใช้เพิ่มภาษาที่ 3 ได้ผ่าน import
- **หมายเหตุข้อจำกัด:** เปลี่ยนภาษาที่ SettingsDialog แจ้งว่าใช้กับหน้าจอที่เปิดแล้วไม่ได้ทันที (อาศัย rebuild บนเปิดแอปครั้งถัดไป) —
  เพราะสตริงถูก bind ตอน widget สร้าง

### 15e — Repackage + ทดสอบรวม `[เสร็จ]`
- เทสต์ใหม่: `tests/test_group_editor.py` (9: ฟอร์ม/แถว/สไลเดอร์คุมกริด · ปุ่มเลือกระบบ · labels เก่าไม่มี ·
  `_SystemIconDialog` สแกน/ค้นหา/แล้ว-fallback ไทย) + `tests/test_grid_drag.py` +1 (selection ว่าง) +
  `tests/test_i18n.py` (13: th/en default · format · overlay ภาษาผู้ใช้ · available · export/import · settings roundtrip ·
  GUI อังกฤษ/ภาษา-ย่อ) → รวม **180 ผ่าน** (157 → +23, เช่นเดียวกับการนับ 167+13)
- พายาน: recheck `compileall` ผ่าน · offscreen smoke GroupEditor/SettingsDialog/_SystemIconDialog รันได้
- rebuild `dist/TaskbarGroups-x86_64.AppImage` + `dist/taskbargroups_0.1.0_amd64.deb` · `dist/config` ยัง intact

## 2026-10-11 — Phase 16a: Auto-refresh ไอค่อน Taskbar หลังแก้กลุ่ม (N1) `[เสร็จ]`

- **ที่มา:** ฟีดแบ็กผู้ใช้รอบ #9 (N1) — เปลี่ยนไอค่อน/ข้อมูลกลุ่มที่**ปักบน Taskbar อยู่** → ไอค่อนบน panel
  ไม่ refresh จนกว่าจะถอนหมุด+ปักใหม่
- **รากสาเหตุ (ตรวจโค้ด):** `install_launcher` เขียน `Icon=` เป็น**พาธไฟล์ไอค่อนตอนปัก** (`build_desktop_entry`
  → `store.resolve_relative(dir_name, group.icon)`) · พอแก้กลุ่ม `main_window._persist` → `import_group_icon`
  **ลบไฟล์เก่า (glob `group_icon.*`) แล้วเขียนไฟล์ใหม่** (นามสกุลอาจเปลี่ยน png→svg) → พาธเดิมใน .desktop
  ไม่มีจริง + applet จำ cache ไอค่อนเก่า → ต้องถอน/ปักใหม่ถึงสด
- **วิธีแก้:** เพิ่ม `MainWindow._refresh_pinned_icon(group, dir_name)` — ถ้า
  `desktop_file_name(dir_name) in pinned_desktop_ids()` → `install_launcher(group, store, dir_name)` ใหม่
  (รีเจน `Icon=`/`Name=`) แล้ว `reload_grouped_window_applet()` (ผ่าน gdbus, คืน False ถ้าไม่มี applet = ปลอดภัย)
  เรียกจาก `_persist` **ระหว่างพุ่ม save กับ `self.refresh()`** — โค้ด 21 บรรทัด
- หมายเหตุ: ยังไม่แตะกรณี **rename กลุ่มที่ปักอยู่** (ปักชี้ .desktop ตัวเก่า → ยังต้องถอน/ปักเอง; จดไว้ใน feedback
  เป็นงานแพลง + ควรทำ re-pin อัตโนมัติด้วยตอนถึงเฟสนั้น)
- เทสต์: `tests/test_gui_smoke.py` +2 ได้แก่
  - `test_refresh_pinned_icon_regenerates_launcher` — ตั้ง `XDG_DATA_HOME=tmp` → import ไอค่อนใหม่ (png→svg)
    + mock `pinned_desktop_ids`={'taskbargroups-group.desktop'} + mock `reload_grouped_window_applet` →
    ตรวจ `Icon=<พาธใหม่>` ใน .desktop จริง + reload ถูกเรียก 1 ครั้ง
  - `test_refresh_pinned_icon_skips_when_not_pinned` — ไม่ปัก → reload ไม่ถูกเรียก
  - (แพตเทิร์น mock เดียวกับ `test_main_window_marks_pinned_rows` เดิม)
- ชุดเทสต์: **182 ผ่าน** (180 → +2) · `compileall` ผ่าน
- repackage: **เก็บรวมตอนจบ Phase 16 (16d)** — เพราะผู้ใช้ขอ UI ยิบย่อย (U1–U3) เพิ่มต่อทันที แพ็กครั้งเดียวจบ

## 2026-10-11 — Phase 16c: UI ยิบย่อย (U1 เฟือง · U2 สีธีม-aware · U3 ตาเปิด/ปิด) `[เสร็จ]`

- **U3 — ไอค่อนสถานะเป็น "ตา":** `gui/main_window.py` `GroupListWidget._paint_pin_shape` เขียนใหม่
  - **ตาเปิด** = ปัก/โชว์อยู่ (อัลมอนด์เค้าโครง + รูม่านตา) · **ตามิด** = ซ่อน (ขีดเปลือกตาส่วนโค้ง)
  - ยังวาดเองด้วย QPainter (ไม่พึ่งไฟล์ธีม) · ชื่อ method/สัญญาณคงเดิม (`_paint_pin_shape`/`pinClicked`/`pin_rect`)
    เพื่อไม่กระทบเทสต์เดิม
- **U2 — สี theme-aware:** `_status_color(pinned)` เลือกสีจาก `QPalette.Base` (พื้นหลังลิสต์):
  - พื้นสว่าง → **เทาเข้ม (82,82,92)** · พื้นมืด → **ขาว (255,255,255)** · ตอนไม่ปักหรี่ alpha 150
  - **ไม่ใช้ `Highlight` แล้ว** → ไม่กลืนกับแถวที่ถูกเลือก (highlight น้ำเงิน) ทั้งธีมสว่าง/มืด
- **U1 — ปุ่มเฟือง Setup:** `font.setPixelSize(20)` + `setFixedWidth(40 → 48)` (ใหญ่ขึ้นตามที่ขอ)
- **i18n tooltip:** `main.pinned_tip` = "กำลังแสดงบนทาสก์บาร์" / "shown on the taskbar" ·
  `main.not_pinned_tip` = "ซ่อนจากทาสก์บาร์" / "hidden from the taskbar" (th/en) — สอดคล้องคำพูดกับไอค่อนตา
- เทสต์: `tests/test_gui_smoke.py` +2:
  - `test_status_color_is_theme_aware` (พื้นดำ→ขาว alpha 255 · พื้นขาว→เทาเข้ม · ไม่ปัก alpha 150)
  - `test_status_icon_paints_both_states` (เรนเดอร์ตาเปิด+ปิดไม่ crash)
  - ตรวจเชิงพิกเซลเพิ่ม (ad-hoc): ตาเปิด center สว่าง+มีม่านตา · ตามิด center มืด = ถูกต้อง
- **ชุดเทสต์: 184 ผ่าน** (182 → +2) · `compileall` ผ่าน

## 2026-10-11 — Phase 16d: Repackage (รวม 16a–16c) `[เสร็จ]`

- rebuild `dist/TaskbarGroups-x86_64.AppImage` (61M) + `dist/taskbargroups_0.1.0_amd64.deb` (51M) — 01:57
- **ตรวจยืนยัน:** boot `--list` = exit 0 (กลุ่ม Tool/Game/Production) · `dist/config` intact
- **ตรวจ PYZ (แกะจาก .deb ผ่าน `CArchiveReader`/`ZlibArchiveReader`):** มี `_refresh_pinned_icon` + `_status_color`
  (ตา) + `drawEllipse`/`QPen` + สตริง tooltip ใหม่ th/en ("กำลังแสดงบนทาสก์บาร์" / "shown on the taskbar") ครบ
- เทสต์: **184 ผ่าน** (ไม่ได้รันใหม่ — โค้ดไม่เปลี่ยนหลัง build)

## สรุป Phase 16 (N1 + UI ยิบย่อย U1–U3)
ผู้ใช้ทดสอบต่อได้เลยค่ะ · เหลือ **Phase 17** (คลิกขวา/hotkey ข้างชื่อ/ค้นหา/duplicate) · **P18** (import/export ชุด config)

## 2026-10-11 — Phase 16e (โค้ด): U4 เฟือง 28px + U5 ตั้งไอค่อนแอป `[โค้ดเสร็จ รอ build]`

- **U4:** `main_window.py` ปุ่ม Setup: `font.setPixelSize(20 → 28)` · `setFixedWidth(48 → 52)`
- **U5 (สาเหตุเฟืองบน Taskbar):** โค้ดตั้ง `setApplicationName` แต่ไม่เคยตั้ง **`setDesktopFileName`** และ **window icon**
  → Cinnamon หา .desktop ไม่เจอ → ใช้ไอค่อน fallback (เฟือง)
- **แก้:**
  - `core/paths.py`: เพิ่ม `APP_ICON_NAME` + `app_icon_path()` (หา `sys._MEIPASS/taskbargroups/assets/` →
    `app_dir()/packaging/appimage/` → `app_dir()/`) ทั้งโหมด bundle/AppImage/ซอร์ส
  - `gui/main_window.py` `run()`: `app.setDesktopFileName("taskbargroups")` + `app.setWindowIcon(QIcon(app_icon_path()))`
  - `packaging/build_appimage.sh` + `build_deb.sh`: เพิ่ม `--add-data "<png>:taskbargroups/assets"` ให้ png ติดไปกับแพ็กเกจ
- เทสต์: `tests/test_paths.py` +2 (`app_icon_path` โหมดซอร์ส + `_MEIPASS` มาก่อน) → **186 ผ่าน**
- **ยังไม่ repackage** — รวมใน build รอบ rebrand (ชื่อแอป + ไอค่อนใหม่) เพื่อไม่ให้ build ซ้ำ

## 2026-10-11 — Phase 16e + P19 Rebrand: build "TaskbarNoob" `[เสร็จ]`

**Rebrand (ชื่อที่แสดงอย่างเดียว — ไม่แตะ APP_ID):**
- `core/i18n.py`: `app.title` th/en "TaskbarGroups"/"Taskbar Groups" → **"TaskbarNoob"**
- `gui/main_window.py` `run()`: `setApplicationName("TaskbarNoob")` + `setApplicationDisplayName("TaskbarNoob")`
  · คง `setDesktopFileName("taskbargroups")` (ต้องตรงชื่อไฟล์ `.desktop`)
- `packaging/appimage/taskbargroups.desktop`: `Name=TaskbarNoob` · `StartupWMClass=TaskbarNoob` · เพิ่ม keyword `taskbar`
  · `Icon=taskbargroups` (ชื่อไฟล์ไอคอน = APP_ID คงเดิม) · `Exec=taskbargroups` เดิม
- `packaging/appimage/taskbargroups.appdata.xml`: `<name>TaskbarNoob</name>` + คำอธิบาย
- `packaging/build_deb.sh` control: Maintainer/Description = TaskbarNoob
- **คง `APP_ID="taskbargroups"`** → พินเดิม/`config` เดิมไม่พัง (ย้าย id จริงเป็นงานอนาคตถ้าจำเป็น)

- **ไอค่อนใหม่จาก `Logo TG.svg`** (ผู้ใช้ออกแบบ · วงกลมฟ้า #29abe2 + ตัวอักษรขาว · viewBox 1000×1000):
  - `packaging/render_icon.py` (ใหม่): เรนเดอร์ SVG→PNG ด้วย `QSvgRenderer` (ไม่ต้องมี rsvg/inkscape)
  - `packaging/appimage/taskbargroups.svg` (คัดลอกจาก `Logo TG.svg`) + `taskbargroups.png` (256, โปร่งใส)
  - `build_appimage.sh` + `build_deb.sh`: ถ้ามี `.svg` → rasterize ทุกครั้ง (reproducible) · ไม่มี → `make_icon.py` fallback
  - AppImage เปลี่ยนชื่อ output เป็น **`TaskbarNoob-x86_64.AppImage`**
- เทสต์: `test_i18n.py` ปรับ expected `app.title` → "TaskbarNoob" · **186 ผ่าน**

## 2026-10-11 — Phase 16e + P19: Repackage (AppImage + .deb) `[เสร็จ]`

- `dist/TaskbarNoob-x86_64.AppImage` (61M, 04:02) + `dist/taskbargroups_0.1.0_amd64.deb` (51M, 04:03)
- ลบ artifact เก่า `TaskbarGroups-x86_64.AppImage`
- **ตรวจยืนยัน:**
  - boot `--list` = exit 0 (Tool/Game/Production) · `dist/config` intact (ไม่แตะ)
  - md5 ของ `assets/taskbargroups.png` = hicolor png = โลโก้ใหม่ (ตรงกัน)
  - `.deb` desktop: `Name=TaskbarNoob` · `StartupWMClass=TaskbarNoob` · `Icon=taskbargroups`
  - PYZ (แกะจาก bundle): `i18n` มี "TaskbarNoob" · `paths` มี `app_icon_path`/`APP_ICON_NAME` ·
    `main_window` มี `setWindowIcon`/`setDesktopFileName`
- **ให้ผู้ใช้ทดสอบ:** ไอค่อนแอปเปลี่ยน (ไม่ใช่เฟือง) · ชื่อ "TaskbarNoob" · เฟือง 28px · ฟีเจอร์เดิมครบ

## 2026-10-11 — Phase 17a + 17d: Context menu + Duplicate `[โค้ดเสร็จ รอ build]`

- **ตัดสินใจรอบนี้:** P17c (ค้นหา/กรอง) ❌ ตัดออก (ผู้ใช้: คนใช้มีกลุ่มไม่ถึง ~10 อยากให้ Taskbar สะอาด) ·
  เพิ่ม **P17f Credits "Noob & Pickle"** (ผู้ใช้ตัดสิน: วางทั้ง Settings + About + appdata)
- **17a Context menu** (`gui/main_window.py`):
  - `GroupListWidget.contextMenuEvent` → เลือกไอเทมใต้เมาส์ + `emit contextMenuRequested(globalPos)`
  - `MainWindow._on_context_menu` → `_group_context_menu(dir_name)` สร้าง `QMenu` (เปิด/แก้ไข/ปัก-ถอน/ตั้ง hotkey/ทำสำเนา/ลบ)
    · ป้ายปัก/ถอนสลับตาม `pinned_desktop_ids()` · `menu.exec(pos)` แล้ว `deleteLater()`
  - i18n `ctx.*` (th/en): open/edit/pin/unpin/set_hotkey/duplicate/delete/copy_suffix
- **17d Duplicate** (`core/storage.py`): `ConfigStore.duplicate_group(dir_name, new_name=None)`
  = `shutil.copytree` ทั้งโฟลเดอร์ (รวมไอคอน) → ตั้ง `group.name` เป็นชื่อโฟลเดอร์ใหม่ →
  ต่อท้าย `order.json` · กันชื่อชนอัตโนมัติ (`name 2`, `name 3`) · rollback ถ้า save ไม่ได้
  · `MainWindow.on_duplicate` ใช้ `tr("ctx.copy_suffix", name=...)`
- **เทสต์ +7 → 193 ผ่าน:** storage 3 (คัดลอก+order, missing, unique) · gui 4 (เมนูมี 6 แอ็กชัน,
  คลิกขวา emit, คลิกที่ว่างไม่ emit, duplicate เพิ่มแถว)
- **เพิ่ม `tests/run.py`:** รันเทสต์แล้ว `os._exit()` เลี่ยง segfault ตอนปิดโปรเซสของ PySide6 6.12
  (`destroyQCoreApplication()` — บั๊กฝั่ง Qt) · `python -m unittest discover` ยังได้ผลเทสต์เท่ากันแต่ปิดโปรเซสไม่สวย
- **ยังไม่ build** — รวมกับ P17b/P17f แล้วค่อย repackage ทีเดียว

## 2026-10-11 — Fix: ไอค่อน Taskbar หายหลัง reboot (Game/Production) `[โค้ดเสร็จ รอ build]`

- **อาการ:** หลัง reboot ไอคอนกลุ่ม Game + Production บน panel หาย (Tool ปกติ)
- **สาเหตุ:** launcher `.desktop` ตั้ง `Icon=<path สัมบูรณ์>` ชี้ไฟล์บน **`/mnt/Backup`** (NTFS USB, `nofail`)
  แต่ Cinnamon panel เริ่มทำงานก่อนไดรฟ์จะ mount → resolve ไอคอนไม่ได้ → ช่องว่าง
- **แก้:** ติดตั้งไอคอนกลุ่มเข้า **user icon theme** (`~/.local/share/icons/hicolor/{scalable,256x256}/apps/<desktop-id>`)
  แล้วตั้ง `Icon=<launcher_id>` (ชื่อธีม ไม่มี path) — อยู่บนดิสก์รากเสมอ หาเจอได้ทุก boot
  - `core/desktop.py`: เพิ่ม `data_home()` · `icons_home()` · `launcher_id()` · `install_launcher_icon()` ·
    `remove_launcher_icon()` · `build_desktop_entry(..., icon_name=)` · `install_launcher(..., icons_root=)` ·
    `remove_launcher` ลบไอคอนด้วย · แก้บั๊ก `import sys` ที่หายไป (ใช้ใน `build_exec` frozen)
  - `gui/main_window.py`: `_sync_pinned_launchers()` (เรียกใน `__init__`) — launcher ที่ปักไว้แต่ยัง `Icon=<path>` เก่า
    → รีเจนเข้า theme + `ReloadXlet` ครั้งเดียว (self-heal เปิดแอปครั้งถัดไป)
- เทสต์ +6 → **201 ผ่าน** (`test_desktop`: theme icon svg/png, fallback, remove · `test_gui_smoke`: heal + skip)

## 2026-10-11 — Phase 17b + 17f: hotkey ข้างชื่อ + Credits `[โค้ดเสร็จ รอ build]`

- **17b hotkey ข้างชื่อ** (`core/hotkeys.py` + `gui/main_window.py`):
  - `hotkey_slot(dir_name)` (ย้าย logic จาก `HotkeyDialog`), `binding_get_command`, `parse_binding`,
    `get_binding`, `group_hotkeys(slots)` (คืน {} ถ้าไม่ใช่ Cinnamon — กัน subprocess) · `cinnamon_to_display("<Control><Alt>t") → "Ctrl+Alt+T"`
  - `MainWindow.refresh` ต่อท้ายชื่อกลุ่มด้วย `tr("main.hotkey_inline", keys=...)` เมื่อกลุ่มนั้นมี binding ลงทะเบียน
  - `hotkey_dialog._slot` เรียก `hotkeys.hotkey_slot` ให้ตรงกัน
- **P17f Credits "Noob & Pickle":**
  - `gui/about_dialog.py` (ใหม่): โลโก้ + ชื่อ + เวอร์ชัน (`taskbargroups.__version__`) + tagline + เครดิต
  - ปุ่มเฟือง → `QMenu` (ตั้งค่า / เกี่ยวกับ) · `MainWindow.open_settings` / `open_about`
  - `settings_dialog.py`: ป้ายเครดิตท้ายหน้า
  - `taskbargroups.appdata.xml`: `<developer><name>Noob &amp; Pickle</name>`
  - i18n: `menu.*` · `about.*` · `settings.credits` · `main.hotkey_inline`
- เทสต์ +7 → **208 ผ่าน** (hotkeys: slot/parse/display/group · gui: about credits + hotkey inline)

## 2026-10-11 — P17e: Repackage (รวม 17a/b/d/f) + fix ไอค่อน reboot `[เสร็จ]`

- `dist/TaskbarNoob-x86_64.AppImage` (61M, 11:09) + `dist/taskbargroups_0.1.0_amd64.deb` (51M, 11:09)
- **ตรวจยืนยัน:**
  - boot `--list` = exit 0 (Tool/Game/Production) · `dist/config` intact (mtime เดิม ไม่ถูกแตะ)
  - PYZ-00.pyz มีโมดูล `taskbargroups.gui.about_dialog` + symbol ใหม่ครบ:
    `_sync_pinned_launchers`/`open_about`/`open_settings` · `hotkey_slot`/`cinnamon_to_display`/`group_hotkeys`/`binding_get_command` ·
    `install_launcher_icon`/`remove_launcher_icon`/`launcher_id`/`icons_home` · i18n มี "Noob & Pickle"
  - AppImage `.desktop`: `Name=TaskbarNoob` · `Icon=taskbargroups` · `StartupWMClass=TaskbarNoob`
  - `.deb` appdata: `<developer id="io.github.neafong"><name>Noob &amp; Pickle</name></developer>`
- **ให้ผู้ใช้ทดสอบ:** ไอค่อนกลุ่มบน Taskbar ไม่หายหลัง reboot · คีย์ลัดโชว์ข้างชื่อกลุ่ม · เมนูเฟืองมี Settings + About (เครดิต Noob & Pickle)

## 2026-10-11 — Fix hotkey "ไม่มี schema" + ทดสอบ install launcher จริง `[เสร็จ]`

- **รากบั๊ก (เจอจริงบน Cinnamon 6.6.9):** `core/hotkeys.py` ใช้ schema ผิด **พหูพจน์**
  `org.cinnamon.desktop.keybindings.custom-keybindings` → ไม่มี schema → ตอนกดติดตั้งขึ้น "ไม่มี schema"
  - ตรวจจาก `/usr/share/glib-2.0/schemas/org.cinnamon.desktop.keybindings.gschema.xml` +
    `/usr/share/cinnamon/cinnamon-settings/bin/KeybindingTable.py`: schema จริง = **`…custom-keybinding` (เอกพจน์)**
  - **จับได้อีกบั๊ก:** key `binding` เป็นชนิด **`as` (array of strings)** ไม่ใช่ string → ต้อง set `['<Control><Alt>g']`
- **แก้:** `CINNAMON_CUSTOM` → เอกพจน์ · เพิ่ม `set_binding_command` (set เป็น array) · `register_cinnamon_hotkey` ใช้ร่วมกัน ·
  `parse_binding` อ่านค่า array ได้ (เดิมอ่านแต่ string) · `on_set_hotkey` → `self.refresh()` ให้คีย์โชว์ทันที
- **ทดสอบจริงกับ gsettings จริง:** register → get → `cinnamon_to_display` = `Ctrl+Alt+G` → `group_hotkeys` คืนค่า → ล้าง slot แล้ว
  · ล้าง orphan `taskbargroups-game` ที่ค้างใน `custom-list` จากรอบที่ bug
- **ทดสอบ `install_launcher` จริง:** สร้าง `.desktop` 3 กลุ่มที่ `~/.local/share/applications/`
  (`Icon=taskbargroups-{tool,game,production}` · `Exec=<AppImage> --open …` · `Path=<dist>`) +
  ติดตั้งไอคอนที่ `~/.local/share/icons/hicolor/scalable/apps/` → **GTK `lookup_icon` เจอทั้ง 3** → `ReloadXlet` แล้ว
  (self-heal ทำงานจริงบนเครื่องผู้ใช้ ไม่ต้อง reboot)
- เทสต์ +2 → **210 ผ่าน** (`set_binding_command` array · `parse_binding` array)

### ต่อ — fix `command` GVariant (เจอตอนผู้ใช้กดติดตั้งจริง) `[เสร็จ]`

- **อาการ:** กดติดตั้งคีย์ลัดขึ้น `expected end of input: "/…/AppImage" --open "Game"` → binding ไม่ถูกตั้ง
  → กดคีย์ไม่ทำงาน + คีย์ไม่โชว์ข้างชื่อกลุ่ม
- **รากบั๊ก:** `gsettings set <path> command <value>` ตีความ VALUE เป็น GVariant literal
  ถ้า value ขึ้นต้นด้วย `"` มันจะอ่านเป็น quoted string แล้วเจอส่วนที่เหลือ → error
- **แก้:** เพิ่ม `_escape_gvariant_string`/`_format_gvariant_string` (ห่อ `'…'` + escape `\` และ `'`)
  · `set_key_command` ใช้ห่อค่า (จำเป็นกับ `name`/`command` ที่มีช่องว่าง/เครื่องหมายคำพูด) ·
  `_format_gvariant_string_array` ก็ escape ด้วย
- **ทดสอบจริง:** register (name "My Group" + command มี quotes/ช่องว่าง + binding array) → อ่านกลับครบ
  (`command` = `"/mnt/x/App.AppImage" --open "Game"` · display `Ctrl+Shift+G` · `group_hotkeys` คืนค่า) → cleanup
- เทสต์ +2 → **212 ผ่าน** (quoting + escaping) · rebuild AppImage (61M) + `.deb` (51M) 11:54

### ต่อ — fix hotkey "กดไม่ทำงาน" + เพิ่มถอนคีย์ลัด `[เสร็จ]`

- **อาการ:** คีย์ลัดโชว์ข้างชื่อกลุ่มแล้ว (register สำเร็จ) แต่**กดแล้วไม่ทำงาน**
- **รากบั๊ก:** Cinnamon (`js/ui/keybindings.js`) rebuild custom keybindings **เฉพาะเมื่อ key `custom-list` เปลี่ยน**
  (`changed::custom-list`) · โค้ดเดิม**เพิ่ม slot ลง custom-list ก่อน** แล้วค่อย set name/command/binding →
  ตอน Cinnamon rebuild ยังอ่านค่าไม่ได้ (หรือ slot มีอยู่แล้ว = list ไม่เปลี่ยน = ไม่ rebuild เลย) → binding ไม่ถูกผูก
  - ต้นแบบอ้างอิง `KeybindingTable.py writeSettings()`: set `name`/`command`/`binding` **ก่อน** แล้วค่อย**แตะ list**
    ด้วย `ensureCustomListChanges` (สลับ dummy `__dummy__` เข้า/ออกเพื่อบังคับให้ยิง change)
- **แก้ (`core/hotkeys.py`):** เพิ่ม `_DUMMY`/`_clean_list`/`_touch_custom_list` (set `[base, dummy]` แล้ว `base`) ·
  `register_cinnamon_hotkey` = set ค่าก่อน → แตะ list ทีหลัง · `unregister_cinnamon_hotkey` เพิ่ม `reset_key_command`
  (ล้าง name/command/binding) + แตะ list
- **ฟีเจอร์ใหม่ (ผู้ใช้ขอ):** ปุ่ม **"ถอนคีย์ลัด"** ใน `HotkeyDialog` (โหลด binding เดิมมาโชว์ · ปุ่ม disable ถ้ายังไม่มี) ·
  ลบคีย์อัตโนมัติเมื่อ**ลบกลุ่ม** (`MainWindow.on_delete`) · i18n `hotkey.remove`/`hotkey.remove_success`
- **ทดสอบจริงกับ gsettings:** register Game → list `['taskbargroups-game']` (ไม่มี dummy) · register+unregister `tbtest3`
  → list กลับมา `['taskbargroups-game']` · binding ของ tbtest3 reset เป็น `@as []` · **Game เปิดใช้จริงแล้ว** (กด Ctrl+Shift+G ได้)
- เทสต์ +1 → **213 ผ่าน** · rebuild AppImage (61M) + `.deb` (51M) 12:08

### ต่อ — fix "ถอนคีย์ลัดแล้วยังกดได้" (ถอนไม่จริง) `[เสร็จ]`

- **อาการ:** กด "ถอนคีย์ลัด" แล้ว แต่คีย์เดิม**ยังเปิดกลุ่มได้อยู่**
- **รากบั๊ก:** Cinnamon (`js/ui/keybindings.js remove_custom_keybindings`) ลบ keybinding จริงเฉพาะชื่อที่มีคำว่า
  **"custom"** (`name.indexOf("custom") > -1`) แต่ slot ของเรา = `taskbargroups-*` → **ไม่ถูกลบ**
  การถอดออกจาก `custom-list` อย่างเดียวจึงไม่ปลดคีย์จริง
- **พิสูจน์สด:** ยิง JS ผ่าน DBus `org.Cinnamon.Eval` อ่าน `imports.ui.main.keybindingManager.bindings` เจอ
  `taskbargroups-game`/`-tool`/`-production`/`tbtest3` ค้างอยู่ใน Muffin ทั้งที่ถอดจาก list แล้ว
- **แก้ (`core/hotkeys.py`):** `unregister_cinnamon_hotkey` ทำ 2 จังหวะ — (1) set `binding=[]` **ขณะที่ slot ยังอยู่ใน list**
  แล้ว "แตะ" list → Cinnamon เรียก `addHotKeyArray(name, [])` → `global.display.remove_keybinding()` จริง
  (2) reset name/command/binding + ถอดจาก list + แตะ · เพิ่ม `set_bindings_command` รองรับ array ว่าง
- **ทดสอบ live กับ Cinnamon จริง:** register `tbtest4` → `Eval` เห็นชื่อ → unregister → หายไปจริง ✅ ·
  ล้าง binding ค้าง 4 รายการ (game/tool/production/tbtest4) → `Eval` เหลือ `[]` ✅ · คืน Game (Ctrl+Shift+G) ให้ใช้ต่อ ✅
- **213 เทสต์ผ่าน** · rebuild AppImage (61M) + `.deb` (51M) 12:44

### ต่อ — เอาปุ่มซ้ำออกจากเฟืองตั้งค่า `[เสร็จ]`

- **ผู้ใช้ชี้:** ปุ่ม "ติดตั้ง launcher" + "ตั้ง hotkey" ในเฟือง ⚙ ไปสั่งกับ **กลุ่มที่เลือกอยู่ (ดีฟอลต์ = ตัวบนสุด)**
  → สับสน และซ้ำกับเมนูคลิกขวาต่อกลุ่ม
- **แก้:** ตัด 2 ปุ่มออกจาก `SettingsDialog` (+ handler `_on_install_launcher`/`_on_set_hotkey`)
  → ใช้เมนูคลิกขวาต่อกลุ่มแทน (ชัดเจนกว่า ไม่กำกวม)
- **213 เทสต์ผ่าน** · rebuild AppImage (61M) + `.deb` (51M) 12:47

## รอบ #10 — UI/แบรนด์ + ตัด open-all + build (2026-10-11) `[เสร็จ]`

> ผู้ใช้ยืนยันหลัง reboot ผ่านหมด (B2/B3/hotkey/ตา toggle) · สั่งงาน UI เพิ่ม · มติตัด open-all

- **A1 About (TH):** `about.credits_note` → **"ไอเดีย/ดีไซน์: นู๊บ · โค้ด: น้องพริก · แจกฟรี ทำด้วยใจ"**
  (บรรทัด `about.credits` **คงเดิม** "สร้างโดย Noob & Pickle" · `settings.credits` คงเดิม) · `core/i18n.py`
- **A2 Donate:** ปุ่ม **"สนับสนุน ☕"** ในหน้าต่าง About → `QDesktopServices.openUrl` ไป **Ko-fi `ko-fi.com/neafong`**
  · เก็บเป็น `Settings.get_donate_url()` + `DEFAULT_DONATE_URL` (`core/settings.py`) · ลิงก์ว่าง = ซ่อนปุ่ม ·
  `AboutDialog(donate_url=...)` override ได้ · i18n `about.donate`/`about.donate_tip`
- **E1 Alignment:** ย้าย label "ชื่อกลุ่ม" เข้า**คอลัมน์ label ของ `QFormLayout`** (`group_editor.py`)
  → ช่องชื่อกลุ่มชิดซ้ายตรงกับ สีพื้นหลัง/ความโปร่งใส/ขนาดไอคอน (เดิม label อยู่ในคอลัมน์ field → ไม่ตรง)
- **E2 ปุ่มมีไอคอน:** ปุ่ม เพิ่ม/แก้ไข/ลบ ใช้ **ไอคอนธีมระบบ** (`QIcon.fromTheme`: `list-add` · `document-edit` ·
  `edit-delete`) · ถ้าธีมไม่มีไอคอน → **fallback เป็นอีโมจิ ➕/📝/🗑️** (`_theme_icon`/`_apply_button_icon`)
- **ตัด open-all:** เอาออกทั้ง checkbox (`group_editor`) + ปุ่ม/Ctrl+Enter (`flyout`) + i18n
  (`editor.open_all`/`flyout.open_all*`) · **คง field `allow_open_all`** ใน `models.py`/`importer.py` (import compat) ·
  `launcher.launch_all` ยังอยู่ · อัปเดตเทสต์ `test_flyout_has_no_open_all_button`
- **มติอื่น ๆ (จดใน `docs/feedback.md` รอบ #10):** คลิกขวา shortcut ใน flyout = พักรอฟีดแบ็ก ·
  ดับเบิลคลิกว่างใน flyout = ตัด · **Phase 18 (import/export zip) = งานหิน ทำหลังสุด**
- **เทสต์ +2 → 215 ผ่าน** (donate settings + about button) · **build ✅ 18:26:**
  `dist/TaskbarNoob-x86_64.AppImage` (61M) + `dist/taskbargroups_0.1.0_amd64.deb` (51M) ·
  boot `--list` OK (Tool/Game/Production) · `dist/config` intact

### ต่อ — Slim bundle (ลดขนาดแพ็กเกจ) `[เสร็จ]`

- **ผู้ใช้ถาม:** แอปเล็กแต่ไฟล์ใหญ่ — คลีนได้ไหม
- **สำรวจ:** bundle = 173M (uncompressed) · ตัวกินหนัก = Qt (PySide6 121M) — `libicudata` 31M (ลบไม่ได้),
  แล้วมี QML/Quick/Pdf/VirtualKeyboard ที่ **แอปไม่ใช้เลย**
- **เพิ่ม `packaging/slim_bundle.sh`** (เรียกใน `build_appimage.sh` + `build_deb.sh` หลัง PyInstaller) ตัด:
  - libs: `libQt6Quick*`/`Qml*`/`Pdf*`/`VirtualKeyboard*`/`EglFS*`
  - plugins: `platforms` (linuxfb/vkkhrdisplay/vnc/eglfs/minimalegl) · `egldeviceintegrations` ·
    `generic/libqevdev*` · `tls/*` (แอปใช้ local socket ไม่ใช้เน็ต) · `imageformats` (tiff/webp/tga/wbmp/icns/pdf)
  - `translations`: เก็บเฉพาะ `*_th.qm`
  - **คงไว้:** xcb/minimal/offscreen/wayland platforms · svg/ico/jpeg/gif imageformats · qgtk3 (native dialogs)
- **ผลลัพธ์:** AppImage **61M → 51M** · .deb **51M → 43M** (ลด ~16%) · boot `--list` OK ·
  GUI start (offscreen) OK · `dist/config` intact · build 18:42

## รอบ #11 — Settings UX: config path + สลับภาษาทันที (2026-10-11) `[เสร็จ]`

> ผู้ใช้ถาม 3 ข้อ: (1) ย้าย "ที่เก็บ config" ไปหน้าตั้งค่า + คลิกเปิดโฟลเดอร์ (2) ข้อความ preview ภาษาควรเปลี่ยนตามที่เลือก (2.1) สลับภาษาให้เปลี่ยนทันทีไม่ต้องปิดเปิดแอป

- **ย้าย config path:** เอา header label `main.config_dir` ออกจาก `main_window.py` → ย้ายเข้า `SettingsDialog`
  เป็นปุ่มแบน (`config_button`) กดแล้ว `QDesktopServices.openUrl(QUrl.fromLocalFile(...))` เปิดโฟลเดอร์ใน file manager
  (สร้างโฟลเดอร์ก่อนถ้ายังไม่มี) · i18n ใหม่ `settings.config_dir` / `settings.open_config_dir` · ลบ `main.config_dir`
- **สลับภาษาทันที (live switch):** เดิมใช้ `tr()` ตอนสร้าง widget ครั้งเดียว + บอกให้เปิดแอปใหม่
  → เปลี่ยนเป็น `_on_language_changed` เรียก `i18n.setup(code, config_dir)` แล้ว retranslate ทั้งคู่:
  `SettingsDialog._retranslate()` (title/theme items/labels/ปุ่ม/credits) + `MainWindow.retranslate()`
  (title + ปุ่ม nav + tooltip เฟือง + `refresh()`) · ลบ restart note (`settings.lang_restart_note`) ·
  ปรับข้อความ `settings.import_ok` (นำเข้าแล้วเลือกจากช่องด้านบน = apply ทันที)
- **เทสต์ +3 → 218 ผ่าน** (`test_language_change_applies_immediately` · `test_config_button_shows_config_dir` ·
  `test_main_window_retranslate_switches_language`)
- **build ✅ 19:22:** `dist/TaskbarNoob-x86_64.AppImage` (**51M**) + `dist/taskbargroups_0.1.0_amd64.deb` (**43M**) ·
  boot `--list` OK (Tool/Game/Production) · `dist/config` intact

## รอบ #12 — ปรับคำ (tagline/ธีม) ให้ตรงพฤติกรรมจริง (2026-10-11) `[เสร็จ]`

> หลังตัด open-all คำโปรย "เปิดทั้งกลุ่มด้วยคลิกเดียว" ไม่จริงแล้ว · ผู้ใช้เสนอ tagline สัมผัสเอง

- **tagline ใหม่:** TH `about.tagline` = **"รวบรวมทางลัด เรื่อง shortcut เราช่วยจัด"** (สัมผัส ลัด–คัท–จัด)
  · EN = "Gather your shortcuts, we do the rest"
- **ป้ายธีม:** ตัด "(ทั้งแอป)" → TH `settings.theme` = "ธีม" · EN = "Theme"
- **เก็บตกคำเก่าที่ค้าง:** `appdata.xml` (summary + description) · `taskbargroups.desktop` (Comment) ·
  docstring `__init__.py` · CLI description `__main__.py` → เลิกใช้คำ "เปิดทั้งกลุ่มด้วยคลิกเดียว"
- ไม่เพิ่มลิงก์แบรนด์ใน About (ผู้ใช้เลือกเก็บแค่ Ko-fi) · เทสต์ **218 ผ่าน**
- **build ✅:** AppImage **51M** + `.deb` **43M**

## รอบ #13 — เก็บบั๊ก cleanup: ลบ/เปลี่ยนชื่อกลุ่มที่ปัก + ชื่อซ้ำ (2026-10-11) `[เสร็จ]`

> ผู้ใช้ขอให้เช็คก่อนเริ่มเฟสใหม่ → เจอบั๊กจริง 3 จุดในเส้นทาง pin/rename

- **ข้อ 1 — ลบกลุ่มที่ปักอยู่ ทิ้งของค้าง:** `on_delete` ถอน hotkey แล้ว แต่ไม่ unpin/ลบ launcher
  → เพิ่ม `_cleanup_launcher()` (ถอนหมุดถ้าปัก + `remove_launcher()` ลบ `.desktop`+ไอคอน hicolor) เรียกหลังลบ
- **ข้อ 2 — เปลี่ยนชื่อกลุ่มที่ปักอยู่ หมุดหลุด:** dir id ผูกกับชื่อ → เปลี่ยนชื่อ = โฟลเดอร์ใหม่ แต่ pin เก่าค้าง
  → `_persist` จับ `was_pinned` แล้ว `_cleanup_launcher(old)` + `_install_and_pin(new)` (ย้ายหมุดตามชื่อใหม่)
- **ข้อ 2.5 — ชื่อกลุ่มซ้ำ = เขียนทับกันเงียบ ๆ (data loss):** `safe_dir_name(name)` ชนกัน → เพิ่ม `_unique_group_name()`
  เติม ` 2`, ` 3`, ... อัตโนมัติ + เด้งกล่องบอก (`main.name_taken_*`) — มติผู้ใช้ = เติมเลขให้อัตโนมัติ
- **เทสต์ +3 → 221 ผ่าน** (`test_delete_pinned_group_removes_launcher_and_unpins` ·
  `test_rename_pinned_group_migrates_launcher` · `test_duplicate_group_name_gets_suffix`)
- **build ✅:** AppImage + `.deb`

## รอบ #14 — Pre-v1 hardening: ตรวจ checklist ก่อน Phase 18 (2026-10-11) `[เสร็จ]`

> ไหน ๆ แกะโค้ดแล้ว จัดข้อค้างก่อนเริ่มเฟสใหม่

- **ข้อ 4 (quit) — ผ่าน:** รัน GUI จริง (offscreen) แล้วปิด → `app.exec()` คืน 0 · process exit code **0**
  ไม่ segfault (ที่เจอในเทสต์เป็นเฉพาะ destroy ตอน `unittest discover` เท่านั้น)
- **ข้อ 3 (first-run/read-only) — ผ่าน:** AppImage + `TASKBARGROUPS_CONFIG` ว่าง → `--list` เปล่า exit 0 ·
  GUI เปิดได้ไม่พัง · fallback/portable มี unit test ครบแล้ว (`test_paths.py`)
- **ข้อ 7 (XML import safety) — แก้:** `importer._parse` ปฏิเสธไฟล์ที่มี `<!DOCTYPE`/`<!ENTITY`
  (กัน billion-laughs / XML entity attack) ไม่ต้องพึ่ง lib ใหม่ · เทสต์ `test_doctype_rejected`
- **ข้อ 9 (เก็บกวาด) — แก้:** ลบ constants ซ้ำใน `paths.py` + ใช้ `APPIMAGE_ENV_VAR` ให้ตรง
- **เทสต์ +2 → 223 ผ่าน** (`test_doctype_rejected` · `test_main_window_first_run_empty`)
- **ยังไม่ทดสอบได้บนเครื่องนี้ (known limitation):** Wayland · จอหลายจอ · panel ย้ายด้าน · DE อื่น (GNOME/KDE)
  → hotkey/pin เป็น Cinnamon-only
- **build ✅:** AppImage + `.deb`

## Pre-Phase 18 — วางแผนจัดระเบียบ (2026-10-11) `[แผนพร้อม]`

> ผู้ใช้ขอ: วางโครงงานให้ระบบก่อน แล้ค่อยเริ่ม Phase 18 ในเซคชั่นใหม่ (ประหยัด token)

- เขียนแผนเต็มที่ `docs/phase18-plan.md`: โครง zip · API `core/archive.py` (export/inspect/import) ·
  กฎ merge (unique ` (N)`) vs replace (backup `config.bak-*`) · ความปลอดภัย (zip-slip guard · whitelist ·
  dry-run ก่อนเขียน · กัน import ตัวเอง) · เทสต์ ~12 ข้อ · i18n keys · ลำดับงาน · วิธีตรวจ
- เหลือ **1 จุดรอผู้ใช้เคาะ**: รูปแบบ dialog ยืนยัน import (เสนอเป็น 3 ปุ่ม merge/replace/ยกเลิก)
- AGENTS.md ชี้แผน + "เริ่มงานชุดใหญ่ในเซคชั่นใหม่" เป็นข้อบังคับแล้ว
- **ผู้ใช้เคาะ UI import แล้ว (2026-10-11):** 3 ปุ่ม merge/replace/ยกเลิก → แผนทุกหัวข้อตัดสินครบ ไม่ต้องถามซ้ำ
  → เซคชั่นใหม่เริ่ม Phase 18 ได้ทันที (อ่าน AGENTS.md + `docs/phase18-plan.md` แล้วลงมือเองต่อ)

## 2026-10-11 — Phase 18: Import/Export ทั้งชุด config (zip) `[เสร็จ]`

> เฟสสุดท้ายในแผน — สำรอง/กู้คืนทั้งชุดเป็น `.zip` (ตาม `docs/phase18-plan.md` ทุกข้อ)
> ทำในเซคชั่นใหม่ เปิดด้วยอ่าน AGENTS.md + แผนก่อนลงมือ

- **`core/storage.py` — แชร์ logic ชื่อซ้ำ:** เพิ่ม `ConfigStore.unique_group_name(desired, old_dir=None, use_parens=True)`
  รองรับทั้ง ` (2)` (importer/archive) และ ` 2` (GUI เดิม) → ย้าย `_unique_group_name` ของ `importer.py`
  และ `gui/main_window.py` มาเรียกตัวนี้ (ลบโค้ดซ้ำ)
- **`core/archive.py` (ใหม่ · Python ล้วน):**
  - `export_config(config_dir, target)` — zip `groups/` + `order.json` + `settings.json` + `lang/` (เฉพาะที่มี), `ZIP_DEFLATED`
  - `inspect_zip(path) -> ZipReport` (groups/settings/lang/size) · `import_config(path, config_dir, mode) -> ImportReport`
  - mode `merge`: ชื่อชนเติม ` (2)` · order ต่อท้าย · settings/lang ไม่แตะ
  - mode `replace`: สำรอง `config.bak-<ts>` ก่อน แล้ววางทับทั้งชุด (`backup_dir` ใน report)
  - ความปลอดภัย: zip-slip guard (`..`/absolute/backslash) · whitelist top-level · cek ขนาด `MAX_ZIP_BYTES` ·
    dry-run validate `group.json` ทุกกลุ่มใน staging ก่อนเขียน · ไฟล์แปลก = ข้าม · zip ที่ไม่ใช่ของเรา = error
  - ลบ temp staging เสมอ (`finally`) + `.bak` กันชื่อชนด้วย suffix
- **GUI `SettingsDialog`:** เพิ่มปุ่ม **"ส่งออกทั้งหมด…"** / **"นำเข้าทั้งหมด…"** (แถวถัดจากปุ่มภาษา) +
  handler ครบ (save/open dialog · import มี 3 ปุ่ม merge/replace/ยกเลิก · replace ถามยืนยันซ้ำ) ·
  อยู่ใน `_retranslate()` แล้ว · import เสร็จเรียก `main_window.refresh()`
- **i18n:** เพิ่มคีย์ TH/EN `settings.export_all*` · `settings.import_all*` · `settings.import_confirm_*` ·
  `settings.import_summary*` · `settings.import_backup_note` · `settings.cancel` · `err.archive_*` (147 คีย์เท่ากันทั้งสองภาษา)
- **เทสต์ `tests/test_archive.py` +11 (234) + settings dialog +1 (235 ผ่าน):** export มี members ครบ ·
  roundtrip replace · merge เติม ` (2)` · merge ไม่แตะ settings · replace สร้าง backup ·
  zip-slip reject · non-whitelist ข้าม · group.json เสีย reject · ใหญ่เกิน reject · ไม่ใช่ zip reject ·
  zip ไม่ใช่ config ของเรา reject · ปุ่มใน dialog + retranslate
- **ทดสอบกับ config จริง (สำเนา):** export `dist/config` → zip (375KB) · replace ลง dest ใหม่ = เท่าเดิม ·
  merge ลงที่มี `Tool` อยู่ = ได้ `Tool (2)` ครบ
- **build ✅:** AppImage + `.deb` (ดู AGENTS.md)

## 2026-10-11 — รอบ #16: ภาษาตัวอย่าง (asset) สำหรับทดสอบ i18n `[เสร็จ]`

> ฟีดแบ็กจากผู้ใช้: ทดสอบส่งออกทั้งหมด → ลบกลุ่มหมด → นำเข้าทั้งหมด **ใช้ได้** · เรื่องภาษา
> ไม่รู้จะทดสอบยังไงเพราะมีแค่ TH/EN → มติ: ทำภาษาที่ 3 แบบ **asset** ให้ผู้ใช้ติดตั้งเอง โดยเราทำตัวอย่างไว้ทดสอบของเรา

- **`packaging/lang/ja.json` (ใหม่):** ภาษา **ญี่ปุ่น** แปลครบทุกข้อความ (147 คีย์ = TH ทุกคีย์) +
  `_lang_name: "日本語"` (key พิเศษสำหรับชื่อแสดงใน dropdown) — เป็นต้นแบบที่ผู้ใช้รายอื่นโหลดไป import
  ผ่านปุ่ม "นำเข้าภาษา…" ได้เลย
- วางสำเนาไว้ที่ `dist/config/lang/ja.json` → dropdown Settings แสดง `日本語` เทสต์สลับภาษาได้ทันที (3 ภาษา)
- **`core/i18n.py`:** `available_languages()` อ่านชื่อแสดงจาก key `_lang_name` ในไฟล์ (fallback = code) ·
  จัดการไฟล์ JSON เสียได้ · `_lang_display_name()` helper ใหม่
- **`gui/settings_dialog.py`:** หลังนำเข้าภาษา ถ้า code ใหม่ ใช้ชื่อแสดงถูกต้อง (อ่านจาก `available_languages`)
- **เทสต์:** +3 (display name / fallback เมื่อ JSON เสีย / parity ของ asset ja กับ TH) → **238 ผ่าน**
- **build ✅:** AppImage + `.deb` (ตรวจ `--list` boot ผ่าน)

## 2026-10-11 — รอบ #17: ปุ่ม "ลบสำรองเก่า" + เตรียมขึ้น GitHub `[เสร็จ]`

> ฟีดแบ็กผู้ใช้: ทดสอบ Import แล้วเหลือ `config.bak-*` (สำรองจากการ replace) ค้างเป็นขยะ
> → เพิ่มทางลบให้ · พร้อมเก็บงานก่อนเผยแพร่บน GitHub

- **`core/archive.py`:** เพิ่ม `list_backups(config_dir)` (หา `config.bak-*` เรียงล่าสุดก่อน) +
  `delete_backups(config_dir, backups)` — ยอมลบเฉพาะโฟลเดอร์สำรองใน parent เดียวกับ config (กันลบพลาด)
- **GUI `SettingsDialog`:** ปุ่ม **"ลบสำรองเก่า…"** ต่อจาก export/import all → ยืนยันพร้อมรายละเอียด
  (จำนวน + ขนาดรวม + รายชื่อ) → ลบ + แจ้งผล · `_dir_size` helper ใหม่ · เข้า `_retranslate()`
- **i18n:** คีย์ TH/EN `settings.delete_backups*` + `err.backup_delete_failed` · อัปเดต `packaging/lang/ja.json` ครบ
- **เทสต์:** +2 (list/delete backups) + ขยายเทสต์ dialog → **240 ผ่าน**
- **build ✅:** AppImage + `.deb`

### เก็บงานก่อนขึ้น GitHub (2026-10-12) `[เสร็จ]`
- ย้าย `Logo TG.svg` + `Logo TG.vectorcraft` → `packaging/assets/` (รวม asset แบรนด์)
- ลบ `dist/config.bak-*` ที่ค้าง (ใช้ `archive.delete_backups`) → ไม่มีขยะเหลือ
- `.gitignore`: เพิ่ม `*.AppImage` / `*.deb` / `*.zip` กัน binary หลุดเข้า repo (build artifacts ควรอยู่ที่ GitHub Releases)
- ร่าง `README.md` (ไทย + อังกฤษ): ฟีเจอร์ · ดาวน์โหลด/ติดตั้ง (AppImage/.deb) · รันจากซอร์ส · build · เทสต์ · วิธีเพิ่มภาษา · เครดิต/โดเนท
- **ยังรอผู้ใช้เคาะ LICENSE** (ยังไม่สร้างไฟล์ `LICENSE`)

### License เคาะแล้ว (2026-10-12) `[เสร็จ]`
- ผู้ใช้เคาะ **GPL-3.0** (เหตุผล: อยากให้ทุกคนใช้ฟรี + ใครเอาไปต่อยอด/ขายต้องเปิดโค้ด → ขายไม่คุ้ม)
- สร้าง `LICENSE` = ข้อความ GPL-3.0 มาตรฐาน (คัดจาก `/usr/share/common-licenses/GPL-3`, 674 บรรทัด)
- เติมหัวข้อ License ใน `README.md`: GPL-3.0-or-later · Copyright (C) 2026 Noob & Pickle · SPDX + โน้ต Qt = LGPLv3 แยกต่างหาก

## 2026-10-12 — ขึ้น GitHub: push + Release v0.1.0 + badge + สกรีนช็อต `[เสร็จ]`

### Publish ขึ้น GitHub
- commit แรก `ebfe189` · branch `main` · tag `v0.1.0`
- ตั้ง SSH key (ed25519) → remote = `git@github.com:Neafong/TaskbarNoob.git`
- `git push -u origin main` + `git push origin v0.1.0` → repo **public**
- **GitHub Release `v0.1.0`** แนบ `TaskbarNoob-x86_64.AppImage` (50 MB) + `taskbargroups_0.1.0_amd64.deb` (42 MB)
  · release notes ไทย · ไม่ใช่ draft/pre-release · topics ที่ใส่: linux · mint · cinnamon · taskbar · pyside6 · shortcuts

### README polish
- commit `cb48325`: badge (release / downloads / license / platform) + ปุ่ม Download latest release
- ส่วน **ตัวอย่างหน้าจอ / Screenshots** — รูปใน `docs/screenshots/`
  (`all-ui.jpg` ภาพรวม · `main-window.png` หน้าหลัก · `edit-group.png` แก้ไขกลุ่ม)

## 2026-10-12 — จัดระเบียบเอกสาร (เฟส A–B ของระบบการเขียนแผน) `[กําลังทำ]`

> คำขอ: แยกไฟล์แผน/อัปเดตให้เป็นระเบียบ อย่าให้บวมที่ไฟล์เดียว + แบ่งงานเป็นเฟส กันโทเคนหมดกลางทาง

- **A ✅** `docs/README.md` = แผนที่เอกสาร (ดัชนี + หลักการ 1 ไฟล์ = 1 หน้าที่ + ลำดับเฟส A→G)
- **B ✅** `docs/roadmap.md` = แผนภาพรวมทุกเฟส (ย้าย checklist P0–P18 มา + งานถัดไป + แผน Windows W0–W5)
  · ย่อ `AGENTS.md` จาก 179 → ~120 บรรทัด (ตัดประวัติรอบ #10–#17 → ชี้ไป WORKLOG · คงหมายเหตุเทคนิคสำคัญไว้ครบ)
- **C ✅** `docs/release-process.md` = ขั้นตอนออกรุ่น/อัปเดต (SemVer แหล่งเดียวที่ `__init__.py` · bump→CHANGELOG→build→tag→Release · release vs ปกติ)
- **D ✅** `CHANGELOG.md` = ประวัติเวอร์ชันแบบ Keep a Changelog (Unreleased + v0.1.0 ครบ: Added/Fixed/Removed/Packaging + link compare)
- **E ✅** `.github/` = CI (`workflows/tests.yml` — apt deps Qt + xvfb + `tests/run.py`) · **รอบแรกผ่าน (success) ทุกสเต็ป (run 38195536365)** ·
  ได้ badge `tests` เข้า README · `FUNDING.yml` (Ko-fi → ปุ่ม Sponsor อัตโนมัติ) · `ISSUE_TEMPLATE/` (bug + feature) · `PULL_REQUEST_TEMPLATE.md`
- **ต่อไป F:** `docs/windows-plan.md` → G: `CONTRIBUTING.md`

## 2026-10-12 — รอบ #18: ไอเดีย "กระเป๋าใส่ได้ทุกอย่าง" + ทิศทาง Windows `[จดแทน — ยังไม่ทำ]`

> ผู้ใช้เสนอฟีเจอร์: ลากไฟล์/โฟลเดอร์อะไรก็ได้เข้ากลุ่ม → shortcut เปิดด้วยโปรแกรม Default ("กระเป๋า 1 ใบ").
> ตอบ: **F7 (ลากเพิ่ม shortcut) ทำแล้ว** — เหลือแค่ "เปิดด้วย default" ฝั่ง Linux (ตอนนี้ `Popen([target])` เปิดไฟล์ไม่ได้ ต้อง `gio open`)
> → เก็บเป็นตัวเก็ง **v0.2** · ผู้ใช้ตกลงทางนี้
>
> ทิศทาง Windows: **เขียน Linux ให้จบก่อน** · Windows = พร้อมรุ่นถัดไป **หลังรวมฟีดแบ็กครบ** → จดลง `docs/roadmap.md` + `docs/feedback.md` รอบ #18

## 2026-10-12 — เฟส G: `CONTRIBUTING.md` (ปิดชุดระบบเอกสาร A→G) `[เสร็จ]`

- **G ✅** `CONTRIBUTING.md` (root) = วิธีร่วมพัฒนา: เริ่มอ่านอะไรก่อน · รายงานบั๊ก/เสนอฟีเจอร์ (ชี้ Issue template) ·
  เซตอัป dev (venv + `tests/run.py`) · กติกาโค้ด (สถาปัตยกรรม `core/` ห้าม Qt · type hints · i18n parity `ja.json` ·
  ไม่อัป binary/config เข้า repo · ห้าม secret) · แนวทาง PR (template + commit message + อัปเดต WORKLOG/feedback/AGENTS) ·
  จุดที่เทสต์ยาก (Cinnamon-only · Wayland/จอหลายจอ/DE อื่น) · ลิงก์สนับสนุน Ko-fi
- อัปเดต `docs/README.md`: ย้าย `CONTRIBUTING.md` เข้าตาราง "เอกสารที่มีอยู่" · มาร์กเฟส **G ✅**
- **สถานะชุดเอกสาร:** A–E ✅ + G ✅ ครบ · เหลือ **F `docs/windows-plan.md`** — เลื่อนไว้ทำตอนจริงจังเรื่อง Windows (ผู้ใช้เคาะ "ทำ Linux ให้จบก่อน")

## 2026-10-13 — v0.2-B: UI polish (B1, B4–B7) `[เสร็จส่วนง่าย]

- **B1 — เคอร์เซอร์ลากกลุ่ม (หน้าหลัก + ShortcutGrid):** `startDrag` ครอบ `QApplication.setOverrideCursor(Qt.SizeAllCursor)` → เคอร์เซอร์ลูกศร 4 ทิศ · `dragEnter/dragMove` accept `MoveAction` สำหรับ internal drag → 🚫 หาย
- **B5 — padding QMenu:** `_style_menu()` (padding 6px 4px, item 8px 22px) ใช้กับ context menu กลุ่ม + setup menu เฟือง
- **B6 — credits+ปุ่มปิดแถวเดียวใน Settings:** `QHBoxLayout` แถวล่าง (credits ชิดซ้าย + stretch + ปิดชิดขวา) แทน 2 แถวเดิม
- **B7 — ปุ่ม config path:** ปุ่ม outline มีกรอบ + hover (`_style_config_button`) · `QPalette` · re-style ตาม theme change
- **B4 — swatch สี + ช่อง hex:** เปลี่ยนจาก `QPushButton` text เป็น `color_swatch` (32px) + `color_hex` (`QLineEdit`) · sync 2 ทาง (`_on_hex_edited/finished`, `_update_color_ui`) · `_normalize_hex` ย่อ `#rgb→#rrggbb` · รองรับ `is_hex_color` · `QPalette` import · เพิ่ม 2 เทสต์ `test_gui_smoke.py` → **223 ผ่าน** (จาก 221 เพิ่ม 2) · i18n `editor.hex_tip` (TH/EN) + parity `ja.json`

**หมายเหตุ:** งด B2 (accent token+ไฮไลท์โปร่งแสง) และ B3 (ชุด SVG+theme tint) ตามคำขอ "งานง่ายทำก่อนงานยากทำทีหลัง" — จดไว้ใน `feedback.md`/`WORKLOG` เพื่อทำต่อได้.

## 2026-10-13 — v0.2-B: B3 SVG icons + theme tint (ชั่วคราวกำลังทำ) `[สำเร็จแล้ว]
- เพิ่มชุด SVG Phosphor Icons (fill): plus/pencil/trash/check/x/gear/eye/eye-slash/push-pin ลง `packaging/assets/icons/`
- `gui/button_icons.py` ใหม่: tint SVG ด้วย `QPalette.ColorRole.Text` (SourceIn) + helper themed_icon/text_color_from_palette
- `group_editor.py`: ใช้ SVG icons แทนอีโมจิ/ธีมระบบเดิม (add/edit/delete) + import ใหม่
- `tests.run.py` → 223 ผ่านครบ

หมายเหตุ: ยังไม่แตะ main_window (ปุ่ม Setup ปัจจุบันใช้ "⚙") ตามที่พิจารณาไว้ (B3 ครอบคลุมปุ่มในตัวแก้ไขก่อน; main_window ยัง fallback ได้)

## 2026-10-13 — v0.2-B: B2 accent token + ไฮไลท์โปร่งแสง `[เสร็จ]
- `theme.py`: เปลี่ยน accent เป็น `#4a90d9` (อ่อน/ทันสมัยขึ้น) + ตั้ง `Link` ให้เข้ากับ accent
- `main_window.py`: pin hover alpha 60→45 (นุ่มขึ้น)
- `group_editor.py`: drop highlight alpha 80→50 (นุ่มขึ้น)
- `tests.run.py` → 223 ผ่านครบ

## 2026-10-13 — v0.2-C: "กระเป๋าใส่ได้ทุกอย่าง" (type-aware + คลิกขวาเปิดโฟลเดอร์แม่) `[เสร็จ]
- `core/launcher.py`: Linux ปรับให้เปิดได้ — .desktop (gio launch) · ไฟล์ที่มีอยู่ (gio open/xdg-open) · โฟลเดอร์ที่มีอยู่ (xdg-open/gio open) · executable ปกติ (เดิม)
- `gui/flyout.py`: ปุ่มแต่ละไอคอนมี context menu คลิกขวา → "เปิดที่อยู่" เฉพาะไฟล์ที่มีอยู่จริง (ไม่ใช่โฟลเดอร์) → เปิด parent ด้วย xdg-open/gio open
- i18n: เพิ่ม `flyout.reveal` (TH/EN) + `packaging/lang/ja.json`
- `tests.run.py` → 223 ผ่านครบ

## 2026-10-14 — ซ่อม UI ตามรีวิวผู้ใช้ (รอบ 7 จุด) `[เสร็จ]`
- **1.1:** `main_window.GroupListWidget` เติมไฮไลท์แถวโปร่งแสง (accent alpha 45) ตอน hover
  (`_row_hover` เก็บเป็นเลขแถวกัน dangling · `clear()` รีเซ็ต state · ของเดิมมีแค่โซนตาเลยดูเหมือนหาย)
- **1.2:** ตาปัก/ถอนใช้ SVG `eye-fill/eye-slash-fill` tint ตามธีม (`button_icons.tinted_icon_pixmap` ใหม่)
  · โค้ดวาดเส้นเดิมเหลือเป็น fallback กัน asset หาไม่เจอ
- **1.3:** ปุ่มเพิ่ม/แก้ไข/ลบ + เฟือง หน้าหลักใช้ SVG (`plus/pencil/trash/gear`) tint ตามธีม · re-apply ใน `retranslate`
- **2:** `shortcut.title` TH = "ทางลัด" · แถวไอคอนตัดคำว่า "ไอคอน" โชว์รูป 48px แทน
  (`_update_icon_preview`: manual pick → shortcut.icon → auto resolve → fallback · refresh ตอนพิมพ์ target ถ้ายังไม่เคย pick)
  · ปุ่ม OK/Cancel = ตกลง/ยกเลิก + SVG (check/x) ผ่าน helper `_style_dialog_buttons`
- **3.1:** GroupEditor OK/Cancel = ตกลง/ยกเลิก + SVG เช่นกัน
- i18n: คีย์ใหม่ `dialog.ok/cancel` (TH/EN + `ja.json` parity)
- เทสต์ 223 ผ่าน · smoke offscreen ตรวจไอคอน/ข้อความ/paintEvent ครบ

## 2026-10-14 — popup เล็กไทยล้วน + ปุ่มไม่มีไอคอน `[เสร็จ]`
- `gui/dialogs.py` ใหม่: `style_message_box` (ลบไอคอนปุ่มทุกปุ่ม + ตั้งข้อความตามภาษา)
  + `show_warning/information/critical/question` (คืนค่า exec เหมือน static เดิม)
- เปลี่ยน static `QMessageBox.*` ทั้ง 39 จุด (main/group_editor/hotkey/settings) มาใช้ helper
  · กล่อง custom ใน settings เรียก `style_message_box` ก่อน `exec`
- About: ปุ่ม Close = "ปิด" ไม่มีไอคอน · Yes/No = ใช่/ไม่ใช่ · i18n `dialog.close/yes/no` (TH/EN + `ja.json`)
- เทสต์: อัปเดต 2 mock ใน `test_gui_smoke.py` ให้ mock `show_question/show_information`
  (mock static เดิมไม่โดนเรียก → dialog จริง block ทำให้ suite hang) → 223 ผ่าน
- i18n parity: `shortcut.working_dir`="โฟลเดอร์ทำงาน" · `shortcut.arguments`="อาร์กิวเมนต์"
  · `editor.shortcut_list_hint`="รายการทางลัด" · โค้ดเลิก hardcode ใช้ `tr()` · ตรวจแล้ว EN ไม่มีภาษาไทยปน

## 2026-10-14 — แก้ไอคอนไม่รีเฟรชตอนสลับธีม (บั๊กคลิก 2 รอบ) `[เสร็จ]`
- สาเหตุ: `app.setPalette()` ส่ง PaletteChange เป็น event คิวไว้ แต่โค้ด tint ไอคอนอ่าน `widget.palette()`
  ทันที → ได้สีเก่า · ตาลูกตารอดเพราะวาดใน paintEvent (เกิดหลัง event เสมอ)
  · หลักฐาน: จังหวะสลับธีม tint ได้ #000000 ทั้งที่ app เป็น #dddddd แล้ว
- `theme.py`: เพิ่ม `app_color(role)` + `app_text_color()` อ่าน app palette ตรงๆ (ค่าจริงทันที ไม่รอ event)
- ใช้ทุกจุดที่ tint ตอน action: ปุ่มหน้าหลัก/เฟือง · ปุ่ม config (กรอบ+hover) · ปุ่มตัวแก้ไข/OK-Cancel · ขอบ swatch
  · paint-time (hover แถว/ตา/`_status_color`) คง `widget.palette()` ไว้ (สดเสมอ + มีเทสต์บังคับระดับ widget)
- `MainWindow.refresh_icons()` ใหม่ + `settings._on_theme_changed` เรียกหลัง `apply_theme`
  → สลับธีมปุ๊บไอคอนเปลี่ยนทันที ไม่ต้องสลับภาษาซ้ำ
- regression test `test_theme_switch_retints_icons_immediately` (+ลบ helper `text_color_from_palette` กันกลับมาใช้ผิด)
- เทสต์ 224 ผ่าน (223 เดิม + 1 ใหม่)

## 2026-10-14 — hover กริด + เปลี่ยน accent เป็น `#1f9ede` `[เสร็จ]`
- `ShortcutGrid` (กริดไอคอนในตัวแก้ไข): เติมไฮไลท์ช่องโปร่งแสงตอน hover (accent alpha 45 ·
  `_hover_row` เป็นเลขแถว + `setMouseTracking` + `clear()` รีเซ็ต) — แบบเดียวกับหน้าหลัก
- `theme.py`: accent `#4a90d9` → **`#1f9ede`** (ฟ้าสดตามที่ผู้ใช้ดูดสีมา) · `Link` (darker 110) กับทุกจุดที่ใช้
  `Highlight` (hover แถว/ตา/drop กริด/selection) เปลี่ยนตามอัตโนมัติเพราะอ่านจาก palette
- เทสต์ 224 ผ่าน

## 2026-10-14 — bump v0.2.0 + build AppImage `[เสร็จ]`
- `__init__.py`: `0.1.0` → **`0.2.0`** (About อ่านจากตัวนี้ — ที่ก่อนหน้าโชว์ 0.1.0)
- `CHANGELOG.md`: ย้าย `[Unreleased]` → **`[0.2.0] — 2026-10-14`** (everything-bag · UI polish ·
  accent `#1f9ede` · hover กริด · แก้ไอคอนไม่รีเฟรชตอนสลับธีม · i18n)
- ลบ `dist/` เก่า → build ใหม่ `bash packaging/build_appimage.sh` → `dist/TaskbarNoob-x86_64.AppImage` (50M)
- คัดลอกไปที่จริง: `/home/noob/AppImage/Tool/TaskbarNoob-x86_64.AppImage`
- ตรวจใน AppImage (PYZ): consts ของ `taskbargroups` = `'0.2.0'` · มี `gui.dialogs` · `--list` ออก Tool/Game/Production
- เทสต์ 224 ผ่าน · ยังไม่ commit / ยังไม่ tag

## 2026-10-15 — ย้าย dev หลัก HDD → SSD + แก้ OpenCode หาโปรเจคไม่เจอ `[เสร็จ]`
- อาการ: รายชื่อโปรเจคใน OpenCode Desktop หาย + New Project ด้วย `/home/noob/Desktop/TaskbarNoob` ไม่ได้
  · **ไม่ใช่ไวรัส** · ไฟล์อยู่ครบทั้งสองที่ · เขียน/ลบได้ปกติ · `dmesg` ไม่มี I/O error
- สาเหตุ: `/mnt/Backup` เป็น NTFS (`fuseblk`) แบบ `noauto` ยังไม่ mount ตอนเปิดแอป → log ฟ้อง
  `realPath (/mnt/Backup/TaskbarGroups) ENOENT` + `removed=["/mnt/Backup/TaskbarGroups"]`
  · สองโฟลเดอร์ remote เดียวกัน (`Neafong/TaskbarNoob`) เลยถูกนับเป็นโปรเจคเดียว
  (worktree=HDD, sandbox=SSD) → สร้าง New Project ซ้ำไม่ได้ ถูกแล้ว
- แก้: push SSD ขึ้น origin ก่อน (`v0.2-D 086c689` · เทสต์ 224 ผ่าน) · สลับ DB
  `project.worktree` → SSD แล้ว (HDD เป็น sandbox สำรอง) · แชทเก่ายังค้าง HDD ต้องเปิด **New Session** ใหม่ถึงจะได้ SSD
- ต่อจากนี้ dev หลักคือ SSD (ext4) · HDD เก็บเป็น `.bak` ไว้ก่อนลบจริง · เปิด OpenCode ต้อง mount Backup ก่อนเสมอ

## 2026-10-15 — ซ่อมแพ็กเกจไอคอน + กด shortcut ใน flyout แล้วไม่เปิด `[เสร็จ]`
- **ไอคอนปุ่มหายใน AppImage:** SVG ทั้งชุดไม่ถูก `--add-data` + โค้ดหา assets แบบ layout เก่า
  แต่ PyInstaller 6 วาง data ใต้ `_internal/` → ปุ่มเฟือง/ตาว่าง (ดูเหมือน 0.1) · ไอคอนแอป (U5) โดนด้วย
  - `core/paths.py`: helper ใหม่ `bundled_assets_dir()` (ลอง `_internal/...` ก่อนแล้วค่อยแบบเก่า) ·
    `gui/button_icons.py` ใช้ helper นี้ · สคริปต์ `build_appimage.sh`/`build_deb.sh` เพิ่ม
    `--add-data packaging/assets/icons:taskbargroups/assets/icons`
  - เทสต์ +3 (smoke: assets resolve + MEIPASS ทั้ง 2 layout · paths: `_internal` layout)
- **กด shortcut ใน flyout แล้วแอปไม่เปิด:** v0.2-C ส่งไฟล์ที่มีอยู่จริงทุกชนิดให้ `gio open`
  แต่ default app ของระบบคือ editor (สคริปต์) / disk-mounter (AppImage) / ไม่มี handler (ELF)
  - `core/launcher.py`: ไฟล์ที่มี `+x` (AppImage/ELF/สคริปต์) → รันตรง `Popen([target, *args])` แบบ 0.1 ·
    เอกสารทั่วไปค่อย `gio open` · ไม่มีไฟล์จริง (คำสั่งใน PATH) → รันตรง
  - เทสต์ `test_launcher.py` +6 (dispatch ครบทุกชนิด + LaunchError) · ตรวจรันจริงสคริปต์ +x ผ่าน
- เทสต์ **233 ผ่าน** · build AppImage ใหม่ + วาง `~/AppImage/Tool/` แล้ว (md5 ตรง `dist/`)
- ค้าง: ลบ `/mnt/Backup/TaskbarGroups/dist/` (ไฟล์เก่า 0.1.0) — ติด loop mount ต้อง reboot ก่อน (พักไว้หลัง push)
