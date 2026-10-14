; =====================================================================
; Inno Setup Script for CODS (Court Official Document System)
; ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม
; 100% Offline & Air-Gapped Judicial Assistant
; =====================================================================

#define MyAppName "CODS"
#define MyAppFullName "CODS - Court Official Document System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Court Official Document System"
#define MyAppExeName "CODS.exe"

[Setup]
; Unique GUID for CODS application
AppId={{C0D50001-8A81-4C5C-9A8E-2B5FD13A492E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\CODS
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=CODS_Setup_v1.0
SetupIconFile=logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Privileges: Allows non-admin installation into local app data, with optional admin override
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} - ถอนการติดตั้งโปรแกรม
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนทางลัดบนหน้าจอเดสก์ท็อป (Create Desktop Shortcut)"; GroupDescription: "ทางลัดเพิ่มเติม (Additional Icons):"
Name: "startmenuicon"; Description: "สร้างทางลัดในเมนูเริ่มต้น (Create Start Menu Shortcut)"; GroupDescription: "ทางลัดเพิ่มเติม (Additional Icons):"; Flags: checkedonce

[Files]
; Main application binaries and dependencies from dist\CODS
Source: "dist\CODS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Core identity logos
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu Shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: startmenuicon; Comment: "ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)"
Name: "{group}\ถอนการติดตั้ง {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon; Comment: "ถอนการติดตั้งโปรแกรม CODS"

; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"; Comment: "ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)"

[Run]
; Option to launch application immediately after installation
Filename: "{app}\{#MyAppExeName}"; Description: "เปิดใช้งานโปรแกรม {#MyAppName} ทันที"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up runtime temporary files (preserve database if desired)
Type: files; Name: "{app}\*.tmp"
