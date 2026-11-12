$ErrorActionPreference = "Stop"

$adb = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adb) {
    throw "adb is not on PATH"
}

$candidates = @(
    "$PSScriptRoot\..\build\windows\bin\Release\Appcuatao.exe",
    "$PSScriptRoot\..\build\windows\bin\Appcuatao.exe",
    "$PSScriptRoot\..\build\windows\bin\Release\App của tao.exe",
    "$PSScriptRoot\..\build\windows\bin\App của tao.exe",
    "$PSScriptRoot\..\build\windows\bin\Release\NativeMirror.exe",
    "$PSScriptRoot\..\build\windows\bin\NativeMirror.exe"
)

$exe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $exe) {
    throw "Desktop app chưa được build. Vui lòng chạy build-windows.ps1 trước."
}

Write-Host "Đang khởi chạy Appcuatao: $exe" -ForegroundColor Green
& $exe
