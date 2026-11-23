# สร้าง TaskbarNoob Portable ฝั่ง Windows (รันบนเครื่อง Windows)
# ใช้: powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
# ผลลัพธ์: dist\TaskbarNoob\  (คัดลอกทั้งโฟลเดอร์ไปใช้งานได้เลย — config อยู่ข้าง exe)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PY = Join-Path $ROOT ".venv-win\Scripts\python.exe"
$APP_ID = "taskbarnoob"
$EXE_NAME = "TaskbarNoob"   # ชื่อแอปที่ผู้ใช้เห็น (APP_ID คงไว้เพื่อ .lnk/.desktop เดิมไม่พัง)
$BUILD = Join-Path $ROOT "build\win"
$DIST = Join-Path $ROOT "dist"
$OUTDIR = Join-Path $DIST "TaskbarNoob"
$ICON = Join-Path $ROOT "packaging\win\$APP_ID.png"
$EXE_ICO = Join-Path $ROOT "packaging\win\taskbarnoob.ico"   # ไอค่อนโลโก้ TG (ต้องเป็น .ico)

# สร้าง .ico + .png จากโลโก้ SVG เสมอ (multi-res PNG-in-ICO) — ไม่งั้น ICO เก่า (single-res) จะถูกใช้ต่อ
Write-Host "สร้างไอคอน exe จาก Logo TG.svg (multi-res)..."
$env:QT_QPA_PLATFORM = "offscreen"
& $PY packaging\render_icon.py (Join-Path $ROOT "packaging\assets\Logo TG.svg") $EXE_ICO
& $PY packaging\render_icon.py (Join-Path $ROOT "packaging\assets\Logo TG.svg") $ICON 256
if (!(Test-Path $ICON)) {
    $ICON = Join-Path $ROOT "packaging\appimage\$APP_ID.png"
}
if (!(Test-Path $EXE_ICO)) {
    $EXE_ICO = ""   # สร้างไม่ได้ = ไม่ใส่ --icon (ไม่ทำให้ build พัง)
}

if (!(Test-Path $PY)) {
    Write-Host "สร้าง venv ใหม่..."
    py -3.11 -m venv (Join-Path $ROOT ".venv-win")
}
& $PY -c "import PySide6, PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $PY -m pip install --quiet PySide6 pyinstaller
}

Write-Host "[1/2] PyInstaller build (portable, one-dir)..."
$pyArgs = @(
    "--noconfirm", "--clean",
    "--name", $EXE_NAME,
    "--paths", $ROOT,
    "--collect-submodules", "taskbarnoob",
    "--add-data", "$ICON;taskbarnoob/assets",
    "--add-data", "$ROOT\packaging\assets\icons;taskbarnoob/assets/icons",
    "--add-data", "$ROOT\packaging\lang;taskbarnoob/assets/lang",
    "--distpath", "$BUILD\dist",
    "--workpath", "$BUILD\build",
    "--specpath", "$BUILD",
    "--windowed"
)
if ($EXE_ICO) { $pyArgs += @("--icon", $EXE_ICO) }
$pyArgs += (Join-Path $ROOT "packaging\entrypoint.py")
& $PY -m PyInstaller @pyArgs

Write-Host "[2/2] จัดโฟลเดอร์ portable..."
if (Test-Path $OUTDIR) { Remove-Item -Recurse -Force $OUTDIR }
New-Item -ItemType Directory -Force $OUTDIR | Out-Null
Copy-Item -Recurse -Force (Join-Path $BUILD "dist\$EXE_NAME\*") $OUTDIR
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
