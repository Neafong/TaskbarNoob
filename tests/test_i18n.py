import json
import os
import tempfile
import unittest
from pathlib import Path

from taskbargroups.core import i18n
from taskbargroups.core.i18n import setup
from taskbargroups.core.settings import Settings

QAPP = None


def _init_qapp():
    global QAPP
    if QAPP is None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        QAPP = QApplication.instance() or QApplication([])
    return QAPP


class I18nCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        i18n.setup("th", self._tmp.name)

    def tearDown(self) -> None:
        i18n.setup("th")
        self._tmp.cleanup()

    def test_default_is_thai(self) -> None:
        self.assertEqual(i18n.tr("main.add_group"), "เพิ่มกลุ่ม")

    def test_english_switches_strings(self) -> None:
        i18n.setup("en", self._tmp.name)
        self.assertEqual(i18n.tr("main.add_group"), "Add group")

    def test_format_placeholder(self) -> None:
        self.assertEqual(
            i18n.tr("main.import_ok_body", dir_name="Game"), "นำเข้ากลุ่มเป็น 'Game' แล้วค่ะ"
        )

    def test_missing_key_returns_key(self) -> None:
        self.assertEqual(i18n.tr("no.such.key"), "no.such.key")

    def test_user_language_overlay_wins(self) -> None:
        lang = Path(self._tmp.name) / "lang"
        lang.mkdir()
        (lang / "ja.json").write_text(
            json.dumps({"main.add_group": "グループ追加"}, ensure_ascii=False),
            encoding="utf-8",
        )
        i18n.setup("ja", self._tmp.name)
        self.assertEqual(i18n.tr("main.add_group"), "グループ追加")
        self.assertEqual(i18n.tr("app.title"), "TaskbarNoob")

    def test_available_languages_lists_builtin_and_user(self) -> None:
        lang = Path(self._tmp.name) / "lang"
        lang.mkdir()
        (lang / "ja.json").write_text("{}", encoding="utf-8")
        codes = [code for code, _ in i18n.available_languages(self._tmp.name)]
        self.assertEqual(codes, ["th", "en", "ja"])

    def test_available_languages_shows_lang_name(self) -> None:
        lang = Path(self._tmp.name) / "lang"
        lang.mkdir()
        (lang / "ja.json").write_text(
            json.dumps({"_lang_name": "日本語", "main.add_group": "グループ追加"}, ensure_ascii=False),
            encoding="utf-8",
        )
        names = dict(i18n.available_languages(self._tmp.name))
        self.assertEqual(names["ja"], "日本語")
        self.assertEqual(names["th"], "ไทย")
        self.assertEqual(names["en"], "English")

    def test_available_languages_fallback_to_code_when_invalid(self) -> None:
        lang = Path(self._tmp.name) / "lang"
        lang.mkdir()
        (lang / "de.json").write_text("[1,2,3]", encoding="utf-8")
        names = dict(i18n.available_languages(self._tmp.name))
        self.assertEqual(names["de"], "de")


class I18nLanguageDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        i18n.setup("th")
        self._tmp.cleanup()

    def test_export_writes_json_with_all_keys(self) -> None:
        target = Path(self._tmp.name) / "ja.json"
        i18n.export_language(target, "en", self._tmp.name)
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn("main.add_group", data)
        self.assertEqual(data["main.add_group"], "Add group")

    def test_import_roundtrip_supplies_language(self) -> None:
        source = Path(self._tmp.name) / "de.json"
        source.write_text(
            json.dumps({"main.add_group": "Gruppe hinzufügen"}, ensure_ascii=False),
            encoding="utf-8",
        )
        self.assertEqual(i18n.import_language(source, self._tmp.name), "de")
        i18n.setup("de", self._tmp.name)
        self.assertEqual(i18n.tr("main.add_group"), "Gruppe hinzufügen")

    def test_invalid_import_rejected(self) -> None:
        source = Path(self._tmp.name) / "bad.json"
        source.write_text("[1,2,3]", encoding="utf-8")
        self.assertIsNone(i18n.import_language(source, self._tmp.name))


class SettingsLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_default_language_thai(self) -> None:
        self.assertEqual(self.settings.get_language(), "th")

    def test_set_language_persists(self) -> None:
        self.settings.set_language("en")
        self.assertEqual(Settings(self._tmp.name).get_language(), "en")


class I18nGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _init_qapp()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        setup("th", self._tmp.name)

    def tearDown(self) -> None:
        setup("th")
        self._tmp.cleanup()

    def test_english_editor_button_text(self) -> None:
        from PySide6.QtWidgets import QLabel, QPushButton

        from taskbargroups.gui.group_editor import GroupEditor

        setup("en", self._tmp.name)
        editor = GroupEditor(None, None)
        labels = [b.text() for b in editor.findChildren(QPushButton)]
        self.assertIn("From system...", labels)
        self.assertIn("Choose icon...", labels)
        label_texts = [l.text() for l in editor.findChildren(QLabel)]
        self.assertIn("Group name", label_texts)

    def test_user_language_editor_button_text(self) -> None:
        from PySide6.QtWidgets import QPushButton

        from taskbargroups.gui.group_editor import GroupEditor

        lang = Path(self._tmp.name) / "lang"
        lang.mkdir()
        (lang / "ja.json").write_text(
            json.dumps({"editor.choose_system": "システムから..."}, ensure_ascii=False),
            encoding="utf-8",
        )
        setup("ja", self._tmp.name)
        editor = GroupEditor(None, None)
        labels = [b.text() for b in editor.findChildren(QPushButton)]
        self.assertIn("システムから...", labels)


class LanguageAssetTests(unittest.TestCase):
    """ตรวจ asset ภาษาใน repo (packaging/lang/<code>.json) — ต้นแบบให้ผู้ใช้ติดตั้งเอง."""

    def setUp(self) -> None:
        self._assets = Path(__file__).resolve().parents[1] / "packaging" / "lang"

    def test_ja_asset_full_translation(self) -> None:
        path = self._assets / "ja.json"
        if not path.is_file():
            self.skipTest("packaging/lang/ja.json ยังไม่สร้าง")
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in i18n.TH:
            self.assertIn(key, data, f"asset ขาดคีย์ {key}")
        self.assertNotIn("_lang_name", i18n.TH)
        self.assertEqual(data["_lang_name"], "日本語")
        self.assertTrue(
            all(isinstance(v, str) for v in data.values()), "ค่าต้องเป็น str ทั้งหมด"
        )


if __name__ == "__main__":
    unittest.main()