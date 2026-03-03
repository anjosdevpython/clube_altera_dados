[Setup]
AppName=ClubeAlteraDados
AppVersion=1.0.0
DefaultDirName={commonappdata}\ClubeAlteraDados
DefaultGroupName=ClubeAlteraDados
OutputDir=.\
OutputBaseFilename=Setup_ClubeAlteraDados
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin 

[Dirs]
Name: "{app}"; Permissions: users-modify

[Files]
; O Updater agora é um arquivo único
Source: "dist\clube_updater.exe"; DestDir: "{app}\updater"; Flags: ignoreversion
; O App Principal permanece em pasta
Source: "dist\CLUBE_modif\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\Clube Altera Dados"; Filename: "{app}\updater\clube_updater.exe"; Parameters: ""; IconFilename: "{app}\app\CLUBE_modif.exe"
Name: "{group}\Clube Altera Dados"; Filename: "{app}\updater\clube_updater.exe"; Parameters: ""; IconFilename: "{app}\app\CLUBE_modif.exe"

[Run]
Filename: "{app}\updater\clube_updater.exe"; Description: "Lançar Clube Altera Dados Agora"; Flags: nowait postinstall
