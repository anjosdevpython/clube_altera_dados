; Inno Setup Script para o Clube Altera Dados
[Setup]
AppName=Clube Altera Dados
AppVersion=1.0.19
DefaultDirName={pf}\ClubeAlteraDados
DefaultGroupName=Clube Altera Dados
OutputBaseFilename=Instalador_Clube_v2
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
SetupIconFile=clube_icon.ico

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Programa Principal (Na subpasta app)
Source: "C:\temp_build2\dist\CLUBE_modif\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
; Atualizador (Na subpasta updater)
Source: "C:\temp_build2\dist\clube_updater.exe"; DestDir: "{app}\updater"; Flags: ignoreversion
; Arquivo de Versão (Na raiz da instalação)
Source: "version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "clube_icon.ico"; DestDir: "{app}\app"; Flags: ignoreversion

[Icons]
Name: "{group}\Clube Altera Dados"; Filename: "{app}\app\CLUBE_modif.exe"; IconFilename: "{app}\app\clube_icon.ico"
Name: "{commondesktop}\Clube Altera Dados"; Filename: "{app}\app\CLUBE_modif.exe"; Tasks: desktopicon; IconFilename: "{app}\app\clube_icon.ico"

[Run]
Filename: "{app}\app\CLUBE_modif.exe"; Description: "{cm:LaunchProgram,Clube Altera Dados}"; Flags: nowait postinstall skipifsilent
