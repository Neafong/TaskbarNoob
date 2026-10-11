import unittest

from taskbargroups.core.launcher import (
    LaunchError,
    _resolve_cwd,
    _split_arguments,
    launch,
)
from taskbargroups.core.models import Shortcut


class ArgumentTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(_split_arguments(""), [])
        self.assertEqual(_split_arguments("   "), [])

    def test_quoted(self) -> None:
        self.assertEqual(
            _split_arguments('--name "my app" --x'),
            ["--name", "my app", "--x"],
        )


class CwdTests(unittest.TestCase):
    def test_none(self) -> None:
        self.assertIsNone(_resolve_cwd(None))

    def test_missing_dir(self) -> None:
        self.assertIsNone(_resolve_cwd("/no/such/dir/xyz"))

    def test_existing_dir(self) -> None:
        self.assertEqual(_resolve_cwd("/tmp"), "/tmp")


class LaunchTests(unittest.TestCase):
    def test_empty_target_raises(self) -> None:
        with self.assertRaises(LaunchError):
            launch(Shortcut(name="x", target="   "))


if __name__ == "__main__":
    unittest.main()
