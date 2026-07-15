; Energy Monitoring System - Inno Setup installer starter
;
; Usage example:
;   ISCC.exe /DSourceRoot="D:\FFPL\energy-monitoring-system\release\energy-monitoring-system-pilot_YYYY-MM-DD_HHMMSS\energy-monitoring-system" installer\energy_monitoring_system.iss
;
; The SourceRoot must point to the prepared application folder created by:
;   powershell -ExecutionPolicy Bypass -File .\scripts\prepare_release_bundle.ps1

#ifndef SourceRoot
  #error SourceRoot must point to the prepared application folder created by prepare_release_bundle.ps1
#endif

#define MyAppName "Plant Energy Monitor"
#define MyAppVersion "0.1.0-pilot"
#define MyAppPublisher "Energy Monitoring System Project"
#define MyAppExeName "run_app.bat"

[Setup]
AppId={{6E64F6D9-30A6-45A9-8AC3-4A8AB75C8DA1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonappdata}\Plant Energy Monitor
DefaultGroupName=Plant Energy Monitor
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=output
OutputBaseFilename=plant_energy_monitor_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UsePreviousAppDir=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\logs"
Name: "{app}\backups"
Name: "{app}\release"

[Icons]
Name: "{group}\Launch Plant Energy Monitor"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Plant Energy Monitor Folder"; Filename: "{app}"
Name: "{group}\Plant PC Deployment Guide"; Filename: "{app}\docs\plant-pc-deployment.md"
Name: "{group}\First-Run Setup"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\first_run_setup.ps1"""
Name: "{group}\Python Environment Bootstrap"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\bootstrap_python_env.ps1"""
Name: "{group}\Register Backend Startup"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\install_task_scheduler_backend.ps1"""
Name: "{group}\Post-Install Check"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\post_install_check.ps1"""
Name: "{commondesktop}\Plant Energy Monitor"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\first_run_setup.ps1"""; Description: "Run first-run setup helper"; Flags: postinstall skipifsilent unchecked
Filename: "{app}\docs\plant-pc-deployment.md"; Description: "Open deployment guide after install"; Flags: postinstall shellexec skipifsilent unchecked
