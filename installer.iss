; ── Fadimrak Steam Tool — Inno Setup Script ──────────────────────────────────
; Inno Setup 6.x gerektirir: https://jrsoftware.org/isdl.php

#define AppName      "Fadimrak Steam Tool"
#define AppVersion   "1.0"
#define AppPublisher "fadimrak"
#define AppExeName   "FadimrakSteamTool.exe"
#define AppDir       "fadimraksteamtool"
#define SourceDir    "dist"

[Setup]
AppId={{A3F2C1D0-4B7E-4F2A-9C1B-8D3E5F6A7B2C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://fadimrak.xyz
AppSupportURL=https://fadimrak.xyz
AppUpdatesURL=https://fadimrak.xyz

DefaultDirName={sd}\{#AppDir}
DefaultGroupName={#AppName}

DirExistsWarning=no
DisableProgramGroupPage=yes

WizardStyle=modern
WizardResizable=no
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

OutputDir=output
OutputBaseFilename=FadimrakSteamTool_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes

MinVersion=10.0
PrivilegesRequired=admin
ShowLanguageDialog=no
CloseApplications=yes
CloseApplicationsFilter=*{#AppExeName}*
RestartApplications=no

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"
Name: "startupicon"; Description: "Windows başlangıcında otomatik çalıştır"; GroupDescription: "Ek görevler:"

[Files]
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "steam_api64.dll"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";         FileName: "{app}\{#AppExeName}"
Name: "{group}\Kaldır";             FileName: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; FileName: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#AppName}"; \
  ValueData: """{app}\{#AppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupicon

Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; \
  ValueType: string; ValueName: "InstallPath"; \
  ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#AppExeName}"; \
  Description: "{#AppName} uygulamasini baslat"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[Code]
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Bu sihirbaz ' + ExpandConstant('{#AppName}') + ' v' + ExpandConstant('{#AppVersion}') +
    ' suruumunu bilgisayariniza kuracaktir.' + #13#10 + #13#10 +
    'Devam etmek icin Ileri dugmesine tiklayin.';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectTasks then
    if WizardForm.TasksList.Items.Count > 1 then
      WizardForm.TasksList.Checked[1] := False;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Response: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Response := MsgBox(
      'Uygulama verileriniz (ayarlar, kurulu oyun listesi) de silinsin mi?' + #13#10 +
      'Hayir secerseniz bu veriler korunur.',
      mbConfirmation, MB_YESNO
    );
    if Response = IDYES then
      DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
