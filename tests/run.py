"""ตัวรันเทสต์ของโปรเจกต์ (กัน segfault ตอน Qt ปิดตัว).

ใช้: .venv/bin/python tests/run.py

หมายเหตุ: `python -m unittest discover -s tests` ให้ผลเทสต์เหมือนกัน แต่ตอนโปรเซสปิดตัว
PySide6 6.12 จะ segfault ใน `destroyQCoreApplication()` (บั๊กฝั่ง Qt ไม่เกี่ยวกับโค้ดแอป)
ตัวรันนี้จึงเรียก `os._exit()` หลังสรุปผล เพื่อข้ามการปิดตัวที่พังนั้น
"""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    suite = unittest.TestLoader().discover(
        os.path.join(ROOT, "tests"), top_level_dir=ROOT
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.stdout.flush()
    sys.stderr.flush()
    # ข้าม Py_FinalizeEx ที่ทำให้ PySide6 crash ตอนปิดโปรเซส
    os._exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
