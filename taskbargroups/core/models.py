"""โครงสร้างข้อมูลของกลุ่มและ shortcut (ข้าม OS, ไม่ผูก GUI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = 1
MAX_GROUP_NAME_LEN = 49
MAX_ITEM_NAME_LEN = 27
MIN_WIDTH = 1
MAX_WIDTH = 50
MIN_OPACITY = 0
MAX_OPACITY = 100
MIN_ICON_SIZE = 16
MAX_ICON_SIZE = 128
DEFAULT_ICON_SIZE = 32
DEFAULT_OPACITY = 10

_HEX_LENGTHS = {4, 7}
_HEX_DIGITS = set("0123456789abcdefABCDEF")


class ColorMode(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"

    @classmethod
    def from_value(cls, value: Any) -> "ColorMode":
        if isinstance(value, ColorMode):
            return value
        try:
            return cls(str(value).lower())
        except ValueError:
            return cls.DARK


def is_hex_color(value: str | None) -> bool:
    if not isinstance(value, str) or len(value) not in _HEX_LENGTHS:
        return False
    if not value.startswith("#"):
        return False
    return all(ch in _HEX_DIGITS for ch in value[1:])


@dataclass
class Shortcut:
    name: str
    target: str
    working_dir: str | None = None
    arguments: str = ""
    icon: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "target": self.target,
            "working_dir": self.working_dir,
            "arguments": self.arguments,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Shortcut":
        return cls(
            name=str(data.get("name", "")),
            target=str(data.get("target", "")),
            working_dir=(data.get("working_dir") or None),
            arguments=str(data.get("arguments", "")),
            icon=(data.get("icon") or None),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("ชื่อ shortcut ห้ามว่าง")
        if len(self.name) > MAX_ITEM_NAME_LEN:
            errors.append(f"ชื่อ shortcut ต้องไม่เกิน {MAX_ITEM_NAME_LEN} ตัวอักษร")
        if not self.target.strip():
            errors.append("target ของ shortcut ห้ามว่าง")
        return errors


@dataclass
class Group:
    name: str
    icon: str | None = None
    width: int = 6
    color_mode: ColorMode = ColorMode.DARK
    custom_color: str | None = None
    opacity: int = DEFAULT_OPACITY
    icon_size: int = DEFAULT_ICON_SIZE
    allow_open_all: bool = False
    items: list[Shortcut] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "icon": self.icon,
            "width": self.width,
            "color": {
                "mode": self.color_mode.value,
                "custom": self.custom_color,
            },
            "opacity": self.opacity,
            "icon_size": self.icon_size,
            "allow_open_all": self.allow_open_all,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Group":
        color = data.get("color")
        if not isinstance(color, dict):
            color = {}
        raw_items = data.get("items")
        if not isinstance(raw_items, list):
            raw_items = []
        return cls(
            name=str(data.get("name", "")),
            icon=(data.get("icon") or None),
            width=int(data.get("width", 6)),
            color_mode=ColorMode.from_value(color.get("mode", "dark")),
            custom_color=(color.get("custom") or None),
            opacity=int(data.get("opacity", DEFAULT_OPACITY)),
            icon_size=int(data.get("icon_size", DEFAULT_ICON_SIZE)),
            allow_open_all=bool(data.get("allow_open_all", False)),
            items=[Shortcut.from_dict(item) for item in raw_items if isinstance(item, dict)],
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("ชื่อกลุ่มห้ามว่าง")
        if len(self.name) > MAX_GROUP_NAME_LEN:
            errors.append(f"ชื่อกลุ่มต้องไม่เกิน {MAX_GROUP_NAME_LEN} ตัวอักษร")
        if not (MIN_WIDTH <= self.width <= MAX_WIDTH):
            errors.append(f"width ต้องอยู่ระหว่าง {MIN_WIDTH} ถึง {MAX_WIDTH}")
        if not (MIN_OPACITY <= self.opacity <= MAX_OPACITY):
            errors.append(f"opacity ต้องอยู่ระหว่าง {MIN_OPACITY} ถึง {MAX_OPACITY}")
        if not (MIN_ICON_SIZE <= self.icon_size <= MAX_ICON_SIZE):
            errors.append(
                f"ขนาดไอคอนต้องอยู่ระหว่าง {MIN_ICON_SIZE} ถึง {MAX_ICON_SIZE}"
            )
        if self.color_mode is ColorMode.CUSTOM and not is_hex_color(self.custom_color):
            errors.append("custom color ต้องเป็นค่ารูปแบบ hex เช่น #RRGGBB")
        for index, item in enumerate(self.items, start=1):
            for err in item.validate():
                errors.append(f"รายการที่ {index}: {err}")
        return errors
