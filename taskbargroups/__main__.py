"""จุดเริ่มต้นของแอป — เปิด GUI หรือ flyout ของกลุ่ม."""

from __future__ import annotations

import argparse
import os
import sys


def _ensure_bundled_libs() -> None:
    """รันจากซอร์สบน Linux: ถ้ามีไลบรารี Qt ที่พกมาให้ re-exec พร้อม LD_LIBRARY_PATH.

    แพ็กเกจ (AppImage/.deb) จัดการไลบรารีเองอยู่แล้ว จึงข้ามเมื่อรันจากแพ็กเกจ.
    """
    if sys.platform != "linux":
        return
    if os.environ.get("APPIMAGE") or getattr(sys, "frozen", False):
        return
    if os.environ.get("TASKBARGROUPS_LIB_REEXEC"):
        return

    from taskbargroups.core.paths import bundled_lib_dirs

    current = os.environ.get("LD_LIBRARY_PATH", "")
    for directory in bundled_lib_dirs():
        if not (directory / "libxcb-cursor.so.0").exists():
            continue
        if str(directory) in current.split(os.pathsep):
            return
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = str(directory) + (
            os.pathsep + current if current else ""
        )
        env["TASKBARGROUPS_LIB_REEXEC"] = "1"
        os.execve(sys.executable, [sys.executable, "-m", "taskbargroups", *sys.argv[1:]], env)


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(
        prog="taskbargroups", description="รวบรวม shortcut เป็นกลุ่ม เปิดใช้ง่ายจาก panel"
    )
    parser.add_argument("--open", dest="open_group", metavar="GROUP", help="เปิด flyout ของกลุ่ม")
    parser.add_argument("--list", action="store_true", help="แสดงชื่อกลุ่มทั้งหมด")
    parser.add_argument(
        "--import",
        dest="import_dir",
        metavar="DIR",
        help="นำเข้ากลุ่มจากโฟลเดอร์ Taskbar Groups (Windows) ที่มี ObjectData.xml",
    )
    parsed, _unknown = parser.parse_known_args(args_list)

    if parsed.list:
        from taskbargroups.core.storage import ConfigStore

        for name in ConfigStore().list_groups():
            print(name)
        return 0

    if parsed.import_dir:
        from taskbargroups.core.importer import GroupImportError, import_group
        from taskbargroups.core.storage import ConfigStore

        try:
            dir_name = import_group(ConfigStore(), parsed.import_dir)
        except GroupImportError as exc:
            print(f"นำเข้าไม่สำเร็จ: {exc}", file=sys.stderr)
            return 1
        print(dir_name)
        return 0

    try:
        from taskbargroups.gui.main_window import run
    except ImportError as exc:
        print("ต้องติดตั้ง PySide6 ก่อน:", exc, file=sys.stderr)
        print("  python -m pip install PySide6", file=sys.stderr)
        return 1
    return run([sys.argv[0], *args_list], open_group=parsed.open_group)


if __name__ == "__main__":
    _ensure_bundled_libs()
    sys.exit(main())
