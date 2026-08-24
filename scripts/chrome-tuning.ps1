# chrome-tuning.ps1
# Aplica as preferencias de memoria do Chrome. EXIGE o Chrome fechado.
# Backup de cada arquivo tocado fica ao lado, com sufixo .bak-<data>.

$ErrorActionPreference = "Stop"
$base = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (Get-Process chrome -ErrorAction SilentlyContinue) {
    Write-Host "ABORTADO: feche o Chrome antes de rodar (as mudancas seriam sobrescritas)." -ForegroundColor Red
    exit 1
}

function Save-Json($obj, $path) {
    Copy-Item $path "$path.bak-$stamp" -Force
    [IO.File]::WriteAllText($path, ($obj | ConvertTo-Json -Depth 100 -Compress), [Text.UTF8Encoding]::new($false))
}

# 1. Desliga "continuar executando apps em segundo plano ao fechar o Chrome" (global)
$lsPath = "$base\Local State"
$ls = Get-Content $lsPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $ls.background_mode) {
    $ls | Add-Member -NotePropertyName background_mode -NotePropertyValue ([pscustomobject]@{ enabled = $false })
} else {
    $ls.background_mode.enabled = $false
}
Save-Json $ls $lsPath
Write-Host "OK  background_mode.enabled = false (global)"

# 2. Por perfil: garante aceleracao de hardware ligada
foreach ($dir in Get-ChildItem $base -Directory | Where-Object { $_.Name -eq "Default" -or $_.Name -like "Profile*" }) {
    $pPath = Join-Path $dir.FullName "Preferences"
    if (-not (Test-Path $pPath)) { continue }
    $p = Get-Content $pPath -Raw -Encoding UTF8 | ConvertFrom-Json

    if (-not $p.hardware_acceleration_mode) {
        $p | Add-Member -NotePropertyName hardware_acceleration_mode -NotePropertyValue ([pscustomobject]@{ enabled = $true })
    } else {
        $p.hardware_acceleration_mode.enabled = $true
    }

    Save-Json $p $pPath
    Write-Host ("OK  {0}: hardware_acceleration_mode = true" -f $dir.Name)
}

Write-Host ""
Write-Host "Pronto. Backups: *.bak-$stamp" -ForegroundColor Green
