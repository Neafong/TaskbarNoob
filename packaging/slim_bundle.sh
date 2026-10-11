#!/usr/bin/env bash
# ตัดไฟล์ Qt/PySide6 ที่ TaskbarNoob ไม่ได้ใช้ออกจาก PyInstaller bundle (ลดขนาด)
# ใช้: bash packaging/slim_bundle.sh <bundle_dir>
#   bundle_dir = build/pyinstaller/dist/taskbargroups
# ปลอดภัย: ลบเฉพาะโมดูลที่แอปไม่ import (QML/Quick/Pdf/VirtualKeyboard) + ปลั๊กอินที่ไม่ใช้
set -euo pipefail

BUNDLE="${1:?ต้องระบุ bundle dir}"
QT="$BUNDLE/_internal/PySide6/Qt"
[[ -d "$QT" ]] || exit 0

# 1) Qt libs ที่ไม่ใช้ (ไม่มี QML/Quick/Pdf/VirtualKeyboard ในแอป)
rm -f "$QT"/lib/libQt6Quick*.so* \
      "$QT"/lib/libQt6Qml*.so* \
      "$QT"/lib/libQt6Pdf*.so* \
      "$QT"/lib/libQt6VirtualKeyboard*.so* \
      "$QT"/lib/libQt6EglFSDeviceIntegration*.so* \
      "$QT"/lib/libQt6EglFsKmsSupport*.so*

# 2) ปลั๊กอินแพลตฟอร์ม/อื่นๆ ที่ไม่ใช้บนเดสก์ท็อป X11
rm -f "$QT"/plugins/platforms/libqlinuxfb.so \
      "$QT"/plugins/platforms/libqvkkhrdisplay.so \
      "$QT"/plugins/platforms/libqvnc.so \
      "$QT"/plugins/platforms/libqeglfs.so \
      "$QT"/plugins/platforms/libqminimalegl.so
rm -rf "$QT"/plugins/egldeviceintegrations
rm -f "$QT"/plugins/generic/libqevdev*.so

# 3) TLS (แอปใช้แค่ local socket ไม่ใช้เน็ต/TLS)
rm -rf "$QT"/plugins/tls

# 4) imageformats: เก็บ png/gif/ico/jpeg/svg · ตัด tiff/webp/tga/wbmp/icns/pdf
rm -f "$QT"/plugins/imageformats/libqtiff.so \
      "$QT"/plugins/imageformats/libqwebp.so \
      "$QT"/plugins/imageformats/libqtga.so \
      "$QT"/plugins/imageformats/libqwbmp.so \
      "$QT"/plugins/imageformats/libqicns.so \
      "$QT"/plugins/imageformats/libqpdf.so

# 5) คำแปล Qt: เก็บเฉพาะไทย (ที่เหลือเป็นอังกฤษ built-in อยู่แล้ว)
if [[ -d "$QT"/translations ]]; then
  find "$QT"/translations -type f ! -name '*_th.qm' -delete
fi

echo "slim: ตัดไฟล์ Qt ที่ไม่ใช้ออกจาก $BUNDLE แล้ว"
