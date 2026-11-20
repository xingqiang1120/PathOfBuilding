# Run on the computer you play on. Copies the useful lines of Path of Exile's logs\Client.txt
# (areas generated and entered, deaths, level-ups) to a small file on your Desktop. Chat and whispers are dropped.
#
#   irm https://raw.githubusercontent.com/xingqiang1120/PathOfBuilding/feature/ai-tools/tools/export_clientlog.ps1 | iex
#
# or save this file and run:  powershell -ExecutionPolicy Bypass -File export_clientlog.ps1 [-Days 60] [-Path <Client.txt>]
param([int]$Days = 60, [string]$Path = "")

if (-not $Path) {
    $candidates = @(
        "C:\Program Files (x86)\Grinding Gear Games\Path of Exile\logs\Client.txt",
        "C:\Program Files\Grinding Gear Games\Path of Exile\logs\Client.txt",
        "C:\Program Files (x86)\Steam\steamapps\common\Path of Exile\logs\Client.txt",
        "C:\Program Files\Epic Games\PathOfExile\logs\Client.txt"
    )
    # other drives: X:\Grinding Gear Games\..., X:\SteamLibrary\..., X:\Steam\...
    foreach ($d in (Get-PSDrive -PSProvider FileSystem).Root) {
        $candidates += "${d}Grinding Gear Games\Path of Exile\logs\Client.txt"
        $candidates += "${d}SteamLibrary\steamapps\common\Path of Exile\logs\Client.txt"
        $candidates += "${d}Steam\steamapps\common\Path of Exile\logs\Client.txt"
        $candidates += "${d}Program Files (x86)\Grinding Gear Games\Path of Exile\logs\Client.txt"
    }
    # the folder of a running game
    $proc = Get-Process -Name "PathOfExile*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($proc -and $proc.Path) { $candidates = @((Join-Path (Split-Path $proc.Path) "logs\Client.txt")) + $candidates }
    $Path = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $Path -or -not (Test-Path $Path)) {
    Write-Host "Client.txt not found. Run again with -Path ""<game folder>\logs\Client.txt""" -ForegroundColor Red
    return
}

$since = (Get-Date).AddDays(-$Days).ToString("yyyy/MM/dd")
$out = Join-Path ([Environment]::GetFolderPath("Desktop")) ("ClientLog-" + (Get-Date -Format "yyyyMMdd") + ".txt")
$keep = [regex]'Generating level \d+ area|\[SCENE\] Set Source|LOG FILE OPENING|\] : '
$chat = [regex]'\] : ([@#$%&]|(<[^>]*> )?\S+: )'

# FileShare.ReadWrite: works while the game is running
$stream = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
$writer = New-Object System.IO.StreamWriter($out, $false, (New-Object System.Text.UTF8Encoding($false)))
$n = 0
try {
    while (($line = $reader.ReadLine()) -ne $null) {
        if ($line.Contains("LOG FILE OPENING")) { $writer.WriteLine($line); continue }
        if ($line.Length -lt 10 -or $line.Substring(0, 10) -lt $since) { continue }
        if ($keep.IsMatch($line) -and -not $chat.IsMatch($line)) { $writer.WriteLine($line); $n++ }
    }
} finally { $reader.Close(); $writer.Close() }

$mb = [math]::Round((Get-Item $out).Length / 1MB, 2)
Write-Host "Read:  $Path"
Write-Host "Saved: $out ($n lines, $mb MB, last $Days days, chat removed)" -ForegroundColor Green
