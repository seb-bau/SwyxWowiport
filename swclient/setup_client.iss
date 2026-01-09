; --- Inno Setup Script: SwyxWowiport Installer --------------------------------
; Voraussetzungen: Inno Setup 6.x
; Funktion:
;  - Installiert swclient.exe und swyxitevent.vbs
;  - Autostart von swyxitevent.vbs
;  - Registrywerte mit Default "<changeme>", überschreibbar per Parametern
; -----------------------------------------------------------------------------

[Setup]
AppName=SwyxWowiport Client
AppVersion=1.0.1
DefaultDirName={commonpf}\SwyxWowiport
DefaultGroupName=SwyxWowiport
PrivilegesRequired=admin
ArchitecturesAllowed=x86 x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
OutputBaseFilename=swclient_setup

[Files]
Source: "dist\swclient\swclient.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\swclient\_internal\*"; \
    DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\swclient\swyxitevent.vbs"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKLM64; Subkey: "Software\SwyxWowiport"; Flags: uninsdeletekeyifempty
Root: HKLM64; Subkey: "Software\SwyxWowiport"; ValueType: string; ValueName: "wowi_url";   ValueData: "{code:RegWowiUrl}"
Root: HKLM64; Subkey: "Software\SwyxWowiport"; ValueType: string; ValueName: "api_key";    ValueData: "{code:RegApiKey}"
Root: HKLM64; Subkey: "Software\SwyxWowiport"; ValueType: string; ValueName: "host";       ValueData: "{code:RegHost}"
Root: HKLM64; Subkey: "Software\SwyxWowiport"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"

Root: HKLM64; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SwyxItevent"; ValueData: """{app}\swyxitevent.vbs"""; Flags: uninsdeletevalue

[Run]
Filename: "{app}\swclient.exe"; Description: "SwyxWowiport Client jetzt starten"; Flags: nowait postinstall skipifsilent

[Code]
var
  wowi_url, api_key, host: string;

function GetParamValue(const Name: string; var Value: string): Boolean;
var
  i: Integer;
  S, Prefix: string;
begin
  Result := False;
  Prefix := '/' + Uppercase(Name) + '=';
  for i := 1 to ParamCount do
  begin
    S := ParamStr(i);
    if Uppercase(Copy(S, 1, Length(Prefix))) = Prefix then
    begin
      Value := Copy(S, Length(Prefix) + 1, MaxInt);
      Result := True;
      Exit;
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  { Default-Werte setzen }
  api_key  := '<changeme>';
  wowi_url := '<changeme>';
  host     := '<changeme>';

  { Optional: Parameter überschreiben Defaults }
  GetParamValue('APIKEY', api_key);
  GetParamValue('WOWIURL', wowi_url);
  GetParamValue('HOST',   host);

  Result := True;
end;

{ Getter für die [Registry]-Einträge }
function RegApiKey(Param: string): string;
begin
  Result := api_key;
end;

function RegWowiUrl(Param: string): string;
begin
  Result := wowi_url;
end;

function RegHost(Param: string): string;
begin
  Result := host;
end;
