; Inno Setup definition for the Windows release artifact.
#define MyAppName "OmniSense AI"
#define MyAppVersion "0.1.0"
[Setup]
AppId={{7E0F8B9A-8B52-4F7D-9B4E-4D4A9D5E10AA}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\OmniSense AI
OutputBaseFilename=OmniSenseAI-Setup
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
[Files]
Source: "dist\OmniSenseAI.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\OmniSense AI"; Filename: "{app}\OmniSenseAI.exe"
