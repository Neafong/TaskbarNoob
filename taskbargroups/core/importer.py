"""นำเข้ากลุ่มจาก Taskbar Groups ต้นฉบับ (Windows) — `ObjectData.xml` → `Group`.

รูปแบบ XML อ้างอิงจากคลาส `Category`/`ProgramShortcut` ของต้นฉบับ
(.NET XmlSerializer) เรียงลำดับดังนี้:

    <Category>
      <Name/>
      <ColorString>#1F1F1F</ColorString>
      <allowOpenAll>false</allowOpenAll>
      <ShortcutList>
        <ProgramShortcut>
          <FilePath/>
          <isWindowsApp>false</isWindowsApp>
          <name/>
          <Arguments/>
          <WorkingDirectory/>
        </ProgramShortcut>
      </ShortcutList>
      <Width/>
      <Opacity/>
    </Category>
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from .icons import IconError, cache_icon, is_image_file
from .models import MAX_GROUP_NAME_LEN, ColorMode, Group, Shortcut, is_hex_color
from .storage import ConfigStore, StorageError, safe_dir_name

OBJECT_DATA_NAME = "ObjectData.xml"
GROUP_IMAGE_NAME = "GroupImage.png"
GROUP_ICON_NAME = "GroupIcon.ico"
ICONS_DIR_NAME = "Icons"

NUMERIC_COLUMN_MIN = 1
NUMERIC_COLUMN_MAX = 50
OPACITY_MIN = 0
OPACITY_MAX = 100

UPSTREAM_DARK = "#1F1F1F"
UPSTREAM_LIGHT = "#E6E6E6"

_WINDOWS_APP_STRIP = re.compile(r"""[\*'",_&#^@]""")
_FOLDER_SUFFIX = "_FolderObjTSKGRoup.png"
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def _basename_stem(path_text: str) -> str:
    """ดึงชื่อไฟล์ไม่มีนามสกุล โดยเข้าใจ path แบบ Windows ด้วย."""
    text = path_text or ""
    if "\\" in text or _WINDOWS_DRIVE.match(text):
        return PureWindowsPath(text).stem
    return PurePosixPath(text).stem


class GroupImportError(Exception):
    """โยนเมื่ออ่าน/นำเข้ากลุ่มจากต้นฉบับไม่สำเร็จ."""


@dataclass
class RawEntry:
    shortcut: Shortcut
    is_windows_app: bool = False
    file_path: str = ""

    def cached_icon_names(self) -> list[str]:
        """ชื่อไฟล์ไอคอนที่ต้นฉบับอาจใช้ในโฟลเดอร์ Icons/."""
        path_text = self.file_path or self.shortcut.target
        if self.is_windows_app:
            return [f"{_WINDOWS_APP_STRIP.sub('', path_text)}.png"]
        stem = _basename_stem(path_text)
        return [f"{stem}{_FOLDER_SUFFIX}", f"{stem}.png"]


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    for child in parent:
        if _localname(child.tag) == name:
            return child
    return None


def _normalize_color(value: str | None) -> tuple[ColorMode, str | None]:
    if not value:
        return ColorMode.DARK, None
    normalized = value.strip().upper()
    if normalized == UPSTREAM_DARK:
        return ColorMode.DARK, None
    if normalized == UPSTREAM_LIGHT:
        return ColorMode.LIGHT, None
    if is_hex_color(normalized):
        return ColorMode.CUSTOM, normalized.lower()
    return ColorMode.DARK, None


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _as_int(value: str, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _parse(xml_text: str) -> tuple[Group, list[RawEntry]]:
    lowered = xml_text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise GroupImportError("ไฟล์ XML มี DOCTYPE/ENTITY ซึ่งไม่อนุญาต (กัน XML entity attack)")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise GroupImportError(f"ไฟล์ ObjectData.xml ผิดรูปแบบ: {exc}") from exc
    if _localname(root.tag) != "Category":
        raise GroupImportError(f"ไม่ใช่ไฟล์กลุ่มของ Taskbar Groups (root = {_localname(root.tag)})")

    name = _text(_find(root, "Name"))
    color_mode, custom_color = _normalize_color(_text(_find(root, "ColorString")))
    allow_open_all = _as_bool(_text(_find(root, "allowOpenAll")))
    width = _clamp(_as_int(_text(_find(root, "Width")), 6), NUMERIC_COLUMN_MIN, NUMERIC_COLUMN_MAX)
    opacity = _clamp(_as_int(_text(_find(root, "Opacity")), 0), OPACITY_MIN, OPACITY_MAX)

    entries: list[RawEntry] = []
    shortcut_list = _find(root, "ShortcutList")
    if shortcut_list is not None:
        for node in shortcut_list:
            if _localname(node.tag) != "ProgramShortcut":
                continue
            file_path = _text(_find(node, "FilePath"))
            is_windows_app = _as_bool(_text(_find(node, "isWindowsApp")))
            arguments = _text(_find(node, "Arguments"))
            working_dir = _text(_find(node, "WorkingDirectory")) or None
            item_name = _text(_find(node, "name")) or _basename_stem(file_path) or file_path
            shortcut = Shortcut(
                name=item_name,
                target=file_path,
                working_dir=working_dir,
                arguments=arguments,
                icon=None,
            )
            entries.append(
                RawEntry(shortcut=shortcut, is_windows_app=is_windows_app, file_path=file_path)
            )

    group = Group(
        name=name,
        icon=None,
        width=width,
        color_mode=color_mode,
        custom_color=custom_color,
        opacity=opacity,
        allow_open_all=allow_open_all,
        items=[entry.shortcut for entry in entries],
    )
    return group, entries


def parse_object_data(xml_text: str) -> Group:
    """แปลงข้อความ ObjectData.xml เป็น Group (ไม่แตะดิสก์)."""
    group, _entries = _parse(xml_text)
    return group


def load_object_data(path: str | Path) -> Group:
    """อ่าน ObjectData.xml จากไฟล์แล้วคืน Group."""
    source = Path(path)
    if source.is_dir():
        source = source / OBJECT_DATA_NAME
    try:
        xml_text = source.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        raise GroupImportError(f"อ่าน ObjectData.xml ไม่สำเร็จ: {exc}") from exc
    return parse_object_data(xml_text)


def _unique_group_name(store: ConfigStore, name: str) -> str:
    desired = (name or "").strip() or "นำเข้าจาก Windows"
    return store.unique_group_name(desired, old_dir=None)


def import_group(
    store: ConfigStore,
    source_dir: str | Path,
    name: str | None = None,
) -> str:
    """นำเข้ากลุ่มจากโฟลเดอร์ต้นฉบับ (มี ObjectData.xml) มาอยู่ใน store.

    คืนชื่อโฟลเดอร์ของกลุ่มที่สร้างใหม่.
    """
    directory = Path(source_dir)
    data_path = directory / OBJECT_DATA_NAME if directory.is_dir() else directory
    if not data_path.is_file():
        raise GroupImportError(f"ไม่พบไฟล์ {OBJECT_DATA_NAME}: {directory}")
    base_dir = data_path.parent

    try:
        group, entries = _parse(data_path.read_text(encoding="utf-8-sig", errors="replace"))
    except OSError as exc:
        raise GroupImportError(f"อ่าน ObjectData.xml ไม่สำเร็จ: {exc}") from exc

    if name:
        group.name = name
    group.name = _unique_group_name(store, group.name)

    for index, entry in enumerate(entries, start=1):
        if not entry.shortcut.name:
            entry.shortcut.name = f"Shortcut {index}"

    try:
        store.save_group(group)
        dir_name = safe_dir_name(group.name)

        for group_image in (GROUP_IMAGE_NAME, GROUP_ICON_NAME):
            source_icon = base_dir / group_image
            if is_image_file(source_icon):
                group.icon = store.import_group_icon(dir_name, source_icon)
                break

        source_icons = base_dir / ICONS_DIR_NAME
        if source_icons.is_dir():
            target_icons = store.icons_dir(dir_name)
            for index, entry in enumerate(entries, start=1):
                for candidate_name in entry.cached_icon_names():
                    candidate = source_icons / candidate_name
                    if is_image_file(candidate):
                        try:
                            stored = cache_icon(
                                candidate, target_icons, f"{index:02d}-{entry.shortcut.name}"
                            )
                        except IconError:
                            continue
                        entry.shortcut.icon = f"icons/{stored}"
                        break

        store.save_group(group)
    except (StorageError, OSError) as exc:
        raise GroupImportError(str(exc)) from exc

    return dir_name
