$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$versionFile = Join-Path $projectRoot "VERSION"
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$bundleDirectory = Join-Path $projectRoot "dist\GestionadorDeArchivos"
$installerDirectory = Join-Path $projectRoot "dist\installer"
$buildDirectory = Join-Path $projectRoot "build"
$innoScript = Join-Path $projectRoot "installer\GestionadorDeArchivos.iss"
$iconFile = Join-Path $projectRoot "assets\gestionador_archivos.ico"
$logoFile = Join-Path $projectRoot "assets\gestionador_archivos.png"

if (-not (Test-Path $versionFile)) {
    throw "No se encontró VERSION. Crea el archivo con una versión MAJOR.MINOR.PATCH."
}

$appVersion = (Get-Content -Raw $versionFile).Trim()
if ($appVersion -notmatch '^(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})$') {
    throw "La versión '$appVersion' no es válida. Usa el formato MAJOR.MINOR.PATCH, por ejemplo 1.0.0."
}

$versionParts = @($appVersion.Split('.') | ForEach-Object { [int]$_ })
if ($versionParts | Where-Object { $_ -gt 65535 }) {
    throw "Cada componente de VERSION debe ser menor o igual a 65535."
}

$missingAssets = @($iconFile, $logoFile) | Where-Object { -not (Test-Path $_) }
if ($missingAssets.Count -gt 0) {
    throw "Faltan recursos de la aplicación: $($missingAssets -join ', ')"
}

$fileVersion = ($versionParts + 0) -join ","
$versionInfoPath = Join-Path $buildDirectory "GestionadorDeArchivos.version.txt"

if (-not (Test-Path $python)) {
    throw "No se encontró .venv. Crea el entorno e instala requirements.txt antes de construir."
}

$innoCompiler = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if (-not $innoCompiler) {
    $innoCandidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
    )
    $innoCompilerPath = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $innoCompilerPath) {
        throw "No se encontró Inno Setup 6 o 7. Instálalo y vuelve a ejecutar este script."
    }
} else {
    $innoCompilerPath = $innoCompiler.Source
}

& $python -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw "No se pudo inicializar pip en el entorno virtual." }

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "No se pudieron actualizar las herramientas de Python." }

& $python -m pip install -r (Join-Path $projectRoot "requirements.txt") pyinstaller
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de construcción." }

New-Item -ItemType Directory -Path $buildDirectory -Force | Out-Null
$versionInfo = @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($fileVersion),
    prodvers=($fileVersion),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Gestionador de archivos'),
          StringStruct('FileDescription', 'Gestionador de archivos'),
          StringStruct('FileVersion', '$appVersion'),
          StringStruct('InternalName', 'GestionadorDeArchivos'),
          StringStruct('OriginalFilename', 'GestionadorDeArchivos.exe'),
          StringStruct('ProductName', 'Gestionador de archivos'),
          StringStruct('ProductVersion', '$appVersion')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@
Set-Content -Path $versionInfoPath -Value $versionInfo -Encoding ascii

& $python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name GestionadorDeArchivos `
    --icon $iconFile `
    --version-file $versionInfoPath `
    --add-data "$logoFile;assets" `
    --add-data "$iconFile;assets" `
    --collect-all customtkinter `
    --collect-all send2trash `
    --distpath (Join-Path $projectRoot "dist") `
    --workpath $buildDirectory `
    --specpath $buildDirectory `
    (Join-Path $projectRoot "main.py")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller no pudo construir la aplicación." }

New-Item -ItemType Directory -Path $installerDirectory -Force | Out-Null
& $innoCompilerPath "/DSourceDir=$bundleDirectory" "/DOutputDir=$installerDirectory" "/DAppVersion=$appVersion" "/DIconFile=$iconFile" $innoScript
if ($LASTEXITCODE -ne 0) { throw "Inno Setup no pudo crear el instalador." }

Write-Host "Versión: $appVersion"
Write-Host "Ejecutable creado: $bundleDirectory\GestionadorDeArchivos.exe"
Write-Host "Instalador creado: $installerDirectory\GestionadorDeArchivos-Setup-$appVersion.exe"