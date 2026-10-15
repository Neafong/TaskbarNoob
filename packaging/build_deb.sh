#!/usr/bin/env bash
# สร้าง .deb จาก PyInstaller bundle เดียวกับ AppImage
set -euo pipefail
umask 022

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
APP_ID="taskbargroups"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
BUNDLE="$BUILD/pyinstaller/dist/${APP_ID}"

if [[ ! -x "$PY" ]]; then
  echo "ไม่พบ $PY (ต้องมี .venv)"; exit 1
fi

VERSION="$("$PY" -c "import taskbargroups; print(taskbargroups.__version__)")"
ARCH="amd64"
SVG_ICON="$ROOT/packaging/appimage/${APP_ID}.svg"
PNG_ICON="$ROOT/packaging/appimage/${APP_ID}.png"
if [[ -f "$SVG_ICON" ]]; then
  QT_QPA_PLATFORM=offscreen "$PY" "$ROOT/packaging/render_icon.py" "$SVG_ICON" "$PNG_ICON" 256 >/dev/null
elif [[ ! -f "$PNG_ICON" ]]; then
  QT_QPA_PLATFORM=offscreen "$PY" "$ROOT/packaging/make_icon.py" "$PNG_ICON" 256
fi
# ต้องสเตจบน filesystem ที่รองรับสิทธิ์ (repo อยู่บน fuseblk ที่ chmod ไม่ติด)
STAGE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/tbg-deb.XXXXXX")"
STAGE="$STAGE_ROOT/${APP_ID}_${VERSION}_${ARCH}"
trap 'rm -rf "$STAGE_ROOT"' EXIT
OUT="$DIST/${APP_ID}_${VERSION}_${ARCH}.deb"

if [[ ! -x "$BUNDLE/${APP_ID}" ]]; then
  if ! "$PY" -m PyInstaller --version >/dev/null 2>&1; then
    "$PY" -m pip install --quiet pyinstaller
  fi
  echo "[1/3] PyInstaller build..."
  "$PY" -m PyInstaller \
    --noconfirm --clean \
    --name "$APP_ID" \
    --paths "$ROOT" \
    --collect-submodules taskbargroups \
    --add-data "$ROOT/packaging/appimage/${APP_ID}.png:taskbargroups/assets" \
    --add-data "$ROOT/packaging/assets/icons:taskbargroups/assets/icons" \
    --distpath "$BUILD/pyinstaller/dist" \
    --workpath "$BUILD/pyinstaller/build" \
    --specpath "$BUILD/pyinstaller" \
    "$ROOT/packaging/entrypoint.py"
fi

bash "$ROOT/packaging/slim_bundle.sh" "$BUNDLE"

echo "[2/3] จัดโครง .deb..."
rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/lib/${APP_ID}" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps" \
         "$STAGE/usr/share/metainfo"
cp -a "$BUNDLE/." "$STAGE/usr/lib/${APP_ID}/"

cat > "$STAGE/usr/bin/${APP_ID}" <<'WRAP'
#!/bin/sh
exec "/usr/lib/taskbargroups/taskbargroups" "$@"
WRAP
chmod +x "$STAGE/usr/bin/${APP_ID}"

cp "$ROOT/packaging/appimage/${APP_ID}.desktop" "$STAGE/usr/share/applications/"
cp "$ROOT/packaging/appimage/${APP_ID}.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/"
cp "$ROOT/packaging/appimage/${APP_ID}.appdata.xml" "$STAGE/usr/share/metainfo/"

SIZE="$(du -sk "$STAGE/usr" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: ${APP_ID}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libc6, libstdc++6, libgl1, libglib2.0-0, libxkbcommon0, libxcb-cursor0, libfontconfig1, libdbus-1-3, libxcb1
Installed-Size: ${SIZE}
Maintainer: TaskbarNoob <noreply@example.com>
Description: จัดกลุ่ม shortcut แล้วเปิดทั้งกลุ่มด้วยคลิกเดียว
 TaskbarNoob ช่วยจัดกลุ่ม shortcut เป็นกลุ่ม แล้วกดครั้งเดียวเปิดได้ทั้งกลุ่ม
 เหมาะกับ Linux Mint (Cinnamon) โดยเก็บ config แบบ portable
CONTROL

echo "[3/3] สร้าง .deb..."
chmod 0755 "$STAGE" "$STAGE/DEBIAN"
mkdir -p "$DIST"
rm -f "$OUT"
fakeroot dpkg-deb --build --root-owner-group "$STAGE" "$OUT" >/dev/null
echo "เสร็จแล้ว: $OUT"
ls -lh "$OUT"
