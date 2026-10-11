import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from taskbargroups.core.importer import (
    GroupImportError,
    import_group,
    load_object_data,
    parse_object_data,
)
from taskbargroups.core.models import ColorMode
from taskbargroups.core.storage import ConfigStore


def make_xml(
    name: str = "Tools",
    color: str = "#1F1F1F",
    width: str = "6",
    opacity: str = "10",
    open_all: str = "false",
    shortcuts: str = "",
) -> str:
    return dedent(
        f"""\
        <Category>
          <Name>{name}</Name>
          <ColorString>{color}</ColorString>
          <allowOpenAll>{open_all}</allowOpenAll>
          <ShortcutList>
            {shortcuts}
          </ShortcutList>
          <Width>{width}</Width>
          <Opacity>{opacity}</Opacity>
        </Category>
        """
    )


def make_shortcut(
    path: str,
    name: str = "App",
    args: str = "",
    cwd: str = "",
    windows_app: str = "false",
) -> str:
    return dedent(
        f"""\
        <ProgramShortcut>
          <FilePath>{path}</FilePath>
          <isWindowsApp>{windows_app}</isWindowsApp>
          <name>{name}</name>
          <Arguments>{args}</Arguments>
          <WorkingDirectory>{cwd}</WorkingDirectory>
        </ProgramShortcut>
        """
    )


class ParseTests(unittest.TestCase):
    def test_basic_fields(self) -> None:
        xml = make_xml(
            name="My Group",
            width="4",
            opacity="30",
            open_all="true",
            shortcuts=make_shortcut(
                "C:\\Apps\\editor.exe", name="Editor", args="--new", cwd="C:\\Apps"
            ),
        )
        group = parse_object_data(xml)
        self.assertEqual(group.name, "My Group")
        self.assertEqual(group.width, 4)
        self.assertEqual(group.opacity, 30)
        self.assertTrue(group.allow_open_all)
        self.assertEqual(len(group.items), 1)
        item = group.items[0]
        self.assertEqual(item.name, "Editor")
        self.assertEqual(item.target, "C:\\Apps\\editor.exe")
        self.assertEqual(item.arguments, "--new")
        self.assertEqual(item.working_dir, "C:\\Apps")

    def test_dark_color(self) -> None:
        group = parse_object_data(make_xml(color="#1F1F1F"))
        self.assertEqual(group.color_mode, ColorMode.DARK)
        self.assertIsNone(group.custom_color)

    def test_light_color(self) -> None:
        group = parse_object_data(make_xml(color="#E6E6E6"))
        self.assertEqual(group.color_mode, ColorMode.LIGHT)
        self.assertIsNone(group.custom_color)

    def test_custom_color(self) -> None:
        group = parse_object_data(make_xml(color="#123456"))
        self.assertEqual(group.color_mode, ColorMode.CUSTOM)
        self.assertEqual(group.custom_color, "#123456")

    def test_color_accepts_lowercase_defaults(self) -> None:
        group = parse_object_data(make_xml(color="#1f1f1f"))
        self.assertEqual(group.color_mode, ColorMode.DARK)

    def test_width_and_opacity_clamped(self) -> None:
        group = parse_object_data(make_xml(width="999", opacity="500"))
        self.assertEqual(group.width, 50)
        self.assertEqual(group.opacity, 100)

    def test_missing_name_falls_back_to_stem(self) -> None:
        xml = make_xml(shortcuts=make_shortcut("C:\\Apps\\thing.exe", name=""))
        group = parse_object_data(xml)
        self.assertEqual(group.items[0].name, "thing")

    def test_invalid_xml_raises(self) -> None:
        with self.assertRaises(GroupImportError):
            parse_object_data("<Category><Name>x</Name>")

    def test_wrong_root_raises(self) -> None:
        with self.assertRaises(GroupImportError):
            parse_object_data("<NotACategory/>")

    def test_doctype_rejected(self) -> None:
        xml = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE Category [<!ENTITY x "y">]>'
            "<Category><Name>a</Name></Category>"
        )
        with self.assertRaises(GroupImportError):
            parse_object_data(xml)


class LoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_load_from_directory(self) -> None:
        (self.root / "ObjectData.xml").write_text(make_xml(name="Here"), encoding="utf-8")
        self.assertEqual(load_object_data(self.root).name, "Here")

    def test_load_missing_raises(self) -> None:
        with self.assertRaises(GroupImportError):
            load_object_data(self.root / "ObjectData.xml")


class ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = self.base / "WindowsGroup"
        self.store = ConfigStore(self.base / "config")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_source(self, xml: str, *, group_image: bool = False, icons=()) -> None:
        (self.source / "Icons").mkdir(parents=True, exist_ok=True)
        (self.source / "ObjectData.xml").write_text(xml, encoding="utf-8")
        if group_image:
            (self.source / "GroupImage.png").write_bytes(b"group-png")
        for icon_name in icons:
            (self.source / "Icons" / icon_name).write_bytes(b"icon-png")

    def test_import_missing_raises(self) -> None:
        with self.assertRaises(GroupImportError):
            import_group(self.store, self.source)

    def test_import_creates_group(self) -> None:
        xml = make_xml(name="Imported", shortcuts=make_shortcut("/usr/bin/app", name="App"))
        self._write_source(xml)
        dir_name = import_group(self.store, self.source)
        self.assertEqual(dir_name, "Imported")
        self.assertIn("Imported", self.store.list_groups())

    def test_import_group_icon(self) -> None:
        xml = make_xml(name="WithIcon")
        self._write_source(xml, group_image=True)
        dir_name = import_group(self.store, self.source)
        group = self.store.load_group(dir_name)
        self.assertEqual(group.icon, "group_icon.png")
        self.assertTrue(self.store.resolve_relative(dir_name, group.icon))

    def test_import_shortcut_icon_plain(self) -> None:
        xml = make_xml(
            name="Icons",
            shortcuts=make_shortcut("C:\\Apps\\firefox.exe", name="Firefox"),
        )
        self._write_source(xml, icons=["firefox.png"])
        dir_name = import_group(self.store, self.source)
        group = self.store.load_group(dir_name)
        self.assertTrue(group.items[0].icon.startswith("icons/"))
        self.assertTrue(
            self.store.resolve_relative(dir_name, group.items[0].icon).is_file()
        )

    def test_import_folder_icon_variant(self) -> None:
        xml = make_xml(name="Folder", shortcuts=make_shortcut("C:\\Folder", name="Stuff"))
        self._write_source(xml, icons=["Folder_FolderObjTSKGRoup.png"])
        import_group(self.store, self.source)
        group = self.store.load_group("Folder")
        self.assertIsNotNone(group.items[0].icon)

    def test_import_windows_app_icon(self) -> None:
        xml = make_xml(
            name="StoreApp",
            shortcuts=make_shortcut(
                "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
                name="Calc",
                windows_app="true",
            ),
        )
        expected = "Microsoft.WindowsCalculator8wekyb3d8bbwe!App.png"
        self._write_source(xml, icons=(expected,))
        import_group(self.store, self.source)
        group = self.store.load_group("StoreApp")
        self.assertIsNotNone(group.items[0].icon)

    def test_import_unique_name(self) -> None:
        xml = make_xml(name="Dup")
        self._write_source(xml)
        first = import_group(self.store, self.source)
        second = import_group(self.store, self.source)
        self.assertEqual(first, "Dup")
        self.assertEqual(second, "Dup (2)")


if __name__ == "__main__":
    unittest.main()
