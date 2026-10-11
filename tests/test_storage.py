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


if __name__ == "__main__":
    unittest.main()
