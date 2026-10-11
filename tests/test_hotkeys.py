import unittest
from unittest import mock

from taskbargroups.core import hotkeys
from taskbargroups.core.hotkeys import (
    HotkeyError,
    cinnamon_to_display,
    group_hotkeys,
    hotkey_slot,
    list_command,
    parse_binding,
    parse_gvariant_string_array,
    register_cinnamon_hotkey,
    set_binding_command,
    set_key_command,
    set_list_command,
    unregister_cinnamon_hotkey,
)


class ParseTests(unittest.TestCase):
    def test_empty_typed(self) -> None:
        self.assertEqual(parse_gvariant_string_array("@as []"), [])

    def test_empty_plain(self) -> None:
        self.assertEqual(parse_gvariant_string_array("[]"), [])

    def test_values(self) -> None:
        self.assertEqual(
            parse_gvariant_string_array("['custom0', 'custom1']"),
            ["custom0", "custom1"],
        )

    def test_invalid_raises(self) -> None:
        with self.assertRaises(HotkeyError):
            parse_gvariant_string_array("not a list")


class CommandTests(unittest.TestCase):
    def test_set_list_formats(self) -> None:
        self.assertEqual(set_list_command(["a", "b"])[-1], "['a', 'b']")

    def test_set_key_path(self) -> None:
        command = set_key_command("slot1", "binding", "<Control>g")
        self.assertIn(
            "/org/cinnamon/desktop/keybindings/custom-keybindings/slot1/", command[2]
        )
        self.assertIn("custom-keybinding:", command[2])
        self.assertNotIn("custom-keybindings:", command[2])

    def test_set_binding_is_string_array(self) -> None:
        command = set_binding_command("slot1", "<Control><Alt>g")
        self.assertEqual(command[-1], "['<Control><Alt>g']")
        self.assertEqual(command[-2], "binding")

    def test_set_key_quotes_gvariant_string(self) -> None:
        command = set_key_command("slot1", "command", '"/p/a" --open "Game"')
        self.assertEqual(command[-1], '\'"/p/a" --open "Game"\'')

    def test_set_key_escapes_quote(self) -> None:
        command = set_key_command("slot1", "name", "O'Brien")
        self.assertEqual(command[-1], "'O\\'Brien'")


class RegisterTests(unittest.TestCase):
    def test_register_sets_values_before_touching_list(self) -> None:
        calls: list = []

        def runner(command):
            calls.append(list(command))
            return "@as []" if list(command) == list_command() else ""

        register_cinnamon_hotkey("slot1", "My Group", "cmd", "<Super>g", runner=runner)
        self.assertEqual(calls[0], list_command())
        self.assertEqual([call[3] for call in calls[1:4]], ["name", "command", "binding"])
        self.assertEqual(calls[4][-1], "['slot1', '__dummy__']")
        self.assertEqual(calls[5][-1], "['slot1']")
        self.assertEqual(len(calls), 6)

    def test_register_existing_slot_still_touches(self) -> None:
        calls: list = []

        def runner(command):
            calls.append(list(command))
            return "['slot1']" if list(command) == list_command() else ""

        register_cinnamon_hotkey("slot1", "t", "c", "b", runner=runner)
        self.assertEqual(calls[4][-1], "['slot1', '__dummy__']")
        self.assertEqual(calls[5][-1], "['slot1']")
        self.assertEqual(len(calls), 6)

    def test_unregister_clears_binding_then_removes(self) -> None:
        calls: list = []

        def runner(command):
            calls.append(list(command))
            return "['slot1', 'other']" if list(command) == list_command() else ""

        unregister_cinnamon_hotkey("slot1", runner=runner)
        self.assertEqual(calls[1][:2], ["gsettings", "set"])
        self.assertEqual(calls[1][3], "binding")
        self.assertEqual(calls[1][-1], "[]")
        self.assertEqual(calls[2][-1], "['slot1', 'other', '__dummy__']")
        self.assertEqual(calls[3][-1], "['slot1', 'other']")
        self.assertEqual([call[3] for call in calls[4:7]], ["name", "command", "binding"])
        self.assertTrue(all(call[1] == "reset" for call in calls[4:7]))
        self.assertEqual(calls[7][-1], "['other', '__dummy__']")
        self.assertEqual(calls[8][-1], "['other']")

    def test_unregister_absent_slot_still_clears(self) -> None:
        calls: list = []

        def runner(command):
            calls.append(list(command))
            return "['other']" if list(command) == list_command() else ""

        unregister_cinnamon_hotkey("slot1", runner=runner)
        self.assertEqual(calls[1][3], "binding")
        self.assertEqual(calls[1][-1], "[]")
        self.assertEqual(calls[2][-1], "['other', 'slot1', '__dummy__']")
        self.assertEqual(calls[8][-1], "['other']")

    def test_touch_drops_dummy(self) -> None:
        calls: list = []

        def runner(command):
            calls.append(list(command))
            return "['slot1', '__dummy__']" if list(command) == list_command() else ""

        register_cinnamon_hotkey("slot1", "t", "c", "b", runner=runner)
        self.assertEqual(calls[4][-1], "['slot1', '__dummy__']")
        self.assertEqual(calls[5][-1], "['slot1']")


class BindingTests(unittest.TestCase):
    def test_hotkey_slot_slug(self) -> None:
        self.assertEqual(hotkey_slot("My Group"), "taskbargroups-my-group")
        self.assertEqual(hotkey_slot("Game"), "taskbargroups-game")

    def test_parse_binding_strips_quotes(self) -> None:
        self.assertEqual(parse_binding("'<Control><Alt>t'"), "<Control><Alt>t")
        self.assertEqual(parse_binding("@s ''"), "")
        self.assertEqual(parse_binding("<Super>g"), "<Super>g")

    def test_parse_binding_from_array(self) -> None:
        self.assertEqual(parse_binding("['<Control><Alt>g']"), "<Control><Alt>g")
        self.assertEqual(parse_binding("@as []"), "")
        self.assertEqual(parse_binding("['<Super>g', '<Alt>g']"), "<Super>g")

    def test_cinnamon_to_display(self) -> None:
        self.assertEqual(cinnamon_to_display("<Control><Alt>t"), "Ctrl+Alt+T")
        self.assertEqual(cinnamon_to_display("<Super>g"), "Super+G")
        self.assertEqual(cinnamon_to_display("<Primary>space"), "Ctrl+Space")
        self.assertEqual(cinnamon_to_display(""), "")

    def test_group_hotkeys_off_cinnamon_is_empty(self) -> None:
        with mock.patch.object(hotkeys, "is_cinnamon", return_value=False):
            self.assertEqual(group_hotkeys(["s"]), {})

    def test_group_hotkeys_reads_registered(self) -> None:
        def runner(command):
            if list(command) == list_command():
                return "['taskbargroups-game', 'other']"
            if "taskbargroups-game" in command[2]:
                return "['<Control><Alt>g']"
            return "@as []"

        with mock.patch.object(hotkeys, "is_cinnamon", return_value=True):
            result = group_hotkeys(
                ["taskbargroups-game", "taskbargroups-tool"], runner=runner
            )
        self.assertEqual(result, {"taskbargroups-game": "<Control><Alt>g"})


if __name__ == "__main__":
    unittest.main()
