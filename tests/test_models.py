import unittest

from taskbargroups.core.models import (
    ColorMode,
    Group,
    Shortcut,
    is_hex_color,
)


class ShortcutTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        item = Shortcut(
            name="Firefox",
            target="/usr/bin/firefox",
            working_dir="/home/me",
            arguments="--new-window",
            icon="icons/firefox.png",
        )
        self.assertEqual(Shortcut.from_dict(item.to_dict()), item)

    def test_validate_empty(self) -> None:
        errors = Shortcut(name="", target="").validate()
        self.assertEqual(len(errors), 2)

    def test_validate_too_long_name(self) -> None:
        item = Shortcut(name="x" * 28, target="/bin/true")
        self.assertTrue(any("27" in err for err in item.validate()))


class GroupTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        group = Group(
            name="Tools",
            width=4,
            color_mode=ColorMode.CUSTOM,
            custom_color="#223344",
            opacity=25,
            allow_open_all=True,
            items=[Shortcut(name="A", target="/bin/a")],
        )
        self.assertEqual(Group.from_dict(group.to_dict()), group)

    def test_from_dict_tolerant_of_garbage(self) -> None:
        group = Group.from_dict({"name": "X", "items": "nope", "color": 5})
        self.assertEqual(group.items, [])
        self.assertEqual(group.color_mode, ColorMode.DARK)

    def test_validate_ok(self) -> None:
        self.assertEqual(Group(name="Good").validate(), [])

    def test_defaults_opacity_and_icon_size(self) -> None:
        group = Group(name="G")
        self.assertEqual(group.opacity, 10)
        self.assertEqual(group.icon_size, 32)

    def test_icon_size_round_trip(self) -> None:
        group = Group(name="G", icon_size=64)
        self.assertEqual(Group.from_dict(group.to_dict()).icon_size, 64)

    def test_validate_bad_icon_size(self) -> None:
        errors = Group(name="G", icon_size=999).validate()
        self.assertTrue(any("ขนาดไอคอน" in err for err in errors))

    def test_validate_bad_width_and_opacity(self) -> None:
        errors = Group(name="G", width=0, opacity=999).validate()
        self.assertTrue(any("width" in err for err in errors))
        self.assertTrue(any("opacity" in err for err in errors))

    def test_validate_custom_color(self) -> None:
        errors = Group(
            name="G", color_mode=ColorMode.CUSTOM, custom_color="red"
        ).validate()
        self.assertTrue(any("hex" in err for err in errors))

    def test_validate_name_too_long(self) -> None:
        errors = Group(name="x" * 50).validate()
        self.assertTrue(any("49" in err for err in errors))

    def test_validate_item_errors_are_prefixed(self) -> None:
        errors = Group(name="G", items=[Shortcut(name="", target="")]).validate()
        self.assertTrue(all(err.startswith("รายการที่ 1") for err in errors))


class HexColorTests(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertTrue(is_hex_color("#fff"))
        self.assertTrue(is_hex_color("#a1B2c3"))

    def test_invalid(self) -> None:
        self.assertFalse(is_hex_color("fff"))
        self.assertFalse(is_hex_color("#gggggg"))
        self.assertFalse(is_hex_color(None))


if __name__ == "__main__":
    unittest.main()
