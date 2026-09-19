---
name: free-php-hosting
description: "Deploy PHP+MySQL apps to free hosting (InfinityFree et al)."
kind: tool
version: 1.0.0
license: MIT
metadata:
  author: isma + Hermes
  hermes:
    tags: [hosting, php, mysql, deployment, free-tier, infinityfree]
    related_skills: [mysql-architect]
---

# Free PHP Hosting

PHP NO corre en Vercel/Netlify/Cloudflare Pages (static o functions Node/Python). Un proyecto PHP+MySQL necesita un host con PHP o un VPS. Esta skill cubre: elegir proveedor gratis, desplegar sin romper el entorno dev, y diagnosticar los límites del free tier.

## When to Use

- El usuario pregunta por alternativas gratuitas de hosting para PHP ("mi hosting era en Vercel, ahora qué hago").
- Quiere desplegar un proyecto PHP+MySQL a InfinityFree o similar, o elegir entre hosts gratuitos.
- Pide SOLO una BD remota gratuita (app alojada en otro lado).
- Diagnostica límites del free tier: suspensión por hits, MySQL remoto inaccesible, "getaddrinfo failed" en tests locales tras un deploy.

## Decision tree — ¿qué necesita el proyecto?

| Situación | Camino | Leer |
|---|---|---|
| App PHP completa (app+BD juntas, cero sysadmin) | InfinityFree / Byet (shared con PHP+MySQL) | `references/infinityfree.md` |
| Solo la BD remota (app alojada en otro lado) | Aiven Free MySQL / TiDB serverless / remotemysql (solo testing) | `references/provider-landscape.md` |
| Deploy moderno git-push / Docker | Koyeb (PHP nativo, 1GB egress/mes) / Render (vía Docker, spin-down 15 min) | `references/provider-landscape.md` |
| Potencia real gratis (tarjeta de verificación) | Oracle Cloud Always Free (VM, 24GB RAM) | `references/provider-landscape.md` |

## Restricciones universales del free tier PHP (verificadas 2026)

- **Sin SSH** en shared hosting → FTP + su phpMyAdmin, nada más.
- **Sin cron** (InfinityFree los quitó en 2023) → tareas programadas via ping externo o no existen.
- **Sin email saliente** (mail() y SMTP bloqueados) → notificaciones quedan in-app o via servicio externo.
- **Límite de hits diarios**: InfinityFree ~50k/día → suspensión automática 24 h sin aviso. Cada asset (JS/CSS/img) cuenta como hit.
- **MySQL REMOTO BLOQUEADO** en InfinityFree/Byet: `sqlXXX.infinityfree.com` NO responde fuera de su red. Jamás apuntar código local o tests al host de producción; los dumps se importan por el phpMyAdmin DE ELLOS.
- Archivos máx ~10 MB, PHP exec ~10 s, php.ini no editable.

## Workflow de deploy — patrón config-split

1. **Config dividido en el repo**: `config.php` = credenciales LOCALES (dev); `config.produccion.php` = credenciales del hosting. Nunca subir credenciales a git; la de producción solo vive en el servidor (renombrada).
2. **BD primero**: crear la BD en el panel del hosting → importar por SU phpMyAdmin en orden: schema → views → seed (el seed re-ejecutable con TRUNCATEs).
3. **FTP**: subir index + api/ + assets; NUNCA subir .git/, tests/, backups/, *.zip, node_modules. Subir `config.produccion.php` RENOMBRADO a `config.php`.
4. **Routing**: `php -S router.php` es solo dev. En shared hosting el docroot sirve el index directo y `api/` necesita .htaccess de rewrite — revisar las reglas del .htaccess del repo antes de confiar en él.
5. **Smoke en vivo** contra la URL pública (login + 1 CRUD + 1 flujo crítico). Los E2E/tests corren SOLO contra la BD local.
6. **Síntoma clave en dev**: `Error de base de datos ... getaddrinfo for sqlXXX... failed` = el config quedó apuntando a producción → restaurar config local y re-correr tests.

## Cuándo NO usar free hosting

Tráfico real (>100 visitantes/día), necesidad de cron/email/SSH, o BD con BLOBs que crezca — pagar ~$3-5/mes un VPS (Hetzner/DO/Lightsail) o Alwaysdata gratuito según el caso. El free tier es para demos, portfolios y proyectos de curso.

## Referencias

- `references/infinityfree.md` — guía paso a paso del panel/FTP/phpMyAdmin y límites exactos.
- `references/provider-landscape.md` — comparativa verificada de proveedores gratuitos 2026.
