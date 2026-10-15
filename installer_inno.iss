; =====================================================================
; Inno Setup Script for CODS (Court Official Document System)
; ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม
; 100% Offline & Air-Gapped Judicial Assistant
; =====================================================================

#define MyAppName "CODS"
#define MyAppFullName "CODS - Court Official Document System"
#define MyAppVersion "1.2.0"
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
UsePreviousAppDir=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=CODS_Setup_v1.2
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
CloseApplicationsFilter={#MyAppExeName},JADS.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
ConfirmUninstall=ท่านต้องการถอนการติดตั้งโปรแกรม %1 ออกจากเครื่องคอมพิวเตอร์ใช่หรือไม่?
UninstallStatusLabel=กำลังถอนการติดตั้งโปรแกรม %1 กรุณารอสักครู่...
UninstalledAll=โปรแกรม %1 ได้รับการถอนการติดตั้งออกจากเครื่องคอมพิวเตอร์เรียบร้อยแล้ว

[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนทางลัดบนหน้าจอเดสก์ท็อป (Create Desktop Shortcut)"; GroupDescription: "ทางลัดเพิ่มเติม (Additional Icons):"
Name: "startmenuicon"; Description: "สร้างทางลัดในเมนูเริ่มต้น (Create Start Menu Shortcut)"; GroupDescription: "ทางลัดเพิ่มเติม (Additional Icons):"; Flags: checkedonce

[Dirs]
Name: "{app}\data"; Flags: uninsneveruninstall

[Files]
; Main application binaries and dependencies (excluding data folder so user databases are never overwritten on update)
Source: "dist\CODS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*,data"
; Initial data templates/config - only installed if doesn't already exist to preserve user data on updates!
Source: "data\*"; DestDir: "{app}\data"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall; Excludes: "*.db,*.db-wal,*.db-shm,*.migrated,*.tmp*"
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
; Clean up runtime temporary files (database cods.db in {app}\data is preserved by uninsneveruninstall)
Type: files; Name: "{app}\*.tmp"
Type: filesandordirs; Name: "{app}\data\cache"
Type: files; Name: "{app}\data\crash.log"

[Code]
var
  IsInstalled: Boolean;
  ExistingDir: String;
  ExistingUninstaller: String;
  MaintenancePage: TInputOptionWizardPage;

function DetectExistingInstall(): Boolean;
var
  s: String;
begin
  Result := False;
  ExistingDir := '';
  ExistingUninstaller := '';

  // 1. Check Current User Uninstall Registry (Default installation location)
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C0D50001-8A81-4C5C-9A8E-2B5FD13A492E}_is1', 'InstallLocation', s) then
  begin
    if (s <> '') and DirExists(s) then
    begin
      ExistingDir := s;
      Result := True;
    end;
  end;

  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C0D50001-8A81-4C5C-9A8E-2B5FD13A492E}_is1', 'UninstallString', s) then
  begin
    s := RemoveQuotes(s);
    if FileExists(s) then
    begin
      ExistingUninstaller := s;
      Result := True;
      if ExistingDir = '' then
        ExistingDir := ExtractFilePath(s);
    end;
  end;

  // 2. Check Local Machine Uninstall Registry (if installed as admin)
  if not Result then
  begin
    if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C0D50001-8A81-4C5C-9A8E-2B5FD13A492E}_is1', 'InstallLocation', s) then
    begin
      if (s <> '') and DirExists(s) then
      begin
        ExistingDir := s;
        Result := True;
      end;
    end;
  end;

  // 3. Fallback: Check default local app data folder
  if not Result then
  begin
    s := ExpandConstant('{localappdata}\Programs\CODS');
    if FileExists(s + '\{#MyAppExeName}') then
    begin
      ExistingDir := s;
      Result := True;
      if FileExists(s + '\unins000.exe') then
        ExistingUninstaller := s + '\unins000.exe';
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  IsInstalled := DetectExistingInstall();
end;

procedure InitializeWizard();
begin
  if IsInstalled then
  begin
    WizardForm.Caption := 'บำรุงรักษาและจัดการโปรแกรม {#MyAppName} - Court Official Document System';
    WizardForm.WelcomeLabel1.Caption := 'ยินดีต้อนรับสู่ตัวจัดการโปรแกรม {#MyAppName}';
    WizardForm.WelcomeLabel2.Caption := 'ระบบตรวจพบว่าโปรแกรม {#MyAppName} ได้รับการติดตั้งอยู่ในเครื่องนี้แล้ว' + #13#10 + #13#10 +
      'ตัวช่วยติดตั้งนี้จะช่วยให้ท่านสามารถดำเนินการ:' + #13#10 +
      '  • อัปเดตโปรแกรมเป็นเวอร์ชันใหม่ (v{#MyAppVersion})' + #13#10 +
      '  • ซ่อมแซมไฟล์ระบบ (Repair / Reinstall)' + #13#10 +
      '  • ถอนการติดตั้งโปรแกรมออกจากเครื่อง (Uninstall)' + #13#10 + #13#10 +
      'ระบบรับประกันความปลอดภัยของฐานข้อมูลคดีและแม่แบบข้อความเดิม 100%' + #13#10 + #13#10 +
      'กดปุ่ม "Next" เพื่อเลือกการดำเนินการที่ต้องการ';

    // Create Maintenance Option Page right after Welcome page
    MaintenancePage := CreateInputOptionPage(
      wpWelcome,
      'โหมดจัดการและบำรุงรักษาโปรแกรม (Maintenance Mode)',
      'ระบบตรวจพบโปรแกรม {#MyAppName} ในเครื่องคอมพิวเตอร์นี้แล้ว',
      'กรุณาเลือกรูปแบบการทำงานที่ท่านต้องการดำเนินการ:',
      True, False
    );
    MaintenancePage.Add('อัปเดตเป็นเวอร์ชันใหม่ v{#MyAppVersion} (Update) [แนะนำ]' + #13#10 +
                        '  - อัปเกรดไฟล์โปรแกรมเป็นรุ่นล่าสุด ปรับปรุงประสิทธิภาพ และรักษาข้อมูลเดิมทั้งหมดปลอดภัย 100%');
    MaintenancePage.Add('ซ่อมแซมโปรแกรม (Repair)' + #13#10 +
                        '  - เขียนทับและกู้คืนไฟล์ระบบทั้งหมดใหม่เพื่อแก้ไขปัญหาไฟล์เสียหายหรือเปิดโปรแกรมไม่ได้');
    MaintenancePage.Add('ถอนการติดตั้งโปรแกรม (Uninstall)' + #13#10 +
                        '  - ลบโปรแกรม {#MyAppName} และทางลัดทั้งหมดออกจากคอมพิวเตอร์');
    MaintenancePage.Values[0] := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if IsInstalled and (MaintenancePage <> nil) and (CurPageID = MaintenancePage.ID) then
  begin
    // Option 2: Uninstall
    if MaintenancePage.SelectedValueIndex = 2 then
    begin
      if MsgBox('ท่านต้องการถอนการติดตั้งโปรแกรม {#MyAppName} ออกจากเครื่องคอมพิวเตอร์ใช่หรือไม่?' + #13#10#13#10 +
                '(หมายเหตุ: ฐานข้อมูลคดีและแม่แบบส่วนตัวในโฟลเดอร์ data จะยังคงปลอดภัย)',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        if ExistingUninstaller <> '' then
        begin
          Exec(ExistingUninstaller, '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
        end
        else
        begin
          MsgBox('ไม่พบไฟล์ถอนการติดตั้ง (unins000.exe) กรุณาถอนการติดตั้งผ่าน Windows Settings / Apps & Features', mbError, MB_OK);
        end;
        WizardForm.Close;
        Result := False;
        Exit;
      end
      else
      begin
        Result := False;
        Exit;
      end;
    end;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  // If Update or Repair, skip directory and program group selection (seamless 1-click upgrade)
  if IsInstalled and (MaintenancePage <> nil) then
  begin
    if (MaintenancePage.SelectedValueIndex = 0) or (MaintenancePage.SelectedValueIndex = 1) then
    begin
      if (PageID = wpSelectDir) or (PageID = wpSelectProgramGroup) then
        Result := True;
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if IsInstalled and (MaintenancePage <> nil) then
  begin
    if CurPageID = wpReady then
    begin
      if MaintenancePage.SelectedValueIndex = 0 then
      begin
        WizardForm.ReadyLabel.Caption := 'ระบบพร้อมดำเนินการอัปเดต {#MyAppName} เป็นเวอร์ชัน {#MyAppVersion} แล้ว' + #13#10#13#10 +
                                         'กดปุ่ม "Install" เพื่อเริ่มการอัปเดตไฟล์ระบบ' + #13#10 +
                                         '(ฐานข้อมูลคดีและแม่แบบส่วนตัวของท่านจะถูกเก็บรักษาไว้อย่างสมบูรณ์)';
      end
      else if MaintenancePage.SelectedValueIndex = 1 then
      begin
        WizardForm.ReadyLabel.Caption := 'ระบบพร้อมดำเนินการซ่อมแซมไฟล์โปรแกรม {#MyAppName} แล้ว' + #13#10#13#10 +
                                         'กดปุ่ม "Install" เพื่อเริ่มการกู้คืนไฟล์ระบบทั้งหมด';
      end;
    end
    else if CurPageID = wpFinished then
    begin
      if MaintenancePage.SelectedValueIndex = 0 then
      begin
        WizardForm.FinishedHeadingLabel.Caption := 'การอัปเดตเสร็จสมบูรณ์';
        WizardForm.FinishedLabel.Caption := 'โปรแกรม {#MyAppName} ได้รับการอัปเดตเป็นเวอร์ชัน {#MyAppVersion} เรียบร้อยแล้ว' + #13#10#13#10 +
                                            'ฐานข้อมูลคดี แม่แบบข้อความ และการตั้งค่าเดิมของท่านพร้อมใช้งานทันที';
      end
      else if MaintenancePage.SelectedValueIndex = 1 then
      begin
        WizardForm.FinishedHeadingLabel.Caption := 'การซ่อมแซมเสร็จสมบูรณ์';
        WizardForm.FinishedLabel.Caption := 'ไฟล์ระบบของโปรแกรม {#MyAppName} ได้รับการซ่อมแซมเรียบร้อยแล้ว' + #13#10#13#10 +
                                            'ท่านสามารถเปิดใช้งานโปรแกรมได้ทันที';
      end;
    end;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

