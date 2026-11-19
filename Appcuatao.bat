@echo off
title Appcuatao

set "PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools;C:\Users\Admin\scoop\shims;%PATH%"

set "PY_EXE=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
)

"%PY_EXE%" "%~dp0launcher.py"
