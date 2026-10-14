param(
    [string]$TargetDir = "$env:LOCALAPPDATA\Programs\CODS"
)

$wsh = New-Object -ComObject WScript.Shell

$exeName = "CODS.exe"
if (!(Test-Path (Join-Path $TargetDir "CODS.exe")) -and (Test-Path (Join-Path $TargetDir "JADS.exe"))) {
    $exeName = "JADS.exe"
}

# 1. Desktop Shortcut
$desktop = [Environment]::GetFolderPath('Desktop')
$scDesktop = $wsh.CreateShortcut((Join-Path $desktop "CODS.lnk"))
$scDesktop.TargetPath = (Join-Path $TargetDir $exeName)
$scDesktop.WorkingDirectory = $TargetDir
$scDesktop.IconLocation = (Join-Path $TargetDir "logo.ico") + ",0"
$scDesktop.Description = "ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)"
$scDesktop.Save()

# 2. Start Menu Shortcut
$startPrograms = [Environment]::GetFolderPath('Programs')
$menuFolder = Join-Path $startPrograms "CODS"
if (!(Test-Path $menuFolder)) {
    New-Item -ItemType Directory -Path $menuFolder -Force | Out-Null
}

$scStart = $wsh.CreateShortcut((Join-Path $menuFolder "CODS.lnk"))
$scStart.TargetPath = (Join-Path $TargetDir $exeName)
$scStart.WorkingDirectory = $TargetDir
$scStart.IconLocation = (Join-Path $TargetDir "logo.ico") + ",0"
$scStart.Description = "ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)"
$scStart.Save()

# 3. Uninstaller Shortcut in Start Menu
$scUn = $wsh.CreateShortcut((Join-Path $menuFolder "Uninstall CODS.lnk"))
$scUn.TargetPath = (Join-Path $TargetDir "uninstall.bat")
$scUn.WorkingDirectory = $TargetDir
$scUn.Description = "ถอนการติดตั้ง CODS"
$scUn.Save()
