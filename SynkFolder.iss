#define MyAppName "SynkFolder"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "SynkFolder"
#define MyAppExeName "SynkFolder.exe"

[Setup]
AppId={{D1CC42E2-5A9B-4A71-BCC1-24C78F7CA112}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SynkFolder
DefaultGroupName=SynkFolder
OutputDir=dist_installer
OutputBaseFilename=SynkFolderSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
SetupIconFile=assets\SynkFolder.ico
UninstallDisplayIcon={app}\SynkFolder.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\SynkFolder.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\SynkFolder.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SynkFolder"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SynkFolder.ico"
Name: "{autodesktop}\SynkFolder"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\SynkFolder.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SynkFolder"; Flags: nowait postinstall skipifsilent
