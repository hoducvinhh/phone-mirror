@echo off
title Appcuatao

set "PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools;%PATH%"

set "PY_EXE=pythonw"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
)

"%PY_EXE%" "%~dp0appcuatao_app.py"
