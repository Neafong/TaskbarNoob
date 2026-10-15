# สร้าง TaskbarNoob Portable ฝั่ง Windows (รันบนเครื่อง Windows)
# ใช้: powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
# ผลลัพธ์: dist\TaskbarNoob\  (คัดลอกทั้งโฟลเดอร์ไปใช้งานได้เลย — config อยู่ข้าง exe)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PY = Join-Path $ROOT ".venv-win\Scripts\python.exe"
$APP_ID = "taskbargroups"
$BUILD = Join-Path $ROOT "build\win"
$DIST = Join-Path $ROOT "dist"
$OUTDIR = Join-Path $DIST "TaskbarNoob"
$ICON = Join-Path $ROOT "packaging\appimage\$APP_ID.png"

if (!(Test-Path $PY)) {
    Write-Host "สร้าง venv ใหม่..."
    py -3.11 -m venv (Join-Path $ROOT ".venv-win")
}
& $PY -m pip install --quiet PySide6 pyinstaller

Write-Host "[1/2] PyInstaller build (portable, one-dir)..."
& $PY -m PyInstaller `
    --noconfirm --clean `
    --name $APP_ID `
    --paths $ROOT `
    --collect-submodules taskbargroups `
    --add-data "$ICON;taskbargroups/assets" `
    --add-data "$ROOT\packaging\assets\icons;taskbargroups/assets/icons" `
    --distpath "$BUILD\dist" `
    --workpath "$BUILD\build" `
    --specpath "$BUILD" `
    --windowed `
    (Join-Path $ROOT "packaging\entrypoint.py")

Write-Host "[2/2] จัดโฟลเดอร์ portable..."
if (Test-Path $OUTDIR) { Remove-Item -Recurse -Force $OUTDIR }
New-Item -ItemType Directory -Force $OUTDIR | Out-Null
Copy-Item -Recurse -Force (Join-Path $BUILD "dist\$APP_ID\*") $OUTDIR
Copy-Item -Force $ICON (Join-Path $OUTDIR "$APP_ID.png")
@"
TaskbarNoob Portable (Windows)
=============================
- รัน TaskbarNoob.exe ได้เลย — config อยู่ในโฟลเดอร์ config ข้าง exe
- ย้ายโฟลเดอร์ได้ แต่ต้องกด "ติดตั้ง launcher" ใหม่ทุกกลุ่ม (.lnk เก็บ path สัมบูรณ์)
- เทสต์: TaskbarNoob.exe --list
"@ | Out-File -Encoding utf8 (Join-Path $OUTDIR "README-Portable.txt")

Write-Host "เสร็จแล้ว: $OUTDIR"
Get-ChildItem $OUTDIR | Format-Table Name, Length
