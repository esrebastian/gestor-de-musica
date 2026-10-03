#ifndef SourceDir
  #error SourceDir no fue definido por build_windows.ps1
#endif

#ifndef OutputDir
  #error OutputDir no fue definido por build_windows.ps1
#endif

#ifndef AppVersion
  #error AppVersion no fue definido por build_windows.ps1
#endif

#ifndef IconFile
  #error IconFile no fue definido por build_windows.ps1
#endif

[Setup]
AppId={{A41D8E72-4B0B-4D79-A0FA-07937E6B37A4}
AppName=Gestionador de archivos
AppVersion={#AppVersion}
AppPublisher=Gestionador de archivos
DefaultDirName={localappdata}\Programs\GestionadorDeArchivos
DefaultGroupName=Gestionador de archivos
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=GestionadorDeArchivos-Setup-{#AppVersion}
SetupIconFile={#IconFile}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=Gestionador de archivos

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\Gestionador de archivos"; Filename: "{app}\GestionadorDeArchivos.exe"; Tasks: desktopicon
Name: "{userprograms}\Gestionador de archivos\Gestionador de archivos"; Filename: "{app}\GestionadorDeArchivos.exe"

[Run]
Filename: "{app}\GestionadorDeArchivos.exe"; Description: "Iniciar Gestionador de archivos"; Flags: postinstall nowait skipifsilent