"""Entry point สำหรับ PyInstaller — เรียก main() ของแพ็กเกจ."""

from __future__ import annotations

import sys

from taskbarnoob.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
