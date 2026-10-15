"""i18n: ภาษาไทย (ค่าเริ่มต้น) + อังกฤษ + ภาษาของผู้ใช้เองผ่าน config/lang/<lang>.json.

- ภาษาในตัว: TH / EN (อยู่ในโค้ดนี้)
- ผู้ใช้เพิ่มภาษาเองได้โดยวางไฟล์ JSON ไว้ใน `<config>/lang/<code>.json`
- key เดียวกันทั้งหมด → ภาษาไทยคือภาษาแม่ (fallback ของทุกภาษา)
"""

from __future__ import annotations

import json
from pathlib import Path

from .paths import default_config_dir

DEFAULT_LANGUAGE = "th"
LANG_DIR_NAME = "lang"

TH = {
    # แอป / หน้าต่างหลัก
    "app.title": "TaskbarNoob",
    "main.add_group": "เพิ่มกลุ่ม",
    "main.edit": "แก้ไข",
    "main.delete": "ลบ",
    "main.setup_tooltip": "ตั้งค่าแอป (ธีม / launcher / hotkey)",
    "main.pinned_tip": "กำลังแสดงบนทาสก์บาร์",
    "main.not_pinned_tip": "ซ่อนจากทาสก์บาร์",
    "main.hotkey_inline": "  ·  คีย์: {keys}",
    "ctx.open": "เปิดกลุ่ม",
    "ctx.edit": "แก้ไข",
    "ctx.pin": "ปักหมุดบนทาสก์บาร์",
    "ctx.unpin": "ถอนหมุดจากทาสก์บาร์",
    "ctx.set_hotkey": "ตั้งปุ่มลัด (Hotkey)",
    "ctx.duplicate": "ทำสำเนากลุ่ม",
    "ctx.delete": "ลบกลุ่ม",
    "ctx.copy_suffix": "{name} (สำเนา)",
    "flyout.reveal": "เปิดที่อยู่",
    "main.confirm_delete_title": "ยืนยันการลบ",
    "main.confirm_delete_body": "ลบกลุ่ม '{dir_name}' ใช่ไหม?",
    "main.name_taken_title": "ชื่อซ้ำ",
    "main.name_taken_body": "มีกลุ่มชื่อ '{name}' อยู่แล้ว ใช้ชื่อ '{new_name}' แทนนะคะ",
    "main.launcher_installed": "ติดตั้ง launcher แล้ว:\n{path}",
    "main.pin_fallback": (
        "ปักหมุดอัตโนมัติไม่ได้ ({exc})\n"
        "ลากไอคอนกลุ่มจากเมนู Applications ไปวางบน panel เองได้เลยค่ะ"
    ),
    "main.pin_ok": (
        "ปักหมุดขึ้น panel แล้วค่ะ\n"
        "(ไอคอนอาจโผล่ใน 1-2 วินาที ถ้าไม่เห็นค่อยรีสตาร์ท Cinnamon)"
    ),
    "main.pin_title": "ปักหมุดขึ้น Taskbar",
    "main.unpin_failed": "ถอนหมุดไม่สำเร็จ",
    "main.unpin_ok": "ถอนหมุดออกจาก panel แล้วค่ะ",
    "main.unpin_not_found": "ไม่พบการปักหมุดของกลุ่มนี้บน panel",
    "main.unpin_title": "ถอนหมุด",
    "main.launcher_installed_title": "ติดตั้ง launcher แล้ว",
    "main.launcher_installed_body": (
        "สร้างไฟล์:\n{path}\n\nตอนนี้หากลุ่มได้ในเมนู Applications แล้วค่ะ"
    ),
    # ข้อความทั่วไป
    "err.generic": "ผิดพลาด",
    "err.invalid_data": "ข้อมูลไม่ถูกต้อง",
    # ปุ่ม dialog มาตรฐาน
    "dialog.ok": "ตกลง",
    "dialog.cancel": "ยกเลิก",
    "dialog.close": "ปิด",
    "dialog.yes": "ใช่",
    "dialog.no": "ไม่ใช่",
    # แก้ไข shortcut (ShortcutDialog)
    "shortcut.title": "ทางลัด",
    "shortcut.display_name": "ชื่อที่แสดง",
    "shortcut.browse": "เลือก...",
    "shortcut.target": "โปรแกรม/ไฟล์",
    "shortcut.working_dir": "โฟลเดอร์ทำงาน",
    "shortcut.arguments": "อาร์กิวเมนต์",
    "shortcut.pick_file": "เลือกไฟล์...",
    "shortcut.auto_icon": "ดึงจากโปรแกรม",
    "shortcut.icon": "ไอคอน",
    "shortcut.auto_placeholder": "(อัตโนมัติ)",
    "shortcut.pick_target_dialog": "เลือกโปรแกรม/ไฟล์",
    "shortcut.pick_cwd_dialog": "เลือกโฟลเดอร์ทำงาน",
    "shortcut.pick_icon_dialog": "เลือกไฟล์ไอคอน",
    "shortcut.no_icon_title": "ไม่พบไอคอน",
    "shortcut.no_icon_body": (
        "หาไอคอนอัตโนมัติไม่ได้ค่ะ "
        "ลองเลือกไฟล์เอง หรือใช้ target ที่เป็น .desktop/ไฟล์รูป"
    ),
    "shortcut.missing_target": "ต้องระบุโปรแกรม/ไฟล์ (target)",
    # เลือกไอคอนจากระบบ
    "system_icon.title": "เลือกไอคอนจากระบบ",
    "system_icon.search_placeholder": "พิมพ์ชื่อไอคอนเพื่อค้นหา (เช่น firefox)...",
    "system_icon.choose": "เลือก",
    "system_icon.count": "{n} ไอคอน",
    "system_icon.count_capped": "แสดง {n} ไอคอน — พิมพ์เพื่อค้นหาเพิ่ม",
    # แก้ไขกลุ่ม (GroupEditor)
    "editor.edit_title": "แก้ไขกลุ่ม",
    "editor.new_title": "เพิ่มกลุ่มใหม่",
    "editor.group_name": "ชื่อกลุ่ม",
    "editor.cols": "แถว",
    "editor.bg_dark": "เข้ม (dark)",
    "editor.bg_light": "สว่าง (light)",
    "editor.bg_custom": "กำหนดเอง (custom)",
    "editor.bg_color": "สีพื้นหลัง",
    "editor.opacity": "ความโปร่งใส",
    "editor.icon_size": "ขนาดไอคอน",
    "editor.pick_icon": "เลือกไอคอน...",
    "editor.pick_icon_tip": "เลือกไฟล์รูปภาพเป็นไอคอนกลุ่ม",
    "editor.choose_system": "เลือกจากระบบ...",
    "editor.choose_system_tip": "เลือกไอคอนจากชุดธีมของระบบ",
    "editor.group_icon": "ไอคอนกลุ่ม",
    "editor.shortcut_list_hint": "รายการทางลัด (ลากไฟล์มาวางได้ · ลากสลับลำดับได้)",
    "editor.add": "เพิ่ม",
    "editor.pick_color": "เลือกสี",
    "editor.hex_tip": "พิมพ์/วางรหัสสี #RRGGBB ได้เลย",
    "editor.pick_icon_dialog": "เลือกไอคอนกลุ่ม",
    # ตั้งค่า
    "settings.title": "ตั้งค่า",
    "settings.theme": "ธีม",
    "settings.theme_auto": "ตามระบบ (auto)",
    "settings.theme_light": "สว่าง (light)",
    "settings.theme_dark": "เข้ม (dark)",
    "settings.theme_hint": (
        "เลือก 'ตามระบบ' เพื่อเข้ม/สว่างตามธีม Cinnamon เอง\n"
        "หมายเหตุ: ธีมนี้ไม่เปลี่ยนไอคอน/ปุ่มบน Taskbar"
    ),
    "settings.language": "ภาษา / Language",
    "settings.config_dir": "ที่เก็บ config",
    "settings.open_config_dir": "เปิดโฟลเดอร์ config ในตัวจัดการไฟล์",
    "settings.install_launcher": "ติดตั้ง launcher",
    "settings.install_launcher_tip": "สร้าง launcher ของกลุ่มที่เลือกในเมนู Applications",
    "settings.set_hotkey": "ตั้ง hotkey",
    "settings.set_hotkey_tip": "ตั้งคีย์ลัดเปิดกลุ่มที่เลือก",
    "settings.export_lang": "ส่งออกภาษา...",
    "settings.export_lang_tip": "บันทึกสตริงภาษาปัจจุบันเป็นไฟล์ JSON (ไว้แปล)",
    "settings.import_lang": "นำเข้าภาษา...",
    "settings.import_lang_tip": "โหลดภาษาใหม่จากไฟล์ JSON",
    "settings.close": "ปิด",
    "settings.cancel": "ยกเลิก",
    "settings.export_dialog_title": "บันทึกภาษาเป็น JSON",
    "settings.export_ok": "บันทึกภาษาเป็น '{path}' แล้วค่ะ",
    "settings.import_dialog_title": "เลือกไฟล์ภาษาจากไฟล์ JSON",
    "settings.import_ok": "นำเข้าภาษา '{language}' แล้ว เลือกใช้ได้จากช่องภาษาด้านบนค่ะ",
    "settings.import_invalid": "ไฟล์ภาษาไม่ถูกต้อง (ต้องเป็น JSON ที่มี key/value เป็นข้อความ)",
    "settings.export_all": "ส่งออกทั้งหมด...",
    "settings.export_all_tip": "สำรองกลุ่ม + การตั้งค่าทั้งหมดเป็นไฟล์ .zip",
    "settings.import_all": "นำเข้าทั้งหมด...",
    "settings.import_all_tip": "กู้คืน/รวมจากไฟล์สำรอง .zip",
    "settings.export_all_dialog_title": "บันทึกสำรองทั้งหมดเป็น .zip",
    "settings.export_all_ok": "ส่งออก {count} กลุ่มเป็น '{path}' แล้ว ({size})",
    "settings.export_all_none": "ยังไม่มีข้อมูลให้ส่งออกค่ะ",
    "settings.import_all_dialog_title": "เลือกไฟล์สำรอง .zip",
    "settings.import_confirm_title": "ยืนยันการนำเข้า",
    "settings.import_confirm_merge": (
        "จะนำเข้า {count} กลุ่มจากไฟล์นี้\n"
        "โหมด 'เพิ่ม': กลุ่มเดิมยังอยู่ กลุ่มที่ชื่อซ้ำจะถูกเติมเลขต่อท้าย\n"
        "การตั้งค่า/ภาษาเดิมไม่ถูกแตะ\n\nต้องการนำเข้าแบบไหนคะ?"
    ),
    "settings.import_confirm_replace": (
        "⚠️ โหมด 'แทนที่ทั้งหมด' จะล้างกลุ่มและการตั้งค่าปัจจุบัน\n"
        "ระบบจะสำรองของเดิมไว้ก่อนเสมอ\n\nยืนยันการแทนที่ทั้งหมดใช่ไหม?"
    ),
    "settings.import_merge_button": "เพิ่ม (merge)",
    "settings.import_replace_button": "แทนที่ทั้งหมด (restore)",
    "settings.import_summary": "นำเข้าสำเร็จ {count} กลุ่ม",
    "settings.import_summary_renamed": " (ชื่อซ้ำถูกเติมเลข {count} กลุ่ม)",
    "settings.import_backup_note": "\nสำรองของเดิมไว้ที่:\n{path}",
    "err.archive_invalid": "ไฟล์สำรองไม่ถูกต้องหรือไม่ใช่ .zip ค่ะ",
    "err.archive_slip": "ไฟล์สำรองมีเส้นทางไฟล์ที่ไม่ปลอดภัย — ยกเลิกเพื่อความปลอดภัย",
    "err.archive_too_big": "ไฟล์สำรองใหญ่เกินกำหนด",
    "err.archive_backup_failed": "สำรองข้อมูลเดิมไม่สำเร็จ — ยกเลิกการนำเข้า",
    # ลบสำรองเก่า
    "settings.delete_backups": "ลบสำรองเก่า…",
    "settings.delete_backups_tip": "ลบฟอล์เดอร์ `config.bak-*` ที่เหลือจากการนำเข้าแบบแทนที่",
    "settings.delete_backups_title": "ลบสำรองเก่า",
    "settings.delete_backups_none": "ไม่มีสำรองเก่าให้ลบค่ะ",
    "settings.delete_backups_confirm": "พบสำรองเก่า {n} ชุด รวม {size}\nลบทิ้งทั้งหมดใช่ไหมคะ?",
    "settings.delete_backups_done": "ลบสำรองเก่าแล้ว {n} ชุด",
    "err.backup_delete_failed": "ลบสำรองไม่สำเร็จ",
    # hotkey
    "hotkey.title": "ตั้ง hotkey — {name}",
    "hotkey.command": "คำสั่ง",
    "hotkey.keys": "คีย์ลัด",
    "hotkey.cinnamon_format": "รูปแบบ Cinnamon",
    "hotkey.empty": "(ว่าง)",
    "hotkey.note": (
        "ฟีเจอร์นี้ใช้ gsettings ของ Cinnamon เท่านั้น "
        "ถ้าใช้ desktop อื่นให้ตั้งคีย์ลัดเองใน System Settings."
    ),
    "hotkey.install": "ติดตั้ง",
    "hotkey.remove": "ถอนคีย์ลัด",
    "hotkey.remove_success": "ถอนคีย์ลัดของกลุ่ม '{name}' แล้ว",
    "hotkey.close": "ปิด",
    "hotkey.unsupported_title": "ไม่รองรับ",
    "hotkey.unsupported_body": "ฟีเจอร์นี้รองรับเฉพาะ Cinnamon ค่ะ",
    "hotkey.no_binding": "ยังไม่ได้ตั้งคีย์ลัด",
    "hotkey.success_title": "สำเร็จ",
    "hotkey.success_body": "ตั้ง hotkey {binding} ให้กลุ่ม '{name}' แล้ว",
    # เมนู + เครดิต
    "menu.settings": "ตั้งค่า",
    "menu.about": "เกี่ยวกับ TaskbarNoob",
    "about.title": "เกี่ยวกับ TaskbarNoob",
    "about.version": "เวอร์ชัน {version}",
    "about.tagline": "รวบรวมทางลัด เรื่อง shortcut เราช่วยจัด",
    "about.credits": "สร้างโดย Noob & Pickle",
    "about.credits_note": "ไอเดีย/ดีไซน์: นู๊บ · โค้ด: น้องพริก · v0.2: น้องมิวช่วยลุย · แจกฟรี ทำด้วยใจ",
    "about.donate": "สนับสนุน ☕",
    "about.donate_tip": "เปิดหน้า Ko-fi เพื่อสนับสนุนผู้พัฒนา",
    "about.close": "ปิด",
    "settings.credits": "Made by Noob & Pickle",
}

EN = {
    "app.title": "TaskbarNoob",
    "main.add_group": "Add group",
    "main.edit": "Edit",
    "main.delete": "Remove",
    "main.setup_tooltip": "App settings (theme / launcher / hotkey)",
    "main.pinned_tip": "shown on the taskbar",
    "main.not_pinned_tip": "hidden from the taskbar",
    "main.hotkey_inline": "  ·  Key: {keys}",
    "ctx.open": "Open group",
    "ctx.edit": "Edit",
    "ctx.pin": "Pin to taskbar",
    "ctx.unpin": "Unpin from taskbar",
    "ctx.set_hotkey": "Set hotkey",
    "ctx.duplicate": "Duplicate group",
    "ctx.delete": "Delete group",
    "ctx.copy_suffix": "{name} (copy)",
    "flyout.reveal": "Open location",
    "main.confirm_delete_title": "Confirm delete",
    "main.confirm_delete_body": "Delete group '{dir_name}'?",
    "main.name_taken_title": "Name already used",
    "main.name_taken_body": "A group named '{name}' already exists, using '{new_name}' instead.",
    "main.launcher_installed": "Launcher installed:\n{path}",
    "main.pin_fallback": (
        "Could not pin automatically ({exc}).\n"
        "Drag the group icon from the Applications menu onto the panel instead."
    ),
    "main.pin_ok": (
        "Pinned to the panel.\n"
        "(The icon may appear within 1-2 seconds; restart Cinnamon if it does not.)"
    ),
    "main.pin_title": "Pin to Taskbar",
    "main.unpin_failed": "Unpin failed",
    "main.unpin_ok": "Unpinned from the panel.",
    "main.unpin_not_found": "This group is not pinned to the panel.",
    "main.unpin_title": "Unpin",
    "main.launcher_installed_title": "Launcher installed",
    "main.launcher_installed_body": "Created:\n{path}\n\nThe group now appears in the Applications menu.",
    "err.generic": "Error",
    "err.invalid_data": "Invalid data",
    # Standard dialog buttons
    "dialog.ok": "OK",
    "dialog.cancel": "Cancel",
    "dialog.close": "Close",
    "dialog.yes": "Yes",
    "dialog.no": "No",
    "shortcut.title": "Shortcut",
    "shortcut.display_name": "Display name",
    "shortcut.browse": "Browse...",
    "shortcut.target": "Program/File",
    "shortcut.working_dir": "Working dir",
    "shortcut.arguments": "Arguments",
    "shortcut.pick_file": "Choose file...",
    "shortcut.auto_icon": "Extract from app",
    "shortcut.icon": "Icon",
    "shortcut.auto_placeholder": "(automatic)",
    "shortcut.pick_target_dialog": "Pick program/File",
    "shortcut.pick_cwd_dialog": "Pick working folder",
    "shortcut.pick_icon_dialog": "Pick icon file",
    "shortcut.no_icon_title": "No icon found",
    "shortcut.no_icon_body": (
        "Could not find an icon automatically. "
        "Pick a file yourself, or use a .desktop/image target."
    ),
    "shortcut.missing_target": "You must set a program/file (target)",
    "system_icon.title": "Pick a system icon",
    "system_icon.search_placeholder": "Type an icon name to search (e.g. firefox)...",
    "system_icon.choose": "Choose",
    "system_icon.count": "{n} icons",
    "system_icon.count_capped": "Showing {n} icons — type to search more",
    "editor.edit_title": "Edit group",
    "editor.new_title": "New group",
    "editor.group_name": "Group name",
    "editor.cols": "Cols",
    "editor.bg_dark": "Dark",
    "editor.bg_light": "Light",
    "editor.bg_custom": "Custom",
    "editor.bg_color": "Background color",
    "editor.opacity": "Opacity",
    "editor.icon_size": "Icon size",
    "editor.pick_icon": "Choose icon...",
    "editor.pick_icon_tip": "Pick an image file as the group icon",
    "editor.choose_system": "From system...",
    "editor.choose_system_tip": "Pick an icon from the system icon theme",
    "editor.group_icon": "Group icon",
    "editor.shortcut_list_hint": "Shortcuts (drop files here · drag to reorder)",
    "editor.add": "Add",
    "editor.pick_color": "Pick color",
    "editor.hex_tip": "Type or paste a #RRGGBB color code",
    "editor.pick_icon_dialog": "Pick group icon",
    "settings.title": "Settings",
    "settings.theme": "Theme",
    "settings.theme_auto": "Follow system (auto)",
    "settings.theme_light": "Light",
    "settings.theme_dark": "Dark",
    "settings.theme_hint": (
        "Choose 'Follow system' to match your Cinnamon theme.\n"
        "Note: this does not change icons on the Taskbar."
    ),
    "settings.language": "Language",
    "settings.config_dir": "Config folder",
    "settings.open_config_dir": "Open the config folder in the file manager",
    "settings.install_launcher": "Install launcher",
    "settings.install_launcher_tip": "Create a launcher of the selected group in the Applications menu",
    "settings.set_hotkey": "Set hotkey",
    "settings.set_hotkey_tip": "Set a shortcut to open the selected group",
    "settings.export_lang": "Export language...",
    "settings.export_lang_tip": "Save current UI strings as JSON (for translating)",
    "settings.import_lang": "Import language...",
    "settings.import_lang_tip": "Load a new language from a JSON file",
    "settings.close": "Close",
    "settings.cancel": "Cancel",
    "settings.export_dialog_title": "Save language as JSON",
    "settings.export_ok": "Language saved as '{path}'.",
    "settings.import_dialog_title": "Pick a language JSON file",
    "settings.import_ok": "Language '{language}' imported. Pick it in the language dropdown above.",
    "settings.import_invalid": "Invalid language file (must be JSON with string keys/values)",
    "settings.export_all": "Export all...",
    "settings.export_all_tip": "Back up all groups + settings as a .zip file",
    "settings.import_all": "Import all...",
    "settings.import_all_tip": "Restore/merge from a .zip backup",
    "settings.export_all_dialog_title": "Save full backup as .zip",
    "settings.export_all_ok": "Exported {count} groups to '{path}' ({size}).",
    "settings.export_all_none": "There is nothing to export yet.",
    "settings.import_all_dialog_title": "Pick a .zip backup",
    "settings.import_confirm_title": "Confirm import",
    "settings.import_confirm_merge": (
        "This will import {count} groups from the file.\n"
        "'Merge': existing groups stay; name clashes get a number suffix.\n"
        "Your settings/languages are left untouched.\n\nWhich mode do you want?"
    ),
    "settings.import_confirm_replace": (
        "⚠️ 'Replace all' will wipe your current groups and settings.\n"
        "A backup of the current data is always made first.\n\nReplace everything?"
    ),
    "settings.import_merge_button": "Merge",
    "settings.import_replace_button": "Replace all (restore)",
    "settings.import_summary": "Imported {count} groups",
    "settings.import_summary_renamed": " ({count} name clashes got a number suffix)",
    "settings.import_backup_note": "\nBackup of previous data:\n{path}",
    "err.archive_invalid": "Invalid backup file (not a .zip).",
    "err.archive_slip": "Backup contains an unsafe file path — aborted for safety.",
    "err.archive_too_big": "Backup file is too large.",
    "err.archive_backup_failed": "Failed to back up existing data — import aborted.",
    "settings.delete_backups": "Clean old backups...",
    "settings.delete_backups_tip": "Remove `config.bak-*` folders left over from replace imports",
    "settings.delete_backups_title": "Clean old backups",
    "settings.delete_backups_none": "There are no old backups to clean.",
    "settings.delete_backups_confirm": "Found {n} old backup(s), {size} total.\nDelete them all?",
    "settings.delete_backups_done": "Removed {n} old backup(s).",
    "err.backup_delete_failed": "Failed to remove backups",
    "hotkey.title": "Set hotkey — {name}",
    "hotkey.command": "Command",
    "hotkey.keys": "Shortcut",
    "hotkey.cinnamon_format": "Cinnamon format",
    "hotkey.empty": "(empty)",
    "hotkey.note": (
        "This feature uses Cinnamon gsettings only. "
        "On other desktops set a shortcut in System Settings."
    ),
    "hotkey.install": "Install",
    "hotkey.remove": "Remove hotkey",
    "hotkey.remove_success": "Removed hotkey for group '{name}'.",
    "hotkey.close": "Close",
    "hotkey.unsupported_title": "Unsupported",
    "hotkey.unsupported_body": "This feature supports Cinnamon only.",
    "hotkey.no_binding": "No shortcut set",
    "hotkey.success_title": "Success",
    "hotkey.success_body": "Hotkey {binding} set for group '{name}'.",
    "about.title": "About TaskbarNoob",
    "about.version": "Version {version}",
    "about.tagline": "Gather your shortcuts, we do the rest",
    "about.credits": "Made by Noob & Pickle",
    "about.credits_note": "Design & ideas by Noob · Code by Pickle · v0.2 with Mew · Free, made with love",
    "about.donate": "Support me ☕",
    "about.donate_tip": "Open the Ko-fi page to support the developer",
    "about.close": "Close",
    "menu.settings": "Settings",
    "menu.about": "About TaskbarNoob",
    "settings.credits": "Made by Noob & Pickle",
}


class I18n:
    def __init__(
        self,
        language: str | None = None,
        config_dir: str | Path | None = None,
    ) -> None:
        self._language = language or DEFAULT_LANGUAGE
        self._config_dir = (
            Path(config_dir) if config_dir is not None else default_config_dir()
        )
        self._data = self._load()

    @property
    def language(self) -> str:
        return self._language

    def _load(self) -> dict:
        base = dict(TH)
        if self._language == "en":
            base.update(EN)
        overlay = (self.lang_dir() / f"{self._language}.json")
        if overlay.is_file():
            try:
                user = json.loads(overlay.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                user = {}
            if isinstance(user, dict):
                for key, value in user.items():
                    if isinstance(value, str):
                        base[key] = value
        return base

    def lang_dir(self) -> Path:
        return self._config_dir / LANG_DIR_NAME

    def text(self, key: str, **kwargs) -> str:
        value = self._data.get(key, key)
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return value
        return value


_active: I18n | None = None


def tr(key: str, **kwargs) -> str:
    """สตริงปัจจุบันของ key (ภาษาไทยเป็นค่าพื้นฐาน ถ้ายังไม่เรียก setup)."""
    i18n = _active or I18n(DEFAULT_LANGUAGE)
    return i18n.text(key, **kwargs)


def setup(language: str | None = None, config_dir: str | Path | None = None) -> I18n:
    global _active
    _active = I18n(language, config_dir)
    return _active


def available_languages(config_dir: str | Path | None = None) -> list[tuple[str, str]]:
    """รายการภาษา [(code, ชื่อที่แสดง), ...] — ไทย/อังกฤษ + ไฟล์ใน config/lang.

    ไฟล์ภาษาเพิ่มเติมสามารถฝังชื่อที่แสดงได้ด้วย key พิเศษ `_lang_name`
    เช่น {"_lang_name": "日本語", ...} → dropdown โชว์ "日本語"
    """
    result: list[tuple[str, str]] = [("th", "ไทย"), ("en", "English")]
    seen = {"th", "en"}
    lang_dir = I18n(config_dir=config_dir).lang_dir()
    if lang_dir.is_dir():
        for path in sorted(lang_dir.glob("*.json")):
            code = path.stem
            if code not in seen:
                result.append((code, _lang_display_name(path, code)))
                seen.add(code)
    return result


def _lang_display_name(path: Path, fallback: str) -> str:
    """อ่านชื่อแสดงจาก key `_lang_name` ในไฟล์ภาษา (ถ้ามี) ไม่งั้นใช้ code."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    name = data.get("_lang_name") if isinstance(data, dict) else None
    return str(name).strip() if isinstance(name, str) and name.strip() else fallback


def lang_dir(config_dir: str | Path | None = None) -> Path:
    return I18n(config_dir=config_dir).lang_dir()


def export_language(
    target: Path,
    language: str | None = None,
    config_dir: str | Path | None = None,
) -> None:
    """ส่งออกคู่ key/ข้อความของภาษาที่ระบุ (หรือภาษาที่ active อยู่) ลงไฟล์ JSON."""
    i18n = I18n(language or (_active.language if _active else DEFAULT_LANGUAGE), config_dir)
    data = {}
    for key in TH:
        data[key] = i18n.text(key)
    for key, value in i18n._data.items():
        if key not in data:
            data[key] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def import_language(
    source: Path,
    config_dir: str | Path | None = None,
) -> str | None:
    """นำเข้าภาษา JSON ไปไว้ที่ config/lang/<ชื่อไฟล์>.json → คืน language code."""
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        return None
    destination = lang_dir(config_dir)
    code = source.stem
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f"{code}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return code