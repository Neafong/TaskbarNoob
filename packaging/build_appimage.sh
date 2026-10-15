#!/usr/bin/env bash
# สร้าง AppImage ของ TaskbarNoob (Linux x86_64)
# ต้องมี .venv ที่ติดตั้ง PySide6 แล้ว (ดู AGENTS.md)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
APP_ID="taskbargroups"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
APPDIR="$BUILD/${APP_ID}.AppDir"
OUT="$DIST/TaskbarNoob-x86_64.AppImage"
TOOLS="$BUILD/tools"
ICON="$ROOT/packaging/appimage/${APP_ID}.png"

if [[ ! -x "$PY" ]]; then
  echo "ไม่พบ $PY (ต้องมี .venv ก่อน)" >&2
  exit 1
fi

if ! "$PY" -m PyInstaller --version >/dev/null 2>&1; then
  echo "ติดตั้ง PyInstaller..."
  "$PY" -m pip install --quiet pyinstaller
fi

SVG_ICON="${ICON%.png}.svg"
if [[ -f "$SVG_ICON" ]]; then
  QT_QPA_PLATFORM=offscreen "$PY" "$ROOT/packaging/render_icon.py" "$SVG_ICON" "$ICON" 256
elif [[ ! -f "$ICON" ]]; then
  QT_QPA_PLATFORM=offscreen "$PY" "$ROOT/packaging/make_icon.py" "$ICON" 256
fi

echo "[1/4] PyInstaller build..."
rm -rf "$BUILD/pyinstaller"
"$PY" -m PyInstaller \
  --noconfirm --clean \
  --name "$APP_ID" \
  --paths "$ROOT" \
  --collect-submodules taskbargroups \
  --add-data "$ICON:taskbargroups/assets" \
  --add-data "$ROOT/packaging/assets/icons:taskbargroups/assets/icons" \
  --distpath "$BUILD/pyinstaller/dist" \
  --workpath "$BUILD/pyinstaller/build" \
  --specpath "$BUILD/pyinstaller" \
  "$ROOT/packaging/entrypoint.py"

bash "$ROOT/packaging/slim_bundle.sh" "$BUILD/pyinstaller/dist/${APP_ID}"

echo "[2/4] จัด AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/metainfo"
cp -a "$BUILD/pyinstaller/dist/${APP_ID}/." "$APPDIR/usr/bin/"
cp "$ROOT/packaging/appimage/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
cp "$ROOT/packaging/appimage/${APP_ID}.desktop" "$APPDIR/${APP_ID}.desktop"
cp "$ROOT/packaging/appimage/${APP_ID}.desktop" "$APPDIR/usr/share/applications/"
cp "$ROOT/packaging/appimage/${APP_ID}.png" "$APPDIR/${APP_ID}.png"
cp "$ROOT/packaging/appimage/${APP_ID}.png" "$APPDIR/.DirIcon"
cp "$ROOT/packaging/appimage/${APP_ID}.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
cp "$ROOT/packaging/appimage/${APP_ID}.appdata.xml" "$APPDIR/usr/share/metainfo/"

# รวม libxcb-cursor (Qt 6.6+ ต้องใช้; เครื่องที่ไม่มีจะเปิด xcb plugin ไม่ได้)
XCB_DIR="$BUILD/tools/xcb-cursor"
if [[ ! -e "$XCB_DIR/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0" ]]; then
  rm -rf "$XCB_DIR"
  if (cd "$BUILD/tools" && apt-get download libxcb-cursor0 >/dev/null 2>&1); then
    deb="$(ls "$BUILD"/tools/libxcb-cursor0_*.deb 2>/dev/null | head -1)"
    mkdir -p "$XCB_DIR"
    dpkg-deb -x "$deb" "$XCB_DIR"
    rm -f "$deb"
  fi
fi
if [[ -e "$XCB_DIR/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0" ]]; then
  mkdir -p "$APPDIR/usr/lib"
  cp -a "$XCB_DIR"/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0* "$APPDIR/usr/lib/"
else
  echo "คำเตือน: ไม่พบ libxcb-cursor0 — เครื่องที่ไม่มีไลบรารีนี้จะเปิด GUI ไม่ได้"
fi

echo "[3/4] เตรียม appimagetool..."
mkdir -p "$TOOLS" "$DIST"
AIT="$TOOLS/appimagetool-x86_64.AppImage"
if [[ ! -x "$AIT" ]]; then
  curl -L --fail -o "$AIT" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$AIT"
fi

echo "[4/4] สร้าง AppImage..."
rm -f "$OUT"
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$AIT" --no-appstream "$APPDIR" "$OUT"
chmod +x "$OUT"
echo "เสร็จแล้ว: $OUT"
ls -lh "$OUT"
