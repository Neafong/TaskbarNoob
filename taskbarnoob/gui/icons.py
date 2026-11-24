"""ตัวช่วยแปลง shortcut/กลุ่ม เป็น QIcon."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QFileIconProvider

from taskbarnoob.core import icons as core_icons
from taskbarnoob.core.models import Group, Shortcut
from taskbarnoob.core.paths import app_icon_path
from taskbarnoob.core.storage import ConfigStore

_APP_ICON_SIZES = (16, 22, 24, 32, 48, 64, 128, 256)

_provider = QFileIconProvider()
_FALLBACK = "application-x-executable"
_PROVIDER_ICON_CACHE_DIRNAME = core_icons.PROVIDER_ICON_CACHE_DIRNAME

# นามสกุลที่ให้ QFileIconProvider ดึงไอคอนระบบให้ (Windows/macOS)
# — core ดึงให้ไม่ได้ (ไม่ใช่ไฟล์รูป) แต่ Qt อ่านไอคอนฝังของ OS ได้
_PROVIDER_SUFFIXES = frozenset(
    {".exe", ".lnk", ".bat", ".cmd", ".app", ".command"}
)
_CACHEABLE_PROVIDER_SUFFIXES = _PROVIDER_SUFFIXES | frozenset({".ico", ".dll", ".url"})


def _smooth_scaled_pixmap(source: QPixmap, size: int) -> QPixmap:
    """ย่อ QPixmap แบบ step-halving (mipmap) เพื่อไม่ให้ขอบวงกลมหยักเมื่อย่อมากกว่า 2 เท่า."""
    from PySide6.QtCore import Qt

    cur = source
    while cur.width() > size * 2 and cur.height() > size * 2:
        cur = cur.scaled(
            cur.width() // 2,
            cur.height() // 2,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
    if cur.width() == size and cur.height() == size:
        return cur
    return cur.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def app_window_icon(path: Path | None = None) -> QIcon:
    """สร้าง QIcon หลายขนาด (16–256px) ให้ X11/Cinnamon/Windows เลือกขนาดที่คมเนียนที่สุด.

    ถ้าส่ง `QIcon(str(png_256))` ตรงๆ Qt จะส่งเฉพาะ 256x256 ใน `_NET_WM_ICON`
    แล้ว panel/titlebar ย่อรวดเดียว 8–10 เท่า → ขอบวงกลมหยัก.
    """
    target = path if path is not None else app_icon_path()
    if target is None or not target.is_file():
        return QIcon()
    base = QPixmap(str(target))
    if base.isNull():
        return QIcon(str(target))
    icon = QIcon()
    for size in _APP_ICON_SIZES:
        icon.addPixmap(_smooth_scaled_pixmap(base, size))
    return icon


def _from_file(path: Path) -> QIcon | None:
    """โหลดไอคอนจากไฟล์ — ใช้ QPixmap ไม่ใช่ QIcon(path).

    QIcon(str(path)) cache ตาม path → เปลี่ยนไอคอนแล้ว Qt ยังโชว์ของเก่า
    (path เดิม `group_icon.png` แต่เนื้อไฟล์เปลี่ยน) — QPixmap โหลดใหม่ทุกครั้ง

    ยกเว้น .ico: QPixmap โหลดได้แค่ขนาดเล็กสุด → ใช้ QIcon(str(path)) เพื่อ
    โหลดทุกขนาด (multi-res) — .ico มี hashed filename แล้วจึงไม่มีปัญหา cache
    """
    if not path.is_file():
        return None
    if path.suffix.lower() in (".exe", ".lnk", ".dll", ".bat", ".cmd"):
        return None
    if path.suffix.lower() == ".ico":
        icon = QIcon(str(path))
        return icon if not icon.isNull() else None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return QIcon(pixmap)


def _provider_icon(target: str) -> QIcon | None:
    """ไอคอนจาก OS ผ่าน QFileIconProvider."""
    path = Path((target or "").strip())
    if sys.platform in ("win32", "darwin"):
        if path.suffix.lower() not in _PROVIDER_SUFFIXES or not path.is_file():
            return None
    else:
        if not path.exists():
            return None
    icon = _provider.icon(QFileInfo(str(path)))
    return icon if not icon.isNull() else None


def _lnk_icon_source(lnk: Path) -> tuple[str, int] | None:
    """หาไฟล์จริงที่เก็บไอคอนของ `.lnk` (IconLocation ถ้าตั้งเอง → ไม่งั้น Target)."""
    from taskbarnoob.core.platform import win32 as core_win32
    from taskbarnoob.core.platform.win32 import com as win32_com

    loc = win32_com.read_icon_location(lnk)
    if loc:
        icon_path, index = loc
        # IconLocation อาจมีตัวแปรสภาพแวดล้อม เช่น %windir%\system32\app.exe
        expanded = Path(os.path.expandvars(icon_path)) if icon_path else None
        if expanded is not None and expanded.is_file():
            return str(expanded), index
    target = core_win32.read_lnk_target(lnk)
    if target and Path(target).is_file():
        return target, 0
    return None


def _url_icon_source(url: Path) -> str | None:
    """อ่าน `IconFile=` จากไฟล์ .url (Internet shortcut)."""
    try:
        text = url.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("iconfile="):
            value = stripped[len("iconfile="):].strip()
            if value:
                return os.path.expandvars(value)
    return None


def _appsfolder_icon_png(aumid: str, dest: Path, size: int) -> Path | None:
    """สกัดไอคอนแอป MSIX/Store ผ่าน shell:AppsFolder\\<aumid> เป็น PNG."""
    import ctypes
    from ctypes import wintypes
    from taskbarnoob.core.platform.win32 import com as win32_com

    hbm = win32_com.extract_appsfolder_hbitmap(aumid, size)
    if not hbm:
        return None
    gdi32 = ctypes.windll.gdi32
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    try:
        image = QImage.fromHBITMAP(hbm)
        if image.isNull():
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(dest), "PNG"):
            return None
        return dest
    finally:
        gdi32.DeleteObject(wintypes.HGDIOBJ(hbm))


def _extract_icon_index_png(
    icon_path: str, index: int, dest: Path, size: int
) -> Path | None:
    """สกัดไอคอนตาม (path, index) ด้วย SHDefExtractIconW เป็น PNG ความละเอียดสูง."""
    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.windll.shell32
    shell32.SHDefExtractIconW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.POINTER(wintypes.HICON),
        ctypes.POINTER(wintypes.HICON),
        ctypes.c_uint,
    ]
    shell32.SHDefExtractIconW.restype = ctypes.c_long
    user32 = ctypes.windll.user32
    large = wintypes.HICON()
    small = wintypes.HICON()
    hr = shell32.SHDefExtractIconW(
        icon_path,
        index,
        0,
        ctypes.byref(large),
        ctypes.byref(small),
        (size << 16) | size,
    )
    try:
        if hr != 0 or not large.value:
            return None
        image = QImage.fromHICON(large.value)
        if image.isNull():
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(dest), "PNG"):
            return None
        return dest
    finally:
        if large.value:
            user32.DestroyIcon(large.value)
        if small.value:
            user32.DestroyIcon(small.value)


def extract_dll_icon_png(
    dll_path: Path, index: int, dest: Path, size: int = 256
) -> Path | None:
    """สกัดไอคอนจาก DLL/EXE ของ Windows ตาม index เป็น PNG."""
    if sys.platform != "win32" or not dll_path.is_file():
        return None
    return _extract_icon_index_png(str(dll_path), index, dest, size)


def list_dll_icons(dll_path: Path) -> list[tuple[int, QIcon]]:
    """ดึงรายการ (index, QIcon) ทั้งหมดจาก DLL ไอคอนระบบของ Windows แบบรวดเร็ว."""
    if sys.platform != "win32" or not dll_path.is_file():
        return []
    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    count = int(shell32.ExtractIconExW(str(dll_path), -1, None, None, 0))
    if count <= 0:
        return []
    handles = (wintypes.HICON * count)()
    got = int(shell32.ExtractIconExW(str(dll_path), 0, handles, None, count))
    result: list[tuple[int, QIcon]] = []
    for idx in range(got):
        h = handles[idx]
        if not h:
            continue
        try:
            image = QImage.fromHICON(h)
            if not image.isNull():
                result.append((idx, QIcon(QPixmap.fromImage(image))))
        finally:
            user32.DestroyIcon(h)
    return result


def _shell_icon_png(source: Path, dest: Path, size: int) -> Path | None:
    """สกัดไอคอนด้วย shell API ของ Windows (ความละเอียดสูง ไม่มี overlay ลูกศร)."""
    from taskbarnoob.core.platform.win32 import com as win32_com

    icon_path, index = str(source), 0
    if source.suffix.lower() == ".lnk":
        resolved = _lnk_icon_source(source)
        if resolved is None:
            return None
        icon_path, index = resolved
    elif source.suffix.lower() == ".url":
        resolved = _url_icon_source(source)
        if resolved is None or not Path(resolved).is_file():
            steam_img = core_icons.icon_from_steam_shortcut(source)
            if steam_img is not None and steam_img.is_file():
                pixmap = QPixmap(str(steam_img))
                if not pixmap.isNull():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if pixmap.save(str(dest), "PNG"):
                        return dest
            return None
        icon_path, index = resolved, 0
    # แอป MSIX/WindowsApps (เช่น Affinity) เป็น 0-byte AppExecutionAlias
    # ไม่มี PE resource ในตัว → อ่าน reparse point ไปดึงไอคอนจาก AppsFolder หรือ target exe จริง
    if Path(icon_path).suffix.lower() == ".exe":
        app_link = win32_com.read_app_exec_link(Path(icon_path))
        if app_link is not None:
            aumid, target_exe = app_link
            png = _appsfolder_icon_png(aumid, dest, size)
            if png is not None:
                return png
            if target_exe and Path(target_exe).is_file():
                icon_path = target_exe
    if not Path(icon_path).is_file():
        return None
    return _extract_icon_index_png(icon_path, index, dest, size)


def extract_os_icon_png(source: Path, dest: Path, size: int = 256) -> Path | None:
    """สกัดไอคอนจากไฟล์ OS (.exe/.lnk/.dll/โฟลเดอร์) เป็น PNG — คืน path (None ถ้าไม่ได้).

    Windows: shell API (SHDefExtractIconW) → ได้ความละเอียดสูงสุดที่ฝังไว้ (เช่น 256px)
    และ**ไม่มีลูกศร shortcut** — ต้อง resolve `.lnk` ไปหาไฟล์ไอคอนจริงก่อน
    (QFileIconProvider เดิมได้แค่ ~128px และมี overlay ของ .lnk ติดมาด้วย)
    OS อื่น/ดึงไม่ได้ → fallback QFileIconProvider (พฤติกรรมเดิม).
    """
    if sys.platform == "win32":
        png = _shell_icon_png(source, dest, size)
        if png is not None:
            return png
    icon = _provider.icon(QFileInfo(str(source)))
    if icon.isNull():
        return None
    pixmap = icon.pixmap(size, size)
    if pixmap.isNull():
        return None
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # เพิ่ม anti-aliasing buffer ก่อน save PNG เพื่อลด Moire artifacts ที่ขอบไอคอน
        # (QPixmap.save() จะทำ anti-alias อัตโนมัติถ้าเปิด smoothing hint แล้ว)
        if not pixmap.save(str(dest), "PNG"):
            return None
    except (OSError, RuntimeError):
        return None
    return dest


def _provider_png(source: Path, dest: Path, size: int = 256) -> Path | None:
    """สกัดไอคอนที่ฝังในไฟล์ของ OS (.exe/.lnk/.dll) ออกมาเป็น PNG."""
    return extract_os_icon_png(source, dest, size)


def cached_provider_png(source: Path, base: Path, size: int = 256) -> Path | None:
    """สกัดไอคอนจากไฟล์ OS แล้วแคชเป็น PNG (ข้ามถ้าแคชยังใหม่กว่าไฟล์ต้นทาง)."""
    try:
        mtime = source.stat().st_mtime
    except OSError:
        return None
    digest = hashlib.sha1(f"{source}|{int(mtime)}".encode("utf-8")).hexdigest()[:16]
    dest = base / f"{digest}.png"
    if dest.is_file():
        try:
            if dest.stat().st_mtime >= mtime:
                return dest
        except OSError:
            pass
    return _provider_png(source, dest, size)


_cached_provider_png = cached_provider_png


def shortcut_icon(shortcut: Shortcut, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, shortcut.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    target = shortcut.target.strip()
    if target:
        icon = _from_file(Path(target))
        if icon is not None and not icon.isNull():
            return icon
        # Windows: .url/.lnk → สกัดไอคอนผ่าน shell API (หรือ Steam librarycache)
        if (
            sys.platform == "win32"
            and Path(target).suffix.lower() in (".url", ".lnk")
            and Path(target).is_file()
        ):
            cache = Path(tempfile.gettempdir()) / _PROVIDER_ICON_CACHE_DIRNAME
            png = cached_provider_png(Path(target), cache)
            if png is not None:
                icon = _from_file(png)
                if icon is not None and not icon.isNull():
                    return icon
        resolved = core_icons.resolve_icon_source(target)
        if resolved is not None:
            icon = _from_file(resolved)
            if icon is not None and not icon.isNull():
                return icon
        icon = _provider_icon(target)
        if icon is not None:
            return icon
    return QIcon.fromTheme(_FALLBACK)


def group_icon(group: Group, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, group.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    fallback = _from_file(default_group_icon_file(store))
    if fallback is not None:
        return fallback
    return QIcon.fromTheme("folder")


def default_group_icon_file(store: ConfigStore) -> Path | None:
    """ไฟล์ไอคอนสำรองของกลุ่ม — ดึงไอคอนโฟลเดอร์จากระบบมาแคชไว้ครั้งเดียว.

    ต้องเป็น **ไฟล์จริง** ไม่ใช่ QIcon เปล่า เพราะ `.lnk` บน Windows รับได้แค่พาธ
    (IconLocation) — ถ้าไม่มีไฟล์ ปุ่มบน taskbar จะโชว์ไอคอน shortcut ทั่วไปของ Windows

    เก็บใน `config/cache/` (ไม่ใช่ `config/groups/`) เพื่อไม่ให้สับสนกับกลุ่มจริง
    """
    cache = store.cache_dir() / "icons"
    png = cache / "default.png"
    if png.is_file():
        return png
    source = cache if cache.is_dir() else store.groups_dir
    icon = _provider.icon(QFileInfo(str(source if source.is_dir() else Path.home())))
    pixmap = icon.pixmap(256, 256)
    if pixmap.isNull():
        return None
    try:
        cache.mkdir(parents=True, exist_ok=True)
        if not pixmap.save(str(png), "PNG"):
            return None
    except (OSError, RuntimeError):
        return None
    return png


def cache_provider_icon(
    store: ConfigStore,
    dir_name: str,
    target: str | None,
    stem: str,
    size: int = 256,
) -> str | None:
    """แคชไอคอนจาก OS ลง icons/ ของกลุ่ม คืน path สัมพัทธ์ (None ถ้าทำไม่ได้).

    ใช้ตอนบันทึก เผื่อไฟล์พวก .exe/.lnk ที่ core แคชให้ไม่ได้ — จะได้พกพา config
    ข้ามเครื่องได้เหมือนไอคอนชนิดอื่น.
    """
    path = Path((target or "").strip())
    if path.suffix.lower() not in _CACHEABLE_PROVIDER_SUFFIXES or not path.is_file():
        return None
    icons_dir = store.icons_dir(dir_name)
    try:
        icons_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    safe = core_icons.safe_stem(stem or path.stem or "icon")
    for old in icons_dir.glob(f"{safe}.*"):
        try:
            old.unlink()
        except OSError:
            pass
    dest = icons_dir / f"{safe}.png"
    if extract_os_icon_png(path, dest, size) is None:
        return None
    return f"{core_icons.ICONS_DIR_NAME}/{dest.name}"
