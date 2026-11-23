"""สร้าง/อ่าน `.lnk` ผ่าน COM `IShellLinkW` + `IPropertyStore` (ctypes ล้วน ไม่ต้องลงอะไรเพิ่ม).

ทำไมต้องใช้ COM แทน PowerShell (`WScript.Shell`):
- PowerShell ตั้ง **AppUserModelID** ไม่ได้ · ต้องเข้าผ่าน `IPropertyStore`
- AUMID สำคัญมาก — Windows เอาปุ่มบน taskbar มาแสดงรวมกันตาม AUMID
  ถ้าทุกกลุ่มใช้ AUMID เดียวกับตัวแอป ปุ่มทุกกลุ่มจะซ้อนกันเหลือปุ่มเดียว
  (อ้างอิง: ต้นฉบับ Taskbar Groups — `ShellLink.cs` ตั้ง
   `AppUserModel_ID = "tjackenpacken.taskbarGroup.menu." + groupName`)

เขียนตามแนวเดียวกับ `ShellLink.cs` ของต้นฉบับ
"""

from __future__ import annotations

import os
import struct
import sys
import uuid
from ctypes import wintypes
from pathlib import Path

CLSID_SHELL_LINK = "00021401-0000-0000-c000-000000000046"
IID_SHELL_LINK_W = "000214f9-0000-0000-c000-000000000046"
IID_PERSIST_FILE = "0000010b-0000-0000-c000-000000000046"
IID_PROPERTY_STORE = "886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"
IID_SHELL_ITEM_IMAGE_FACTORY = "bcc18b79-ba16-442f-80c4-8a59c30c463b"

# MSIX / WindowsApps AppExecutionAlias reparse tag
_IO_REPARSE_TAG_APPEXECLINK = 0x8000001B
_FSCTL_GET_REPARSE_POINT = 0x000900A8
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_SIIGBF_BIGGERSIZEOK = 0x01
_SIIGBF_ICONONLY = 0x04

# PROPERTYKEY.AppUserModel_ID — fmtid ของ System.AppUserModel.ID, pid 5
_PKEY_AUMID_FMTID = "9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3"
_PKEY_AUMID_PID = 5
_VT_LPWSTR = 31

# vtable ของ IShellLinkW (ลำดับตาม shobjidl.h)
_GET_ICON_LOCATION = 16
_SET_PATH = 20
_SET_ARGUMENTS = 11
_SET_DESCRIPTION = 7
_SET_WORKING_DIR = 9
_SET_ICON_LOCATION = 17
# IPersistFile
_PERSIST_LOAD = 5
_PERSIST_SAVE = 6
# IPropertyStore
_PROPSTORE_GET_VALUE = 5
_PROPSTORE_SET_VALUE = 6
_PROPSTORE_COMMIT = 7


class ComError(OSError):
    """COM ล้มเหลว (หรือเรียกบน OS ที่ไม่ใช่ Windows)."""


def _types():
    """คืน (GUID, PropertyKey, PropVariant) — สร้างครั้งเดียวต่อโปรเซส."""
    import ctypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    class PropertyKey(ctypes.Structure):
        _pack_ = 4
        _fields_ = [("fmtid", GUID), ("pid", ctypes.c_uint)]

    # PROPVARIANT มีขนาด 24 ไบต์บน x64 — เก็บเป็น buffer เหมือนกันทั้งสองฝั่ง
    class PropVariant(ctypes.Structure):
        _fields_ = [
            ("vt", ctypes.c_ushort),
            ("reserved", ctypes.c_ubyte * 6),
            ("value", ctypes.c_void_p),
            ("tail", ctypes.c_ubyte * 8),
        ]

    return ctypes, GUID, PropertyKey, PropVariant


def _guid(guid_cls, text: str):
    import ctypes

    return guid_cls.from_buffer_copy(uuid.UUID(text).bytes_le)


def _ole32():
    import ctypes

    try:
        ole32 = ctypes.WinDLL("ole32")
    except (OSError, AttributeError) as exc:
        raise ComError(f"ใช้ COM ได้เฉพาะ Windows: {exc}") from exc
    # COINIT_APARTMENTTHREADED — ต้องเรียกก่อน CoCreateInstance ไม่งั้นได้ 0x800401F0
    ole32.CoInitializeEx(None, 2)
    return ole32


def _method(pointer, index, restype, *argtypes):
    """สร้าง callable จาก vtable slot ของ COM object."""
    import ctypes

    table = ctypes.cast(
        pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
    ).contents
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(table[index])


def _shell_link(ole32, guid_cls, iid_shell_link):
    import ctypes

    clsid = _guid(guid_cls, CLSID_SHELL_LINK)
    iid = _guid(guid_cls, iid_shell_link)
    obj = ctypes.c_void_p()
    # CLSCTX_INPROC_SERVER
    hr = ole32.CoCreateInstance(
        ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(obj)
    )
    if hr != 0 or not obj.value:
        raise ComError(f"CoCreateInstance(ShellLink) ล้มเหลว: 0x{hr & 0xFFFFFFFF:08X}")
    return obj


def _query_interface(ole32, pointer, guid_cls, iid_text: str):
    import ctypes

    query = _method(
        pointer, 0, ctypes.c_long, ctypes.POINTER(guid_cls), ctypes.POINTER(ctypes.c_void_p)
    )
    iid = _guid(guid_cls, iid_text)
    out = ctypes.c_void_p()
    hr = query(pointer, ctypes.byref(iid), ctypes.byref(out))
    if hr != 0 or not out.value:
        raise ComError(f"QueryInterface ล้มเหลว: 0x{hr & 0xFFFFFFFF:08X}")
    return out


def _check(hr: int, what: str) -> None:
    if hr != 0:
        raise ComError(f"{what} ล้มเหลว: 0x{hr & 0xFFFFFFFF:08X}")


def _set_aumid(props, guid_cls, key_cls, pv_cls, value: str) -> None:
    import ctypes

    key = key_cls(_guid(guid_cls, _PKEY_AUMID_FMTID), _PKEY_AUMID_PID)
    buffer = ctypes.create_unicode_buffer(value)
    variant = pv_cls()
    variant.vt = _VT_LPWSTR
    variant.value = ctypes.cast(buffer, ctypes.c_void_p).value
    set_value = _method(
        props,
        _PROPSTORE_SET_VALUE,
        ctypes.c_long,
        ctypes.POINTER(key_cls),
        ctypes.POINTER(pv_cls),
    )
    _check(set_value(props, ctypes.byref(key), ctypes.byref(variant)), "ตั้ง AUMID")
    commit = _method(props, _PROPSTORE_COMMIT, ctypes.c_long)
    _check(commit(props), "บันทึก AUMID")


def write_lnk(
    path: Path,
    target: str,
    arguments: str = "",
    workdir: str = "",
    icon_location: str = "",
    description: str = "",
    aumid: str = "",
) -> Path:
    """เขียนไฟล์ `.lnk` หนึ่งไฟล์ (คืน path ที่เขียน)."""
    import ctypes

    ctypes_, guid_cls, key_cls, pv_cls = _types()
    ole32 = _ole32()
    link = _shell_link(ole32, guid_cls, IID_SHELL_LINK_W)
    try:
        _check(
            _method(link, _SET_PATH, ctypes.c_long, wintypes.LPCWSTR)(link, target),
            "ตั้ง TargetPath",
        )
        if arguments:
            _check(
                _method(link, _SET_ARGUMENTS, ctypes.c_long, wintypes.LPCWSTR)(
                    link, arguments
                ),
                "ตั้ง Arguments",
            )
        if description:
            _check(
                _method(link, _SET_DESCRIPTION, ctypes.c_long, wintypes.LPCWSTR)(
                    link, description
                ),
                "ตั้ง Description",
            )
        if workdir:
            _check(
                _method(link, _SET_WORKING_DIR, ctypes.c_long, wintypes.LPCWSTR)(
                    link, workdir
                ),
                "ตั้ง WorkingDirectory",
            )
        if icon_location:
            _check(
                _method(
                    link,
                    _SET_ICON_LOCATION,
                    ctypes.c_long,
                    wintypes.LPCWSTR,
                    ctypes.c_int,
                )(link, icon_location, 0),
                "ตั้ง IconLocation",
            )
        if aumid:
            props = _query_interface(
                ole32, link, guid_cls, IID_PROPERTY_STORE
            )
            _set_aumid(props, guid_cls, key_cls, pv_cls, aumid)
        persist = _query_interface(ole32, link, guid_cls, IID_PERSIST_FILE)
        save = _method(
            persist, _PERSIST_SAVE, ctypes.c_long, wintypes.LPCWSTR, ctypes.c_int
        )
        _check(save(persist, str(path), 1), "บันทึกไฟล์ .lnk")
    finally:
        _method(link, 2, ctypes.c_ulong)(link)
    return path


def _open_lnk(path: Path):
    """เปิด .lnk ที่มีอยู่ → (persist_file, property_store) หรือโยน ComError."""
    import ctypes

    ctypes_, guid_cls, _key_cls, _pv_cls = _types()
    ole32 = _ole32()
    link = _shell_link(ole32, guid_cls, IID_SHELL_LINK_W)
    persist = _query_interface(ole32, link, guid_cls, IID_PERSIST_FILE)
    load = _method(persist, _PERSIST_LOAD, ctypes.c_long, wintypes.LPCWSTR, ctypes.c_uint)
    hr = load(persist, str(path), 0)
    if hr != 0:
        _method(link, 2, ctypes.c_ulong)(link)
        raise ComError(f"เปิด .lnk ไม่ได้: 0x{hr & 0xFFFFFFFF:08X}")
    props = None
    try:
        props = _query_interface(ole32, link, guid_cls, IID_PROPERTY_STORE)
    except ComError:
        pass
    return link, persist, props


def read_target(path: Path) -> str | None:
    """อ่าน TargetPath (None ถ้าอ่านไม่ได้)."""
    import ctypes

    if not path.is_file():
        return None
    link, persist, _props = _open_lnk(path)
    try:
        get_path = _method(
            link,
            3,  # GetPath
            ctypes.c_long,
            ctypes.c_wchar_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint,
        )
        buffer = ctypes.create_unicode_buffer(32768)
        _method(persist, 2, ctypes.c_ulong)(persist)
        if get_path(link, buffer, 32768, None, 0) != 0:
            return None
        return buffer.value or None
    except Exception:
        return None
    finally:
        _method(link, 2, ctypes.c_ulong)(link)


def read_arguments(path: Path) -> str | None:
    """อ่าน Arguments จาก .lnk (None ถ้าอ่านไม่ได้)."""
    import ctypes

    if not path.is_file():
        return None
    link, _persist, _props = _open_lnk(path)
    try:
        get_args = _method(link, 10, ctypes.c_long, ctypes.c_wchar_p, ctypes.c_int)
        buffer = ctypes.create_unicode_buffer(32768)
        if get_args(link, buffer, 32768) != 0:
            return None
        return buffer.value or None
    except Exception:
        return None
    finally:
        _method(link, 2, ctypes.c_ulong)(link)


def read_icon_location(path: Path) -> tuple[str, int] | None:
    """อ่าน IconLocation (path, index) จาก .lnk (None ถ้าไม่ได้ตั้ง/อ่านไม่ได้)."""
    import ctypes

    if not path.is_file():
        return None
    link, _persist, _props = _open_lnk(path)
    try:
        get_icon = _method(
            link,
            _GET_ICON_LOCATION,
            ctypes.c_long,
            ctypes.c_wchar_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
        )
        buffer = ctypes.create_unicode_buffer(32768)
        index = ctypes.c_int(0)
        if get_icon(link, buffer, 32768, ctypes.byref(index)) != 0:
            return None
        return (buffer.value, index.value) if buffer.value else None
    except Exception:
        return None
    finally:
        _method(link, 2, ctypes.c_ulong)(link)


def read_aumid(path: Path) -> str | None:
    """อ่าน AppUserModelID (None ถ้าไม่มี/อ่านไม่ได้)."""
    import ctypes

    if not path.is_file():
        return None
    link, _persist, props = _open_lnk(path)
    if props is None:
        _method(link, 2, ctypes.c_ulong)(link)
        return None
    try:
        _ctypes, guid_cls, key_cls, pv_cls = _types()
        key = key_cls(_guid(guid_cls, _PKEY_AUMID_FMTID), _PKEY_AUMID_PID)
        out = pv_cls()
        get_value = _method(
            props,
            _PROPSTORE_GET_VALUE,
            ctypes.c_long,
            ctypes.POINTER(key_cls),
            ctypes.POINTER(pv_cls),
        )
        if get_value(props, ctypes.byref(key), ctypes.byref(out)) != 0:
            return None
        return ctypes.wstring_at(out.value) if out.value else None
    except Exception:
        return None
    finally:
        _method(link, 2, ctypes.c_ulong)(link)


def parse_app_exec_link_reparse(data: bytes) -> tuple[str, str] | None:
    """แกะ (aumid, target_exe) จาก REPARSE_DATA_BUFFER ของ IO_REPARSE_TAG_APPEXECLINK."""
    if len(data) < 12:
        return None
    tag, data_len = struct.unpack_from("<IH", data, 0)
    if tag != _IO_REPARSE_TAG_APPEXECLINK or data_len < 4:
        return None
    payload = data[12 : 8 + data_len]
    payload = payload[: len(payload) - (len(payload) % 2)]
    parts = [s for s in payload.decode("utf-16-le", errors="ignore").split("\x00") if s]
    if len(parts) < 2:
        return None
    return parts[1], (parts[2] if len(parts) >= 3 else "")


def read_app_exec_link(path: Path) -> tuple[str, str] | None:
    """อ่าน (aumid, target_exe) จากไฟล์ MSIX WindowsApps alias (None ถ้าไม่ใช่)."""
    if sys.platform != "win32":
        return None
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.DeviceIoControl.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    kernel32.DeviceIoControl.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    invalid = ctypes.c_void_p(-1).value
    handle = kernel32.CreateFileW(
        str(path),
        0,
        7,  # FILE_SHARE_READ | WRITE | DELETE
        None,
        3,  # OPEN_EXISTING
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if not handle or handle == invalid:
        return None
    try:
        buf = ctypes.create_string_buffer(16384)
        returned = wintypes.DWORD(0)
        ok = kernel32.DeviceIoControl(
            handle,
            _FSCTL_GET_REPARSE_POINT,
            None,
            0,
            buf,
            len(buf),
            ctypes.byref(returned),
            None,
        )
        if not ok or returned.value < 12:
            return None
        return parse_app_exec_link_reparse(buf.raw[: returned.value])
    finally:
        kernel32.CloseHandle(handle)


def extract_appsfolder_hbitmap(aumid: str, size: int = 256) -> int | None:
    """ดึง HBITMAP ไอคอนของแอป MSIX/Store ผ่าน shell:AppsFolder\\<aumid>.

    ผู้เรียกต้องคืนหน่วยความจำด้วย `gdi32.DeleteObject(hbm)` เอง.
    """
    if sys.platform != "win32" or not aumid:
        return None
    import ctypes

    class _Size(ctypes.Structure):
        _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

    _ctypes, guid_cls, _key_cls, _pv_cls = _types()
    _ole32()
    shell32 = ctypes.windll.shell32
    shell32.SHCreateItemFromParsingName.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        ctypes.POINTER(guid_cls),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    shell32.SHCreateItemFromParsingName.restype = ctypes.c_long

    iid = _guid(guid_cls, IID_SHELL_ITEM_IMAGE_FACTORY)
    factory = ctypes.c_void_p()
    hr = shell32.SHCreateItemFromParsingName(
        f"shell:AppsFolder\\{aumid}",
        None,
        ctypes.byref(iid),
        ctypes.byref(factory),
    )
    if hr != 0 or not factory.value:
        return None
    try:
        get_image = _method(
            factory,
            3,  # IShellItemImageFactory::GetImage
            ctypes.c_long,
            _Size,
            ctypes.c_int,
            ctypes.POINTER(wintypes.HBITMAP),
        )
        hbm = wintypes.HBITMAP()
        for flags in (_SIIGBF_BIGGERSIZEOK | _SIIGBF_ICONONLY, 0):
            hr = get_image(factory, _Size(size, size), flags, ctypes.byref(hbm))
            if hr == 0 and hbm.value:
                return int(hbm.value)
        return None
    finally:
        _method(factory, 2, ctypes.c_ulong)(factory)
