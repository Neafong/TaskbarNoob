import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from taskbargroups.core import archive
from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.storage import ConfigStore


def make_store(root: str | Path) -> ConfigStore:
    store = ConfigStore(Path(root))
    return store


class ExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self._tmp.name) / "config"
        self.store = make_store(self.cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_export_contains_expected_members(self) -> None:
        self.store.save_group(Group(name="Tool"))
        self.store.save_order(["Tool"])
        (self.cfg / "settings.json").write_text(
            json.dumps({"language": "th"}), encoding="utf-8"
        )
        lang_dir = self.cfg / "lang"
        lang_dir.mkdir(parents=True, exist_ok=True)
        (lang_dir / "ja.json").write_text("{}", encoding="utf-8")

        out = archive.export_config(self.cfg, Path(self._tmp.name) / "backup.zip")
        report = archive.inspect_zip(out)
        self.assertIn("Tool", report.groups)
        self.assertTrue(report.has_settings)
        self.assertEqual(report.has_lang, ["ja.json"])
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
        self.assertIn("order.json", names)
        self.assertIn("settings.json", names)
        self.assertIn("lang/ja.json", names)


class RoundTripTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.src = self.root / "src"
        self.store = make_store(self.src)
        self.store.save_group(
            Group(name="Tool", items=[Shortcut(name="Term", target="/usr/bin/xterm")])
        )
        self.store.save_order(["Tool"])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _export(self) -> Path:
        return archive.export_config(self.src, self.root / "backup.zip")

    def test_roundtrip_replace(self) -> None:
        zip_path = self._export()
        dest = self.root / "dest"
        report = archive.import_config(zip_path, dest, mode="replace")
        dest_store = make_store(dest)
        self.assertEqual(dest_store.list_groups(), ["Tool"])
        self.assertEqual(report.groups_imported, ["Tool"])
        self.assertEqual(dest_store.load_group("Tool").name, "Tool")

    def test_merge_suffixes_conflicting_group(self) -> None:
        zip_path = self._export()
        dest = self.root / "dest"
        dest_store = make_store(dest)
        dest_store.save_group(Group(name="Tool"))
        report = archive.import_config(zip_path, dest, mode="merge")
        self.assertEqual(dest_store.list_groups(), ["Tool", "Tool (2)"])
        self.assertIn("Tool (2)", report.groups_imported)

    def test_merge_does_not_touch_settings(self) -> None:
        (self.src / "settings.json").write_text(
            json.dumps({"language": "th"}), encoding="utf-8"
        )
        zip_path = self._export()
        dest = self.root / "dest"
        dest_store = make_store(dest)
        dest_store.save_group(Group(name="X"))
        (dest / "settings.json").write_text(
            json.dumps({"language": "en"}), encoding="utf-8"
        )
        report = archive.import_config(zip_path, dest, mode="merge")
        self.assertFalse(report.settings_imported)
        self.assertEqual(
            json.loads((dest / "settings.json").read_text(encoding="utf-8")),
            {"language": "en"},
        )

    def test_replace_creates_backup_and_replaces(self) -> None:
        zip_path = self._export()
        dest = self.root / "dest"
        dest_store = make_store(dest)
        dest_store.save_group(Group(name="Old"))
        report = archive.import_config(zip_path, dest, mode="replace")
        self.assertIsNotNone(report.backup_dir)
        self.assertTrue(report.backup_dir.is_dir())
        backup_store = make_store(report.backup_dir)
        self.assertEqual(backup_store.list_groups(), ["Old"])
        self.assertEqual(dest_store.list_groups(), ["Tool"])


class SafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_zip_slip_rejected(self) -> None:
        bad = self.root / "bad.zip"
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("../evil.txt", "x")
        dest = self.root / "dest"
        dest.mkdir()
        with self.assertRaises(archive.ArchiveError):
            archive.import_config(bad, dest, mode="merge")

    def test_non_whitelisted_skipped(self) -> None:
        z = self.root / "ok.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("groups/Tool/group.json", json.dumps({"name": "Tool"}))
            zf.writestr("random.txt", "junk")
            zf.writestr(".DS_Store", "junk")
        dest = self.root / "dest"
        report = archive.import_config(z, dest, mode="merge")
        self.assertEqual(report.groups_imported, ["Tool"])
        self.assertFalse((dest / "random.txt").exists())

    def test_invalid_group_rejected(self) -> None:
        z = self.root / "bad.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("groups/Tool/group.json", "{not valid json}")
        dest = self.root / "dest"
        dest.mkdir()
        with self.assertRaises(archive.ArchiveError):
            archive.import_config(z, dest, mode="merge")

    def test_too_big_rejected(self) -> None:
        z = self.root / "big.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("order.json", "[]")
        original = archive.MAX_ZIP_BYTES
        archive.MAX_ZIP_BYTES = 1
        try:
            with self.assertRaises(archive.ArchiveError):
                archive.inspect_zip(z)
        finally:
            archive.MAX_ZIP_BYTES = original

    def test_not_a_zip_rejected(self) -> None:
        f = self.root / "notzip.txt"
        f.write_text("hello", encoding="utf-8")
        with self.assertRaises(archive.ArchiveError):
            archive.inspect_zip(f)

    def test_import_non_config_zip_rejected(self) -> None:
        z = self.root / "other.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("random.txt", "junk")
        dest = self.root / "dest"
        dest.mkdir()
        with self.assertRaises(archive.ArchiveError):
            archive.import_config(z, dest, mode="merge")


class BackupCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cfg = self.root / "config"
        self.cfg.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_list_backups_only_matching_dirs(self) -> None:
        (self.root / "config.bak-20250101-000000").mkdir()
        (self.root / "config.bak-20260101-000000").mkdir()
        (self.root / "config.bakup").mkdir()
        (self.root / "config.bak-20250101-000000.txt").write_text("x", encoding="utf-8")
        (self.root / "other").mkdir()
        backups = archive.list_backups(self.cfg)
        self.assertEqual(
            [b.name for b in backups],
            ["config.bak-20260101-000000", "config.bak-20250101-000000"],
        )

    def test_delete_backups_removes_only_valid_targets(self) -> None:
        keep = self.root / "config.bak-20250101-000000"
        drop = self.root / "config.bak-20260101-000000"
        keep.mkdir()
        drop.mkdir()
        (keep / "settings.json").write_text("{}", encoding="utf-8")
        outsider = self.root / "elsewhere" / "config.bak-20260101-000000"
        outsider.mkdir(parents=True)
        removed = archive.delete_backups(self.cfg, [drop, outsider, self.cfg])
        self.assertEqual(removed, 1)
        self.assertFalse(drop.exists())
        self.assertTrue(keep.exists())
        self.assertTrue(outsider.exists())


if __name__ == "__main__":
    unittest.main()
