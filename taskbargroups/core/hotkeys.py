"""ตั้ง global hotkey ผ่าน gsettings/dconf (รองรับ Cinnamon เป็นหลัก)."""

from __future__ import annotations

import ast
import os
import subprocess
from typing import Callable, Sequence

CINNAMON_BASE = "org.cinnamon.desktop.keybindings"
CINNAMON_CUSTOM = "org.cinnamon.desktop.keybindings.custom-keybinding"
CINNAMON_PATH_ROOT = "/org/cinnamon/desktop/keybindings/custom-keybindings/"

# Cinnamon rebuild custom keybindings เฉพาะเมื่อ key `custom-list` เปลี่ยนเท่านั้น
# (js/ui/keybindings.js → changed::custom-list) จึงต้อง "แตะ" list ด้วย dummy ให้ change ยิงทุกครั้ง
_DUMMY = "__dummy__"

Runner = Callable[[Sequence[str]], str]


class HotkeyError(Exception):
    """โยนเมื่อตั้ง/ลบ hotkey ไม่สำเร็จ."""


def detect_desktop() -> str:
    return os.environ.get("XDG_CURRENT_DESKTOP", "").lower()


def is_cinnamon() -> bool:
    return "cinnamon" in detect_desktop()


def _run(command: Sequence[str]) -> str:
    result = subprocess.run(list(command), capture_output=True, text=True)
    if result.returncode != 0:
        raise HotkeyError(result.stderr.strip() or f"คำสั่งล้มเหลว: {' '.join(command)}")
    return result.stdout


def parse_gvariant_string_array(raw: str) -> list[str]:
    text = raw.strip()
    if text.startswith("@as"):
        text = text[3:].strip()
    if not text or text == "[]":
        return []
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError) as exc:
        raise HotkeyError(f"อ่าน custom-list ไม่ได้: {raw!r}") from exc
    if not isinstance(value, (list, tuple)):
        raise HotkeyError(f"custom-list ไม่ใช่ list: {raw!r}")
    return [str(item) for item in value]


def _escape_gvariant_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _format_gvariant_string(value: str) -> str:
    """ห่อ string เป็น GVariant string literal (จำเป็นเมื่อมีช่องว่าง/เครื่องหมายคำพูด)."""
    return f"'{_escape_gvariant_string(value)}'"


def _format_gvariant_string_array(values: Sequence[str]) -> str:
    return "[" + ", ".join(_format_gvariant_string(value) for value in values) + "]"


def list_command() -> list[str]:
    return ["gsettings", "get", CINNAMON_BASE, "custom-list"]


def binding_get_command(slot: str) -> list[str]:
    path = f"{CINNAMON_CUSTOM}:{CINNAMON_PATH_ROOT}{slot}/"
    return ["gsettings", "get", path, "binding"]


def hotkey_slot(dir_name: str) -> str:
    """ชื่อ slot ใน custom-keybindings ของกลุ่ม (ใช้ร่วมกับ HotkeyDialog)."""
    slug = "".join(
        ch if (ch.isalnum() or ch in "-_") else "-"
        for ch in str(dir_name).strip().lower()
    ).strip("-") or "group"
    return f"taskbargroups-{slug}"


def parse_binding(raw: str) -> str:
    text = raw.strip()
    if text.startswith("@as"):
        text = text[3:].strip()
    if text.startswith("["):
        try:
            values = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return ""
        if isinstance(values, (list, tuple)):
            return next((str(value) for value in values if value), "")
        return ""
    if text.startswith("@s"):
        text = text[2:].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        text = text[1:-1]
    return text


_MODIFIER_DISPLAY = {
    "Control": "Ctrl",
    "Primary": "Ctrl",
    "Shift": "Shift",
    "Alt": "Alt",
    "Super": "Super",
    "Meta": "Super",
    "Mod1": "Alt",
    "Mod4": "Super",
}


def cinnamon_to_display(binding: str) -> str:
    """แปลง `<Control><Alt>t` → `Ctrl+Alt+T` เพื่อโชว์ในลิสต์."""
    text = (binding or "").strip()
    if not text:
        return ""
    parts: list[str] = []
    text = (binding or "").strip()
    while text.startswith("<"):
        end = text.find(">")
        if end == -1:
            break
        token = text[1:end]
        text = text[end + 1 :]
        parts.append(_MODIFIER_DISPLAY.get(token, token))
    key = text.strip()
    if len(key) == 1:
        key = key.upper()
    elif key:
        key = key[0].upper() + key[1:]
    return "+".join([*parts, key]) if key else "+".join(parts)


def get_binding(slot: str, runner: Runner = _run) -> str:
    try:
        raw = runner(binding_get_command(slot))
    except HotkeyError:
        return ""
    return parse_binding(raw)


def group_hotkeys(slots: Sequence[str], runner: Runner = _run) -> dict[str, str]:
    """คืน {slot: binding} เฉพาะ slot ที่ลงทะเบียนใน custom-list แล้ว.

    คืน {} ทันทีถ้าไม่ใช่ Cinnamon (กัน subprocess ตอนเทสต์/เดสก์ท็อปอื่น).
    """
    if not is_cinnamon():
        return {}
    try:
        registered = set(parse_gvariant_string_array(runner(list_command())))
    except HotkeyError:
        return {}
    result: dict[str, str] = {}
    for slot in slots:
        if slot not in registered:
            continue
        binding = get_binding(slot, runner)
        if binding:
            result[slot] = binding
    return result


def set_list_command(values: Sequence[str]) -> list[str]:
    return ["gsettings", "set", CINNAMON_BASE, "custom-list", _format_gvariant_string_array(values)]


def set_key_command(slot: str, key: str, value: str) -> list[str]:
    path = f"{CINNAMON_CUSTOM}:{CINNAMON_PATH_ROOT}{slot}/"
    return ["gsettings", "set", path, key, _format_gvariant_string(value)]


def set_binding_command(slot: str, binding: str) -> list[str]:
    return set_bindings_command(slot, [binding])


def set_bindings_command(slot: str, bindings: Sequence[str]) -> list[str]:
    path = f"{CINNAMON_CUSTOM}:{CINNAMON_PATH_ROOT}{slot}/"
    return ["gsettings", "set", path, "binding", _format_gvariant_string_array(bindings)]


def reset_key_command(slot: str, key: str) -> list[str]:
    path = f"{CINNAMON_CUSTOM}:{CINNAMON_PATH_ROOT}{slot}/"
    return ["gsettings", "reset", path, key]


def _clean_list(values: Sequence[str]) -> list[str]:
    return [value for value in values if value != _DUMMY]


def _touch_custom_list(values: Sequence[str], runner: Runner) -> None:
    """ตั้ง `custom-list` ให้ต่างจากเดิมชั่วคราว (dummy) แล้วตั้งค่าจริง เพื่อยิง change event.

    Cinnamon rebuild custom keybindings เฉพาะตอน key `custom-list` เปลี่ยน.
    """
    base = _clean_list(values)
    runner(set_list_command([*base, _DUMMY]))
    runner(set_list_command(base))


def register_cinnamon_hotkey(
    slot: str,
    title: str,
    command: str,
    binding: str,
    runner: Runner = _run,
) -> None:
    # ตั้งค่า path ให้ครบก่อน แล้วค่อยแตะ custom-list เป็นขั้นสุดท้าย
    # (ไม่งั้น Cinnamon rebuild ตอน list เปลี่ยน แต่ยังอ่านค่าไม่ได้ → binding ไม่ทำงาน)
    current = _clean_list(parse_gvariant_string_array(runner(list_command())))
    if slot not in current:
        current.append(slot)
    runner(set_key_command(slot, "name", title))
    runner(set_key_command(slot, "command", command))
    runner(set_binding_command(slot, binding))
    _touch_custom_list(current, runner)


def unregister_cinnamon_hotkey(slot: str, runner: Runner = _run) -> None:
    current = _clean_list(parse_gvariant_string_array(runner(list_command())))
    # ให้ slot อยู่ใน list ชั่วคราวเสมอ เพื่อให้ Cinnamon เรียก addHotKeyArray(name, [])
    # แล้วสั่ง global.display.remove_keybinding() จริง (ถ้าไม่ทำ จะถอนจาก list เฉยๆ
    # แต่ remove_custom_keybindings() ของ Cinnamon ลบเฉพาะชื่อที่มี "custom" — ไม่ลบของเรา)
    temp = current if slot in current else [*current, slot]
    runner(set_bindings_command(slot, []))
    _touch_custom_list(temp, runner)
    for key in ("name", "command", "binding"):
        runner(reset_key_command(slot, key))
    remaining = [value for value in current if value != slot]
    _touch_custom_list(remaining, runner)
