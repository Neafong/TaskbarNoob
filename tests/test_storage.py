import sys
import tempfile
import unittest
from pathlib import Path

from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.storage import ConfigStore, StorageError, safe_dir_name


class SafeDirNameTests(unittest.TestCase):
    def test_strips_invalid_chars(self) -> None:
        self.assertEqual(safe_dir_name("a/b:c*d"), "a_b_c_d")

    def test_blank_falls_back(self) -> None:
        self.assertEqual(safe_dir_name("   "), "group")


class ConfigStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_empty_list(self) -> None:
        self.assertEqual(self.store.list_groups(), [])

    def test_save_then_load(self) -> None:
        group = Group(
            name="My Group",
            width=3,
            items=[Shortcut(name="Editor", target="/usr/bin/editor")],
        )
        path = self.store.save_group(group)
        self.assertTrue(path.is_file())
        self.assertEqual(self.store.list_groups(), ["My Group"])
        loaded = self.store.load_group("My Group")
        self.assertEqual(loaded, group)

    def test_icons_dir_created(self) -> None:
        self.store.save_group(Group(name="G"))
        self.assertTrue(self.store.icons_dir("G").is_dir())

    def test_import_group_icon_freshens_mtime(self) -> None:
        """mtime ไฟล์ที่ import ต้องเป็น "ตอนนี้" ไม่ใช่ของต้นทาง — ไม่งั้น .ico
        ที่แปลงไว้แล้ว (คิดจาก mtime) ดูใหม่กว่า .png นี้ → เปลี่ยนไอคอนแล้ว
        .lnk ยังใช้รูปเก่า."""
        import os

        self.store.save_group(Group(name="G"))
        source = Path(self._tmp.name) / "pick.png"
        source.write_bytes(b"png")
        os.utime(source, (1_000_000_000, 1_000_000_000))  # ทำ mtime เก่าจงใจ

        self.store.import_group_icon("G", str(source))
        # ชื่อไฟล์มี hash suffix → หาไฟล์ที่ขึ้นต้นด้วย group_icon_
        dests = list(self.store.group_dir("G").glob("group_icon_*"))
        self.assertEqual(len(dests), 1)
        dest = dests[0]
        self.assertGreater(dest.stat().st_mtime, source.stat().st_mtime)

    def test_save_invalid_raises(self) -> None:
        with self.assertRaises(StorageError):
            self.store.save_group(Group(name=""))

    def test_load_missing_raises(self) -> None:
        with self.assertRaises(StorageError):
            self.store.load_group("nope")

    def test_delete(self) -> None:
        self.store.save_group(Group(name="G"))
        self.store.delete_group("G")
        self.assertEqual(self.store.list_groups(), [])

    def test_delete_missing_raises(self) -> None:
        with self.assertRaises(StorageError):
            self.store.delete_group("nope")

    def test_corrupt_file_raises(self) -> None:
        path = self.store.group_dir("Bad")
        path.mkdir(parents=True)
        (path / "group.json").write_text("{ not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.store.load_group("Bad")

    def test_duplicate_group_copies_and_appends_order(self) -> None:
        self.store.save_group(
            Group(name="Tool", items=[Shortcut(name="Editor", target="/usr/bin/editor")])
        )
        icon = self.store.icons_dir("Tool")
        (icon / "a.png").write_bytes(b"png")
        self.store.save_order(["Tool"])
        new_dir = self.store.duplicate_group("Tool", "Tool (copy)")
        self.assertEqual(new_dir, "Tool (copy)")
        self.assertEqual(self.store.load_group("Tool (copy)").name, "Tool (copy)")
        self.assertEqual(len(self.store.load_group("Tool (copy)").items), 1)
        self.assertTrue((self.store.icons_dir("Tool (copy)") / "a.png").is_file())
        self.assertEqual(self.store.load_order()[-1], "Tool (copy)")
        self.assertEqual(self.store.list_groups(), ["Tool", "Tool (copy)"])

    def test_duplicate_group_missing_raises(self) -> None:
        with self.assertRaises(StorageError):
            self.store.duplicate_group("nope")

    def test_duplicate_group_unique_on_collision(self) -> None:
        self.store.save_group(Group(name="G"))
        first = self.store.duplicate_group("G", "G copy")
        second = self.store.duplicate_group("G", "G copy")
        self.assertEqual(first, "G copy")
        self.assertEqual(second, "G copy 2")


class OrderHygieneTests(unittest.TestCase):
    """ชื่อกลุ่มที่ลบแล้วต้องหายจาก order.json ไม่งั้นสร้างชื่อเดิมแล้วซ้ำ."""

    def test_delete_removes_name_from_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            store.save_order(["Alpha"])
            store.delete_group("Alpha")
            self.assertEqual(store.load_order(), [])

    def test_recreate_same_name_after_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            store.save_order(["Alpha"])
            store.delete_group("Alpha")
            store.save_group(Group(name="Alpha", items=[]))
            self.assertEqual(store.load_order(), ["Alpha"])

    def test_new_group_enters_order(self) -> None:
        """กลุ่มใหม่ต้องเข้า order — เดิมมีแต่โฟลเดอร์ ทำให้ไม่มีลำดับ"""
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            self.assertEqual(store.load_order(), ["Alpha"])

    def test_edit_existing_does_not_reorder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            store.save_group(Group(name="Beta", items=[]))
            store.save_group(
                Group(name="Alpha", items=[Shortcut(name="x", target="x.exe")])
            )
            self.assertEqual(store.load_order(), ["Alpha", "Beta"])  # ยังอยู่หน้าเดิม

    def test_save_order_adopts_orphan_group(self) -> None:
        """กลุ่มที่มีโฟลเดอร์แต่หลุดจาก order ต้องถูกดึงกลับมา"""
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            store.save_group(Group(name="Orphan", items=[]))
            store.order_file().write_text("[]", encoding="utf-8")  # order หาย
            store.save_order(store.load_order())
            self.assertEqual(store.load_order(), ["Alpha", "Orphan"])

    def test_save_order_drops_missing_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Alpha", items=[]))
            store.save_order(["Alpha", "Ghost"])
            self.assertEqual(store.load_order(), ["Alpha"])  # Ghost ถูกตัดทิ้ง

    def test_save_order_drops_case_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="test", items=[]))
            store.save_order(["Game", "test", "Test"])
            kept = store.load_order()
            self.assertEqual(len(kept), len(set(kept)))  # ไม่มีชื่อซ้ำ
            self.assertIn("test", kept)

    def test_order_matches_disk_after_selfheal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            for name in ("A", "B", "C"):
                store.save_group(Group(name=name, items=[]))
            store.order_file().write_text('["C"]', encoding="utf-8")
            store.save_order(store.load_order())
            self.assertEqual(store.load_order(), ["C", "A", "B"])  # C ก่อน แล้วคนที่เหลือ


class CacheLocationTests(unittest.TestCase):
    def test_cache_dir_is_outside_groups(self) -> None:
        """`config/groups/` ต้องมีแต่กลุ่มจริง — ของแอปห้ามปนอยู่ข้างใน

        ผู้ใช้มักเปิดโฟลเดอร์นี้มาเพิ่มกลุ่มเอง ถ้ามีโฟลเดอร์แปลกๆ ปนอยู่
        จะเปิดแล้วไม่มีในรายการ (เพราะไม่มี group.json) → สับสน
        """
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            self.assertNotIn("groups", store.cache_dir().parts)
            self.assertTrue(str(store.cache_dir()).startswith(tmp))

    def test_list_groups_ignores_folder_without_group_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp))
            store.save_group(Group(name="Real", items=[]))
            (store.groups_dir / "EmptyFolder").mkdir()  # โฟลเดอร์เปล่า ไม่ใช่กลุ่ม
            self.assertEqual(store.list_groups(), ["Real"])


if __name__ == "__main__":
    unittest.main()
