#!/usr/bin/env bash
# backup.sh — Sincroniza tu Hermes de Linux hacia este repo (ejecutar desde el repo)
# Uso: cd ~/hermes-config && bash scripts/backup.sh  (copia skills/plugins/config/secrets y listo)
set -euo pipefail

H="$HOME/.hermes"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Respaldando skills propias =="
# Skills de diseño + propias (ajusta la lista si agregas otras)
for s in frontend-design canvas-design animate design-taste-frontend designer-skills \
         interface-review web-design-engineer ui-ux-pro-max impeccable skills \
         android-compose-tutoring custom-provider-setup gestionest1-dev hermes-model-ops \
         localstorage-web-app mysql-architect mysql-expert codebase-memory skill-creator; do
  if [ -d "$H/skills/$s" ] && [ ! -L "$H/skills/$s" ]; then
    rsync -a --delete --exclude '__pycache__' "$H/skills/$s" "$REPO/skills/"
  fi
done
for cat in automation desktop development devops software-development frontend android teaching productivity research; do
  if [ -d "$H/skills/$cat" ] && [ ! -L "$H/skills/$cat" ]; then
    rsync -a --delete --exclude '__pycache__' "$H/skills/$cat" "$REPO/skills/"
  fi
done

echo "== Respaldando plugins =="
rsync -a --delete --exclude '__pycache__' "$H/plugins/model-providers" "$REPO/plugins/"
[ -d "$H/plugins/orca-status" ] && rsync -a --delete --exclude '__pycache__' "$H/plugins/orca-status" "$REPO/plugins/"

echo "== Respaldando memorias, agentes, reglas, SOUL =="
cp "$H/memories/MEMORY.md" "$H/memories/USER.md" "$REPO/memories/" 2>/dev/null || true
rsync -a --delete "$H/agents/" "$REPO/agents/"
rsync -a --delete "$H/rules/" "$REPO/rules/"
cp "$H/SOUL.md" "$REPO/SOUL.md"

echo "== Respaldando config.yaml (sanitizado) =="
# Copia cruda; recuerda sanitizar tokens antes de commit si editaste MCPs
cp "$H/config.yaml" "$REPO/config.yaml"
grep -qE "ghp_[A-Za-z0-9]{10,}" "$REPO/config.yaml" && echo "⚠️  ATENCION: config.yaml contiene un token ghp_ — sanitizalo antes de commit"

echo "== Copiando secrets (texto plano) =="
mkdir -p "$REPO/secrets"
cp "$H/.env" "$REPO/secrets/.env"
cp "$H/auth.json" "$REPO/secrets/auth.json"
echo "   secrets/.env y secrets/auth.json actualizados."

echo "== Backup listo. Revisa con git status y haz commit+push =="
git -C "$REPO" status --short | head -30
