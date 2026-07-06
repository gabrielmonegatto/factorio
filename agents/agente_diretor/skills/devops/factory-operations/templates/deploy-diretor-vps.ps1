<#
  🏭 Deploy do Diretor VPS - Fabrica EternalL
  Uso: powershell -File deploy-diretor-vps.ps1
  Requer: Chave SSH em ~/.ssh/id_eternall
#>

$VPS = "root@187.127.44.153"
$KEY = "$env:USERPROFILE\.ssh\id_eternall"
$AGENTS = "$env:USERPROFILE\Desktop\EternalL\_factorio\agents"

Write-Host "🚀 Deploy Diretor VPS" -ForegroundColor Cyan

# 1. Copia arquivos
Write-Host "`n📦 Copiando arquivos..." -ForegroundColor Yellow
@("Dockerfile","requirements.txt","entrypoint.sh","diretor-vps\config.yaml","diretor-vps\.env") | ForEach-Object {
    $src = Join-Path $AGENTS $_
    scp -i $KEY -o StrictHostKeyChecking=no $src "${VPS}:/app/_factorio/agents/$_"
    if ($?) { Write-Host "  ✅ $_" } else { Write-Host "  ❌ $_" }
}

# 2. Rebuild
Write-Host "`n🔧 Rebuildando..." -ForegroundColor Yellow
ssh -i $KEY -o StrictHostKeyChecking=no $VPS @"
    cd /app/_factorio
    docker compose build factorio_agents
    docker compose up -d factorio_agents
"@

# 3. Verificar
Write-Host "`n✅ Pronto!" -ForegroundColor Green
ssh -i $KEY $VPS "docker ps | grep factorio_agents && docker logs factorio_agents --tail 5"
Write-Host "`n🎮 Teste no Discord mencionando @Diretor" -ForegroundColor Green