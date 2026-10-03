#ifndef SourceDir
  #error SourceDir no fue definido por build_windows.ps1
#endif

#ifndef OutputDir
  #error OutputDir no fue definido por build_windows.ps1
#endif

#ifndef AppVersion
  #error AppVersion no fue definido por build_windows.ps1
#endif

[Setup]
AppId={{A41D8E72-4B0B-4D79-A0FA-07937E6B37A4}
AppName=Gestor de Música
AppVersion={#AppVersion}
AppPublisher=Gestor de Música
DefaultDirName={localappdata}\Programs\GestorDeMusica
DefaultGroupName=Gestor de Música
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=GestorDeMusica-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=Gestor de Música

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userdesktop}\Gestor de Música"; Filename: "{app}\GestorDeMusica.exe"; Tasks: desktopicon
Name: "{userprograms}\Gestor de Música\Gestor de Música"; Filename: "{app}\GestorDeMusica.exe"

[Run]
Filename: "{app}\GestorDeMusica.exe"; Description: "Iniciar Gestor de Música"; Flags: postinstall nowait skipifsilent