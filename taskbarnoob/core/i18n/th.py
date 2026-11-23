"""ตารางคำแปลภาษาไทย (built-in)."""

from __future__ import annotations

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
    "ctx.open_launcher_dir": "เปิดโฟลเดอร์ launcher",
    "main.win_pinned_tip": (
        "<b>ปักอยู่บน taskbar แล้ว</b><br><br>"
        "คลิกที่ไอคอนโฟลเดอร์เพื่อเปิดโฟลเดอร์อีกครั้ง"
    ),
    "main.win_pin_label_stale": (
        "<br><br><b><font color=\"#E5484D\">⚠ ข้อจำกัด</font></b><br>"
        "ชื่อบน taskbar เปลี่ยนไม่ได้หลังลากวางแล้ว "
        "เพราะ Windows อัปเดตตอนลากวางเท่านั้น<br>"
        "หากอยากให้ตรงกับชื่อกลุ่ม ให้ถอนออกจาก taskbar แล้วลากมาใหม่"
    ),
"main.win_not_pinned_tip": (
        "<b>ยังไม่ได้ปักบน taskbar</b><br><br>"
        "คลิกที่ไอคอนโฟลเดอร์ แล้วลากไฟล์ <b>{file}</b> ไปวางบน taskbar"
        "<br>(ทำครั้งเดียวพอ หลังจากนั้นไอค่อนจะอยู่บน taskbar ถาวร)<br><br>"
        "<b><font color=\"#E5484D\">💡 คำแนะนำ:</font></b> ตั้งชื่อกลุ่มให้ถูกก่อนลากวาง "
        "จะได้ชื่อตรงบน taskbar โดยไม่ต้องลากใหม่"
    ),
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
    "system_icon.source_system": "ไอคอนระบบ Windows (imageres / shell32)",
    "system_icon.source_apps": "แอปใน Start Menu",
    "system_icon.linux_categories": "หมวดหมู่และโฟลเดอร์",
    "system_icon.linux_apps": "แอปที่ติดตั้ง",
    "system_icon.linux_all": "ไอคอนทั้งหมด",
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
    "editor.show_labels": "แสดงชื่อใต้ไอคอน",
    "editor.show_labels_tip": "โชว์ชื่อไฟล์/แอปใต้ไอคอนใน flyout (มีผลกับกลุ่มนี้)",
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
    "settings.flyout_labels": "ค่าเริ่มต้น: แสดงชื่อใต้ไอคอนใน flyout",
    "settings.flyout_labels_tip": (
        "ใช้กับกลุ่มที่ไม่ได้ตั้งค่าไว้เอง · ปรับรายกลุ่มได้ในหน้าแก้ไขกลุ่ม"
    ),
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
    "hotkey.focus_scale": "ขนาดไอคอนโหมดโฟกัส",
    "hotkey.focus_scale_tip": (
        "ตัวคูณขนาดไอคอนตอนกด hotkey (โหมดโฟกัสกลางจอ) · "
        "กลุ่มที่มีไอคอนเยอะอาจต้องลดลงเพื่อให้พอดีจอ"
    ),
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
    "about.credits": "สร้างโดย Noob & Jenny",
    "about.credits_note": "ไอเดีย/ดีไซน์: นู๊บ · โค้ด: เจนนี่ · แจกฟรี ทำด้วยใจ",
    "about.donate": "สนับสนุน ☕",
    "about.donate_tip": "เปิดหน้า Ko-fi เพื่อสนับสนุนผู้พัฒนา",
    "about.close": "ปิด",
    "settings.credits": "Made by Noob & Jenny",
}
