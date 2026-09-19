# hermes-config — Backup completo de tu Hermes Agent

Repo privado para replicar tu instalación de Hermes Agent en cualquier PC (Linux o Windows) sin perder skills, MCPs, providers ni API keys.

**Contenido:**

| Carpeta | Qué contiene |
|---|---|
| `config.yaml` | Tu configuración completa (18 providers, 9+ MCP servers, hooks) — sanitizada, sin tokens en texto plano |
| `env.example` | Los 36 nombres de variables de entorno que Hermes espera (valores = `PEGAR_TU_KEY_AQUI`) |
| `secrets/secrets.tar.gz.enc` | Tu `.env` real + `auth.json` (40 credenciales OAuth) CIFRADOS con AES-256-CBC + PBKDF2 (600k iteraciones) |
| `skills/` | 36 skills propias que Hermes NO trae por defecto (diseño UI/UX, MySQL, Android, automatización, etc.) |
| `plugins/model-providers/` | 17 providers personalizados en Python (tokenrouter, orcarouter, modelscope, etc.) |
| `plugins/orca-status/` | Plugin de estado |
| `memories/` | MEMORY.md + USER.md (memoria del agente) |
| `agents/` | 68 agentes personalizados |
| `rules/` | Reglas (ecc) |
| `SOUL.md` | Personalidad base |
| `scripts/backup.sh` | (Linux) Re-sincroniza tu Hermes hacia este repo |
| `scripts/restore.ps1` | (Windows) Restaura todo en `C:\Users\<tú>\.hermes\` desde este repo |

## 🔑 Passphrase de los secrets

Los secrets están cifrados con:

```
openssl enc -aes-256-cbc -pbkdf2 -iter 600000
```

**La passphrase NO está en este repo** (obviamente). Guárdala en tu gestor de contraseñas.
El archivo contiene: `.env` (28+ API keys) y `auth.json` (pool de 40 credenciales).

Descifrar manualmente (cualquier OS con openssl):

```bash
openssl enc -aes-256-cbc -d -pbkdf2 -iter 600000 \
  -in secrets/secrets.tar.gz.enc -pass pass:TU_PASSPHRASE \
  | tar xzf - -C ~/.hermes/
```

## 🪟 Instalación en Windows desde 0

```powershell
# 1. Instalar Hermes (PowerShell como administrador)
irm https://hermes-agent.nousresearch.com/install.ps1 | iex
#    (o el comando oficial de la doc: hermes-agent.nousresearch.com/docs)

# 2. Clonar este repo
git clone https://github.com/iamisma326-cpu/hermes-config.git
cd hermes-config

# 3. Ejecutar el restore (pide passphrase)
.\scripts\restore.ps1 -Passphrase "TU_PASSPHRASE"

# 4. Confianza de skills + verificar
hermes skills trust "$env:USERPROFILE\.hermes\skills"
hermes skills list
hermes mcp list

# 5. MCPs remotos (URLs, no se copian solos)
hermes mcp add inspo --url https://inspomcp.dev/api/mcp
hermes mcp add ui-skills --url https://www.ui-skills.com/mcp
```

### Requisitos Windows
- **Node.js 22+** (para los MCP vía `npx`: filesystem, fetch, github, sequential-thinking, context7, playwright, memory)
- **Git para Windows** (trae `openssl.exe` y `tar`, necesarios para descifrar secrets)
- **GitHub CLI** (`gh auth login`) si usas el MCP github

### Diferencias conocidas Linux → Windows
1. **codebase-memory-mcp**: es un binario ELF Linux (293 MB) — en Windows queda DESHABILITADO (el hook y el MCP se eliminan del config automáticamente durante el restore). Busca un build Windows del proyecto si lo necesitas.
2. **Rutas**: el restore.ps1 reemplaza `/home/isma` por tu `C:\Users\<usuario>` automáticamente.
3. **playwright MCP**: usa `--browser chrome`; en Windows también funciona con Edge (`--browser msedge`).
4. **ecc-imports** (~300 skills): NO incluidas en este repo (4.2 MB, re-importables de su fuente original).

## 🐧 Restaurar en otro Linux

```bash
git clone https://github.com/iamisma326-cpu/hermes-config.git
cd hermes-config
# Copiar skills, plugins, memories, agents, rules, SOUL.md a ~/.hermes/
rsync -a skills/ ~/.hermes/skills/
rsync -a plugins/ ~/.hermes/plugins/
rsync -a memories/ ~/.hermes/memories/
rsync -a agents/ ~/.hermes/agents/
rsync -a rules/ ~/.hermes/rules/
cp SOUL.md config.yaml ~/.hermes/
# Secrets
openssl enc -aes-256-cbc -d -pbkdf2 -iter 600000 \
  -in secrets/secrets.tar.gz.enc -pass pass:TU_PASSPHRASE \
  | tar xzf - -C ~/.hermes/
hermes skills trust ~/.hermes/skills
```

## 🔄 Actualizar el backup (desde Linux)

Después de cambiar algo en tu Hermes (nueva skill, provider, key):

```bash
cd ~/hermes-config
bash scripts/backup.sh            # sin passphrase: solo actualiza skills/plugins/config
bash scripts/backup.sh MI_PASS    # con passphrase: también re-cifra .env+auth.json
git add -A && git commit -m "sync: <qué cambió>" && git push
```

## ⚠️ Seguridad
- Repo **privado**. Si alguna vez lo haces público, primero rota TODAS las API keys.
- GitHub escanea y puede bloquear pushes si detecta tokens en texto plano — por eso los secrets van cifrados.
- La passphrase es lo único que protege tus keys: úsala larga y no la compartas.
