"""อ่าน/เขียนกลุ่มลงดิสก์เป็น JSON ต่อกลุ่ม (portable)."""

from __future__ import annotations

import json
import re
import os
import shutil
from pathlib import Path

from .models import MAX_GROUP_NAME_LEN, Group
from .paths import default_config_dir
from .paths import groups_root as _groups_root

ORDER_FILE = "order.json"
CACHE_DIR_NAME = "cache"


GROUP_FILE_NAME = "group.json"
ICONS_DIR_NAME = "icons"
GROUP_ICON_STEM = "group_icon"

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class StorageError(Exception):
    """โยนเมื่ออ่าน/เขียนกลุ่มไม่สำเร็จ."""


def safe_dir_name(name: str) -> str:
    cleaned = _INVALID_CHARS.sub("_", name.strip())
    cleaned = cleaned.strip(" .")
    return cleaned or "group"


class ConfigStore:
    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir is not None else default_config_dir()
        self.groups_dir = _groups_root(self.config_dir)

    def list_groups(self) -> list[str]:
        if not self.groups_dir.is_dir():
            return []
        names = [
            path.name
            for path in self.groups_dir.iterdir()
            if path.is_dir() and (path / GROUP_FILE_NAME).is_file()
        ]
        order = self.load_order()
        # normcase: บน Windows `Test` กับ `test` คือโฟลเดอร์เดียว
        # ถ้า rank เทียบตรงๆ กลุ่มจะหลุดไปต่อท้ายทั้งที่อยู่ใน order
        rank = {os.path.normcase(name): index for index, name in enumerate(order)}
        return sorted(names, key=lambda name: (rank.get(os.path.normcase(name), len(rank)), name))

    def order_file(self) -> Path:
        return self.config_dir / ORDER_FILE

    def load_order(self) -> list[str]:
        try:
            raw = self.order_file().read_text(encoding="utf-8")
        except OSError:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [str(name) for name in data]

    def _prune_order(self, dir_names: list[str]) -> list[str]:
        """ปรับ order ให้ตรงกับโฟลเดอร์จริงเสมอ (กู้ config ที่พังไปแล้ว)

        - ตัดชื่อที่ไม่มีโฟลเดอร์จริงทิ้ง
        - เติมกลุ่มที่มีโฟลเดอร์แต่หลุดจาก order (เคยเกิดตอนกดเพิ่มกลุ่ม)
        - ตัดชื่อซ้ำ (เทียบ `normcase` — บน Windows/macOS โฟลเดอร์ไม่สนตัวพิมพ์
          `Test` กับ `test` คือที่เดียวกัน ถ้าเก็บทั้งคู่จะเห็นกลุ่มซ้ำสองแถว)
        """
        on_disk: list[str] = []
        if self.groups_dir.is_dir():
            on_disk = [
                path.name
                for path in self.groups_dir.iterdir()
                if path.is_dir() and (path / GROUP_FILE_NAME).is_file()
            ]
        seen: set[str] = set()
        keep: list[str] = []
        for name in list(dir_names) + on_disk:
            text = str(name)
            key = os.path.normcase(text)
            if key in seen:
                continue
            seen.add(key)
            # ชื่อที่ใช้ต้องตรงกับโฟลเดอร์จริง (บน Windows case ไม่สำคัญ)
            real = next((d for d in on_disk if os.path.normcase(d) == key), None)
            if real is None:
                continue
            keep.append(real)
        return keep

    def save_order(self, dir_names: list[str]) -> None:
        dir_names = self._prune_order(dir_names)
        try:
            self.order_file().write_text(
                json.dumps([str(name) for name in dir_names], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"บันทึกลำดับกลุ่มไม่สำเร็จ: {exc}") from exc

    def group_dir(self, dir_name: str) -> Path:
        return self.groups_dir / dir_name

    def icons_dir(self, dir_name: str) -> Path:
        return self.group_dir(dir_name) / ICONS_DIR_NAME

    def cache_dir(self) -> Path:
        """โฟลเดอร์ cache ของแอป — อยู่นอก `groups/` เพื่อไม่ให้สับสนกับกลุ่ม

        ผู้ใช้มักเปิด `config/groups/` มาเพิ่มกลุ่มเอง ถ้าเรายัดของแอปไว้ข้างใน
        จะเห็นโฟลเดอร์แปลกๆ ที่เปิดแล้วไม่มีในรายการ (เพราะไม่มี group.json)
        """
        return self.config_dir / CACHE_DIR_NAME

    def group_icon_path(self, dir_name: str) -> Path:
        return self.group_dir(dir_name) / GROUP_ICON_STEM

    def resolve_relative(self, dir_name: str, relative: str | None) -> Path | None:
        if not relative:
            return None
        candidate = self.group_dir(dir_name) / relative
        return candidate if candidate.exists() else None

    def import_group_icon(self, dir_name: str, source: str | Path) -> str:
        src = Path(source)
        if not src.is_file():
            raise StorageError(f"ไม่พบไฟล์ไอคอน: {source}")
        target_dir = self.group_dir(dir_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        # ลบไอคอนเก่าทั้งหมด (รวม hashed versions)
        for old in target_dir.glob(f"{GROUP_ICON_STEM}*"):
            try:
                old.unlink()
            except OSError:
                pass
        # ใช้ hash ของ content เป็น suffix เพื่อ bust Windows icon cache
        # (ถ้าใช้ชื่อเดิม Windows จะโชว์ไอคอนเก่าที่แคชไว้ตาม path)
        import hashlib

        content_hash = hashlib.sha1(src.read_bytes()).hexdigest()[:8]
        dest = target_dir / f"{GROUP_ICON_STEM}_{content_hash}{src.suffix.lower()}"
        try:
            # ใช้ copy (ไม่ใช่ copy2) — mtime ของ dest ต้องเป็น "ตอนนี้"
            shutil.copy(src, dest)
        except OSError as exc:
            raise StorageError(f"คัดลอกไอคอนไม่สำเร็จ: {exc}") from exc
        return dest.name

    def load_group(self, dir_name: str) -> Group:
        path = self.group_dir(dir_name) / GROUP_FILE_NAME
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise StorageError(f"ไม่พบกลุ่ม: {dir_name}") from exc
        except OSError as exc:
            raise StorageError(f"อ่านกลุ่ม '{dir_name}' ไม่สำเร็จ: {exc}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StorageError(f"ไฟล์กลุ่ม '{dir_name}' ผิดรูปแบบ: {exc}") from exc
        if not isinstance(data, dict):
            raise StorageError(f"ไฟล์กลุ่ม '{dir_name}' ต้องเป็น object JSON")
        return Group.from_dict(data)

    def save_group(self, group: Group) -> Path:
        errors = group.validate()
        if errors:
            raise StorageError("; ".join(errors))
        dir_name = safe_dir_name(group.name)
        target_dir = self.group_dir(dir_name)
        existed = target_dir.is_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        self.icons_dir(dir_name).mkdir(parents=True, exist_ok=True)
        path = target_dir / GROUP_FILE_NAME
        payload = json.dumps(group.to_dict(), indent=2, ensure_ascii=False) + "\n"
        try:
            path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"เขียนกลุ่ม '{group.name}' ไม่สำเร็จ: {exc}") from exc
        if not existed:
            # กลุ่มใหม่ต้องเข้า order ด้วย — ไม่งั้นไม่มีลำดับ
            # (เดิมพัง: กลุ่มใหม่มีแต่โฟลเดอร์ ไม่ถูกบันทึกลง order.json)
            self._append_order(dir_name)
        return path

    def _append_order(self, dir_name: str) -> None:
        order = self.load_order()
        key = os.path.normcase(dir_name)
        # แทนที่ชื่อเดิมที่ต่างแค่ตัวพิมพ์ (บน Windows เป็นโฟลเดอร์เดียวกัน)
        kept = [name for name in order if os.path.normcase(name) != key]
        self.save_order(kept + [dir_name])

    def delete_group(self, dir_name: str) -> None:
        target = self.group_dir(dir_name)
        if not target.is_dir():
            raise StorageError(f"ไม่พบกลุ่ม: {dir_name}")
        try:
            shutil.rmtree(target)
        except OSError as exc:
            raise StorageError(f"ลบกลุ่ม '{dir_name}' ไม่สำเร็จ: {exc}") from exc
        # ต้องลบชื่อออกจาก order ด้วย — ไม่งั้นชื่อค้างแล้วภายหลังสร้างชื่อเดิม
        # จะได้กลุ่มซ้ำ (บน Windows filesystem ไม่สนตัวพิมพ์ยิ่งชนง่าย)
        self.save_order([n for n in self.load_order() if n != dir_name])


    def unique_group_name(self, desired: str, old_dir: str | None = None, use_parens: bool = True) -> str:
        """คืนชื่อกลุ่มที่ไม่ชนกับกลุ่มที่มีอยู่ (เติม ' 2', ' 3', ...).

        ถ้า old_dir ระบุ และตรงกับ dir_name ที่ได้จาก desired เดิม จะยอมรับได้
        (ใช้ในกรณีแก้ไขชื่อกลุ่มเดิม) — เทียบด้วย normcase เพราะบน Windows/macOS
        โฟลเดอร์ไม่สนตัวพิมพ์ (`Test` == `test`)
        """
        base_desired = (desired or "").strip() or "กลุ่ม"
        name = base_desired
        counter = 2
        while True:
            dir_name = safe_dir_name(name)
            if old_dir and os.path.normcase(dir_name) == os.path.normcase(old_dir):
                return name
            if not self.group_dir(dir_name).is_dir():
                return name
            if use_parens:
                suffix = f" ({counter})"
            else:
                suffix = f" {counter}"
            if len(base_desired) + len(suffix) > MAX_GROUP_NAME_LEN:
                base_out = base_desired[: MAX_GROUP_NAME_LEN - len(suffix)]
            else:
                base_out = base_desired
            name = base_out + suffix
            counter += 1
    def duplicate_group(self, dir_name: str, new_name: str | None = None) -> str:
        """คัดลอกกลุ่ม (โฟลเดอร์ + ไอคอนทั้งหมด) เป็นกลุ่มใหม่ แล้วต่อท้ายลำดับ.

        คืนชื่อโฟลเดอร์ใหม่ (unique). ถ้าไม่ระบุ new_name จะต่อท้ายว่า 'copy'.
        """
        src = self.group_dir(dir_name)
        if not (src / GROUP_FILE_NAME).is_file():
            raise StorageError(f"ไม่พบกลุ่ม: {dir_name}")
        base = safe_dir_name(new_name) if new_name else f"{dir_name} copy"
        dest_dir_name = base
        counter = 2
        while self.group_dir(dest_dir_name).exists():
            dest_dir_name = f"{base} {counter}"
            counter += 1
        dest = self.group_dir(dest_dir_name)
        try:
            shutil.copytree(src, dest)
        except OSError as exc:
            raise StorageError(f"คัดลอกกลุ่ม '{dir_name}' ไม่สำเร็จ: {exc}") from exc
        try:
            group = self.load_group(dest_dir_name)
            group.name = dest_dir_name
            self.save_group(group)
        except StorageError:
            shutil.rmtree(dest, ignore_errors=True)
            raise
        order = [d for d in self.load_order() if d != dest_dir_name]
        order.append(dest_dir_name)
        self.save_order(order)
        return dest_dir_name
