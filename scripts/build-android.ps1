$ErrorActionPreference = "Stop"

if (-not $env:ANDROID_SDK_ROOT) {
    if (Test-Path "$env:LOCALAPPDATA\Android\Sdk") {
        $env:ANDROID_SDK_ROOT = "$env:LOCALAPPDATA\Android\Sdk"
    } else {
        throw "ANDROID_SDK_ROOT is not set and could not be found automatically."
    }
}

$androidJar = Get-ChildItem "$env:ANDROID_SDK_ROOT\platforms\android-*\android.jar" |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $androidJar) {
    throw "No Android platform android.jar found in $env:ANDROID_SDK_ROOT\platforms"
}

$d8 = Get-ChildItem "$env:ANDROID_SDK_ROOT\build-tools\*\d8.bat" |
    Sort-Object FullName -Descending |
    Select-Object -First 1
if (-not $d8) {
    throw "d8.bat not found in $env:ANDROID_SDK_ROOT\build-tools"
}

$source = Get-ChildItem "$PSScriptRoot\..\android\mirror-server\src" -Recurse -Filter *.java
$build = "$PSScriptRoot\..\android\mirror-server\build\classes"
$outDir = "$PSScriptRoot\..\android\mirror-server\build"
New-Item -ItemType Directory -Force $build | Out-Null
Remove-Item "$build\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Compiling Java sources..."
& javac -source 8 -target 8 -cp $androidJar.FullName -d $build $source.FullName

Write-Host "Converting classes to DEX with d8..."
$classFiles = Get-ChildItem "$build\com\nativemirror\*.class" | Select-Object -ExpandProperty FullName
$jar = "$outDir\mirror-server.jar"
& $d8.FullName --output $jar $classFiles

Write-Host "Successfully built Android Server DEX jar: $jar" -ForegroundColor Green
