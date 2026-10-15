import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class LaunchLinuxDispatchTests(unittest.TestCase):
    """ไฟล์ที่รันได้ต้องรันตรง ห้ามผ่าน `gio open` (กันบั๊ก v0.2-C).

    ที่มา: default app ของระบบคือ editor (สคริปต์) / disk-mounter (AppImage)
    หรือไม่มี handler (ELF) → กด shortcut ใน flyout แล้วแอปไม่เปิด
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _make_file(self, name: str, executable: bool) -> str:
        path = Path(self._tmp.name) / name
        path.write_text("#!/bin/sh\n")
        if executable:
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
        else:
            mode = path.stat().st_mode & ~(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            path.chmod(mode)
        return str(path)

    def test_executable_file_runs_directly(self) -> None:
        target = self._make_file("app.AppImage", executable=True)
        with mock.patch("taskbargroups.core.launcher.subprocess.Popen") as popen:
            launch(Shortcut(name="a", target=target, arguments="--x"))
        popen.assert_called_once_with(
            [target, "--x"], cwd=None, start_new_session=True
        )

    def test_document_file_uses_gio_open(self) -> None:
        target = self._make_file("doc.txt", executable=False)
        with mock.patch("taskbargroups.core.launcher.subprocess.Popen") as popen:
            launch(Shortcut(name="d", target=target))
        popen.assert_called_once_with(
            ["gio", "open", target], cwd=None, start_new_session=True
        )

    def test_directory_uses_xdg_open(self) -> None:
        with mock.patch("taskbargroups.core.launcher.subprocess.Popen") as popen:
            launch(Shortcut(name="d", target=self._tmp.name))
        popen.assert_called_once_with(
            ["xdg-open", self._tmp.name], cwd=None, start_new_session=True
        )

    def test_desktop_file_uses_gio_launch(self) -> None:
        with mock.patch("taskbargroups.core.launcher.subprocess.Popen") as popen:
            launch(Shortcut(name="d", target="/tmp/whatever.desktop"))
        popen.assert_called_once_with(
            ["gio", "launch", "/tmp/whatever.desktop"],
            cwd=None,
            start_new_session=True,
        )

    def test_command_in_path_runs_directly(self) -> None:
        with mock.patch("taskbargroups.core.launcher.subprocess.Popen") as popen:
            launch(Shortcut(name="f", target="firefox"))
        popen.assert_called_once_with(
            ["firefox"], cwd=None, start_new_session=True
        )

    def test_failed_exec_raises_launch_error(self) -> None:
        target = self._make_file("broken.AppImage", executable=True)
        with mock.patch(
            "taskbargroups.core.launcher.subprocess.Popen",
            side_effect=OSError("nope"),
        ):
            with self.assertRaises(LaunchError):
                launch(Shortcut(name="b", target=target))


if __name__ == "__main__":
    unittest.main()
