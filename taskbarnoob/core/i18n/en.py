"""English translation table (built-in)."""

from __future__ import annotations

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
    "ctx.open_launcher_dir": "Open launcher folder",
    "main.win_pinned_tip": (
        "<b>Already on the taskbar</b><br><br>"
        "Click the folder icon to open the folder again"
    ),
    "main.win_pin_label_stale": (
        "<br><br><b><font color=\"#E5484D\">⚠ Limitation</font></b><br>"
        "The taskbar label cannot change after you drag the file, "
        "because Windows only updates it at that moment.<br>"
        "To match the group name, unpin it and drag it again."
    ),
    "main.win_not_pinned_tip": (
        "<b>Not on the taskbar yet</b><br><br>"
        "Click the folder icon, then drag <b>{file}</b> onto the taskbar"
        "<br>(only needed once — the icon stays there afterwards)<br><br>"
        "<b><font color=\"#E5484D\">💡 Tip:</font></b> name the group before "
        "dragging so the taskbar label matches it from the start."
    ),
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
    "system_icon.source_system": "Windows system icons (imageres / shell32)",
    "system_icon.source_apps": "Start Menu apps",
    "system_icon.linux_categories": "Categories & Folders",
    "system_icon.linux_apps": "Installed apps",
    "system_icon.linux_all": "All icons",
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
    "editor.show_labels": "Show names under icons",
    "editor.show_labels_tip": "Show file/app names under flyout icons (this group only)",
    "editor.pick_icon": "Choose icon...",
    "editor.pick_icon_tip": "Pick an image file as the group icon",
    "editor.choose_system": "From system...",
    "editor.choose_system_tip": "Pick an icon from the system icon theme",
    "editor.group_icon": "Group icon",
    "editor.shortcut_list_hint": "Shortcuts (drop files here · drag to reorder)",
    "editor.add": "Add",
    "editor.add_from_apps": "From apps...",
    "editor.add_from_apps_tip": "Pick from installed apps",
    "editor.redetect_icon": "Re-detect icon",
    "editor.broken_target_tip": "Target file not found (may have been moved or deleted)",
    "shortcut.target_missing_hint": "⚠ Target file or command not found",
    "app_picker.title": "Pick an installed app",
    "app_picker.search_placeholder": "Type an app name to search (e.g. firefox, zen)...",
    "app_picker.count": "{n} apps",
    "editor.pick_color": "Pick color",
    "editor.hex_tip": "Type or paste a #RRGGBB color code",
    "editor.pick_icon_dialog": "Pick group icon",
    "settings.title": "Settings",
    "settings.theme": "Theme",
    "settings.theme_auto": "Follow system (auto)",
    "settings.theme_light": "Light",
    "settings.theme_dark": "Dark",
    "settings.theme_hint": (
        "Choose 'Follow system' to match your system theme.\n"
        "Note: this does not change icons on the Taskbar."
    ),
    "settings.language": "Language",
    "settings.flyout_labels": "Default: show names under flyout icons",
    "settings.flyout_labels_tip": (
        "Applies to groups that don't set their own value · set per group in the editor"
    ),
    "settings.minimize_to_tray": "Minimize to System Tray when closing",
    "settings.minimize_to_tray_tip": (
        "Closing the window hides it to the system tray instead of quitting "
        "(keeps global hotkeys active in the background)"
    ),
    "tray.open": "Open TaskbarNoob",
    "tray.settings": "Settings...",
    "tray.quit": "Quit",
    "tray.tooltip": "TaskbarNoob — Click to open main window",
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
    "hotkey.focus_scale": "Focus-mode icon size",
    "hotkey.focus_scale_tip": (
        "Icon size multiplier when opened by hotkey (centered focus mode) · "
        "groups with many icons may need a lower value to fit"
    ),
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
    "about.credits": "Made by Noob & Jenny",
    "about.credits_note": "Design & ideas by Noob · Code by Jenny · Free, made with love",
    "about.donate": "Support me ☕",
    "about.donate_tip": "Open the Ko-fi page to support the developer",
    "about.close": "Close",
    "menu.settings": "Settings",
    "menu.about": "About TaskbarNoob",
    "settings.credits": "Made by Noob & Jenny",
}
