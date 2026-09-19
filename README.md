# hermes-config — Backup completo de tu Hermes Agent

Repo privado para replicar tu instalación de Hermes Agent en cualquier PC (Linux o Windows) sin perder skills, MCPs, providers ni API keys.

**Contenido:**

| Carpeta | Qué contiene |
|---|---|
| `config.yaml` | Tu configuración completa (18 providers, MCP servers, hooks) |
| `env.example` | Los nombres de las variables de entorno que Hermes espera (referencia) |
| `secrets/.env` | Tus API keys reales (texto plano, repo privado) |
| `secrets/auth.json` | Pool de 40 credenciales OAuth de providers |
| `skills/` | 36 skills propias que Hermes NO trae por defecto |
| `plugins/model-providers/` | 17 providers personalizados en Python |
| `plugins/orca-status/` | Plugin de estado |
| `memories/` | MEMORY.md + USER.md (memoria del agente) |
| `agents/` | 68 agentes personalizados |
| `rules/` | Reglas (ecc) |
| `SOUL.md` | Personalidad base |
| `scripts/backup.sh` | (Linux) Re-sincroniza tu Hermes hacia este repo |
| `scripts/restore.ps1` | (Windows) Restaura todo en `C:\Users\<tú>\.hermes\` |

## 🪟 Instalación en Windows desde 0

```powershell
# 1. Instalar Node.js 22+ (para MCPs via npx) y Hermes
#    (guia oficial: hermes-agent.nousresearch.com/docs)

# 2. Clonar este repo
git clone https://github.com/iamisma326-cpu/hermes-config.git
cd hermes-config

# 3. Restaurar TODO (skills, plugins, keys, config, memorias)
.\scripts\restore.ps1

# 4. Confianza de skills
hermes skills trust "$env:USERPROFILE\.hermes\skills"

# 5. MCPs remotos (URLs, se agregan con 2 comandos)
hermes mcp add inspo --url https://inspomcp.dev/api/mcp
hermes mcp add ui-skills --url https://www.ui-skills.com/mcp

# 6. Verificar
hermes skills list
hermes mcp list
hermes -z "hola"
```

### Requisitos Windows
- **Node.js 22+** (para los MCP vía `npx`: filesystem, fetch, github, sequential-thinking, context7, playwright, memory)
- **GitHub CLI** (`gh auth login`) si usas el MCP github
- No necesitas openssl ni passphrase — los secrets van en texto plano

### Diferencias conocidas Linux → Windows
1. **codebase-memory-mcp**: es un binario ELF Linux (293 MB) — el restore lo DESHABILITA automáticamente en Windows (elimina su hook y entrada MCP del config). Busca un build Windows del proyecto si lo necesitas.
2. **Rutas**: el restore.ps1 reemplaza `/home/isma` por tu `C:\Users\<usuario>` automáticamente.
3. **playwright MCP**: usa `--browser chrome`; en Windows también funciona con Edge (`--browser msedge`).
4. **ecc-imports** (~300 skills): NO incluidas (re-importables de su fuente original).

## 🐧 Restaurar en otro Linux

```bash
git clone https://github.com/iamisma326-cpu/hermes-config.git
cd hermes-config
rsync -a skills/ ~/.hermes/skills/
rsync -a plugins/ ~/.hermes/plugins/
rsync -a memories/ ~/.hermes/memories/
rsync -a agents/ ~/.hermes/agents/
rsync -a rules/ ~/.hermes/rules/
cp SOUL.md config.yaml ~/.hermes/
cp secrets/.env secrets/auth.json ~/.hermes/
hermes skills trust ~/.hermes/skills
```

## 🔄 Actualizar el backup (desde Linux)

Después de cambiar algo en tu Hermes (nueva skill, provider, key):

```bash
cd ~/hermes-config
bash scripts/backup.sh
git add -A && git commit -m "sync: <qué cambió>" && git push
```

## ⚠️ Seguridad
- Repo **privado** — tus API keys van en texto plano aquí. Si alguna vez lo haces público, PRIMERO rota todas las keys.
- Si GitHub bloquea algún push por detectar tokens, avisa y evaluamos cifrar solo ese archivo.
