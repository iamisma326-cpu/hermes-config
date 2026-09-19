# restore.ps1 — Restaura tu configuracion de Hermes en Windows desde este repo
# Prerequisitos: Hermes ya instalado desde 0 en Windows (hermes --version funciona)
# Uso:  .\scripts\restore.ps1 -Passphrase "TU_PASSPHRASE" [-Repo "C:\ruta\al\repo"]
#       (ejecutar desde la raiz del repo clonado, o pasar -Repo)

param(
  [Parameter(Mandatory=$true)]
  [string]$Passphrase,
  [string]$Repo = (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
)

$H = Join-Path $env:USERPROFILE ".hermes"
if (-not (Test-Path $H)) { New-Item -ItemType Directory -Path $H | Out-Null }

Write-Host "== 1. Skills propias =="
Copy-Item -Recurse -Force (Join-Path $Repo "skills\*") (Join-Path $H "skills\")

Write-Host "== 2. Plugins (model-providers + orca-status) =="
Copy-Item -Recurse -Force (Join-Path $Repo "plugins\model-providers") (Join-Path $H "plugins\")
Copy-Item -Recurse -Force (Join-Path $Repo "plugins\orca-status") (Join-Path $H "plugins\")

Write-Host "== 3. Memorias, agentes, reglas, SOUL =="
Copy-Item -Force (Join-Path $Repo "memories\MEMORY.md") (Join-Path $H "memories\")
Copy-Item -Force (Join-Path $Repo "memories\USER.md")   (Join-Path $H "memories\")
Copy-Item -Recurse -Force (Join-Path $Repo "agents\*")  (Join-Path $H "agents\")
Copy-Item -Recurse -Force (Join-Path $Repo "rules\*")   (Join-Path $H "rules\")
Copy-Item -Force (Join-Path $Repo "SOUL.md") $H

Write-Host "== 4. Secrets cifrados (.env + auth.json) =="
$enc = Join-Path $Repo "secrets\secrets.tar.gz.enc"
if (Test-Path $enc) {
  # Requiere openssl en PATH (Git para Windows lo trae: C:\Program Files\Git\usr\bin\openssl.exe)
  $tar = Join-Path $env:TEMP "hermes-secrets.tar.gz"
  & openssl enc -aes-256-cbc -d -pbkdf2 -iter 600000 -in $enc -pass pass:$Passphrase -out $tar
  if ($LASTEXITCODE -ne 0) { throw "Passphrase incorrecta o falta openssl en PATH" }
  & tar -xzf $tar -C $H
  Remove-Item $tar
  Write-Host "   .env y auth.json restaurados en $H"
} else {
  Write-Host "   No se encontro secrets.tar.gz.enc — copia .env manualmente"
}

Write-Host "== 5. config.yaml =="
# NOTA: el config.yaml del repo tiene rutas Linux (/home/isma). En Windows hay que adaptar:
#   - trusted_project_dirs -> C:\Users\<tu-usuario>\.hermes\skills  (etc.)
#   - MCP filesystem args  -> C:\Users\<tu-usuario>
#   - hook codebase-memory-mcp y MCP codebase-memory-mcp -> ELIMINARLOS (binario ELF no corre en Windows)
Copy-Item -Force (Join-Path $Repo "config.yaml") (Join-Path $H "config.yaml")
$cfg = Join-Path $H "config.yaml"
(Get-Content $cfg) `
  -replace '/home/isma', ($env:USERPROFILE -replace '\\','\') `
  -replace '(?s)(codebase-memory-mcp:\s*\n\s*command:[^\n]*\n)', '' `
  -replace "(?m)^\s*- id: codebase-memory-mcp\s*\n\s*type: command\s*\n\s*command:[^\n]*\n?", '' `
  | Set-Content $cfg
Write-Host "   config.yaml copiado y rutas adaptadas a $env:USERPROFILE"

Write-Host "== 6. MCP servers via npx (requiere Node.js instalado) =="
foreach ($mcp in @("filesystem","fetch","github","sequential-thinking","context7","playwright","memory")) {
  # Ya estan en config.yaml; solo verificar que npx exista
  if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "   ADVERTENCIA: npx no encontrado. Instala Node.js 22+ para los MCP servers."
    break
  }
}
Write-Host "   MCPs remotos: agrega inspo y ui-skills manualmente:"
Write-Host "     hermes mcp add inspo --url https://inspomcp.dev/api/mcp"
Write-Host "     hermes mcp add ui-skills --url https://www.ui-skills.com/mcp"
Write-Host "   (inspo usara MCP_INSPO_API_KEY del .env restaurado)"

Write-Host ""
Write-Host "== RESTAURACION COMPLETA =="
Write-Host "Pasos finales manuales:"
Write-Host "  1. hermes skills trust C:\Users\<tu-usuario>\.hermes\skills"
Write-Host "  2. Verificar: hermes skills list | findstr /i 'frontend animate canvas'"
Write-Host "  3. Iniciar nueva sesion de hermes y probar: 'hermes -z 'hola''"
Write-Host "  4. codebase-memory-mcp y su hook quedaron DESHABILITADOS (binario Linux)."
Write-Host "     Si quieres el equivalente en Windows, busca un build Windows del proyecto."
