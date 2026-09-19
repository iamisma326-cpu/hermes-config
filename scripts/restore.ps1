# restore.ps1 — Restaura tu configuracion de Hermes en Windows desde este repo
# Prerequisitos: Hermes ya instalado desde 0 en Windows (hermes --version funciona)
# Uso:  .\scripts\restore.ps1    (ejecutar desde la raiz del repo clonado, o pasar -Repo)

param(
  [string]$Repo = (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
)

$H = Join-Path $env:USERPROFILE ".hermes"
foreach ($d in @("skills","plugins","memories","agents","rules")) {
  if (-not (Test-Path (Join-Path $H $d))) { New-Item -ItemType Directory -Path (Join-Path $H $d) | Out-Null }
}

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

Write-Host "== 4. API keys y credenciales =="
Copy-Item -Force (Join-Path $Repo "secrets\.env")     $H
Copy-Item -Force (Join-Path $Repo "secrets\auth.json") $H
Write-Host "   .env y auth.json copiados a $H"

Write-Host "== 5. config.yaml =="
# El config.yaml del repo tiene rutas Linux (/home/isma). En Windows se adaptan:
#   - rutas -> C:\Users\<tu-usuario>
#   - hook y MCP codebase-memory-mcp -> ELIMINADOS (binario ELF no corre en Windows)
Copy-Item -Force (Join-Path $Repo "config.yaml") (Join-Path $H "config.yaml")
$cfg = Join-Path $H "config.yaml"
$winHome = $env:USERPROFILE
(Get-Content $cfg) `
  -replace '/home/isma', ($winHome -replace '\\','\\') `
  -replace '(?m)^\s*codebase-memory-mcp:\s*\n(\s+command:[^\n]*\n)\s*$', '' `
  -replace "(?m)^\s*- id: codebase-memory-mcp\s*\n\s*type: command\s*\n\s*command:[^\n]*\n?", '' `
  | Set-Content $cfg
Write-Host "   config.yaml copiado y rutas adaptadas a $winHome"

Write-Host "== 6. Verificando MCPs =="
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
  Write-Host "   ADVERTENCIA: npx no encontrado. Instala Node.js 22+ para los MCP servers."
} else {
  Write-Host "   npx OK — los 7 MCPs via npx del config.yaml funcionaran."
}

Write-Host ""
Write-Host "== RESTAURACION COMPLETA =="
Write-Host "Pasos finales manuales:"
Write-Host "  1. hermes skills trust C:\Users\<tu-usuario>\.hermes\skills"
Write-Host "  2. MCPs remotos:"
Write-Host "     hermes mcp add inspo --url https://inspomcp.dev/api/mcp"
Write-Host "     hermes mcp add ui-skills --url https://www.ui-skills.com/mcp"
Write-Host "  3. Iniciar nueva sesion y probar: hermes -z 'hola'"
Write-Host "  4. codebase-memory-mcp y su hook quedaron DESHABILITADOS (binario Linux)."
