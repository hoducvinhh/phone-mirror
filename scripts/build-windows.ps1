$ErrorActionPreference = "Stop"

$preset = "windows-vcpkg"
$buildDir = "$PSScriptRoot\..\build\windows"
New-Item -ItemType Directory -Force $buildDir | Out-Null

cmake -S "$PSScriptRoot\.." -B $buildDir -DCMAKE_BUILD_TYPE=Release
cmake --build $buildDir --config Release
