# Provider landscape — hosting PHP / BD MySQL gratuito (verificado 2026-09)

Investigación con web_search en 2026 (no usar datos de memoria: los planes cambian cada año; 000webhost cerró en 2024, Heroku free murió 2022, PlanetScale free murió antes de 2026 — verificar antes de recomendar).

## Hosting PHP+MySQL compartido (gratis para siempre)

| Proveedor | Fortaleza | Límites clave | Ideal para |
|---|---|---|---|
| **InfinityFree** | PHP 8.3 + MySQL/MariaDB, sin tarjeta, 400 BDs, SSL | ~50k hits/día → suspensión 24h, sin SSH/cron/email, MySQL remoto bloqueado, 10MB/archivo | Demo/portfolio/proyecto de curso (elegido por el usuario para gestion-estudiantes) |
| **Byet.host** | 5GB, MariaDB 11.4, PHP 8.3, más ancho de banda que InfinityFree | Mismos límites estructurales (misma empresa iFastNet) | Alternativa si InfinityFree suspende |
| **Alwaysdata** | 1GB serio, SSH/SFTP, tareas programadas, uptime 99.7%, sin suspensión por tráfico | 1GB total (web+BD), sin dominio propio en free | Proyecto serio pequeño |

## Solo BD MySQL remota (app en otro lado)

| Proveedor | Fortaleza | Trampa |
|---|---|---|
| **Aiven Free MySQL** | Gestionada de verdad, TLS, backups | Requiere cuenta cloud; verificar plan vigente |
| **TiDB Cloud serverless** | MySQL-compatible, escala a cero | Sintaxis/compatibilidad no 100% MySQL |
| **remotemysql** | Instantáneo, phpMyAdmin | Solo testing, sin garantía de uptime |
| **freedb.tech** | Instantáneo | ¡Autoborra en 7 días! Solo demos de corta vida |

OJO: si el PHP vive en InfinityFree, la BD DEBE ser la de InfinityFree (la remota de otro proveedor no es alcanzable de forma fiable, y la de IF no es alcanzable desde fuera).

## Cloud moderno (PHP moderno, cold starts)

- **Koyeb**: 1 web service PHP nativo gratis (512MB, 1GB egress/mes), deploy git-push. El egress de 1GB se agota rápido si la app sirve BLOBs.
- **Render**: PHP solo vía Docker; free duerme tras 15 min inactividad (cold start 30-60 s). Postgres free caduca.

## VM gratis con tarjeta de verificación (no cobra en Always Free)

- **Oracle Cloud Always Free**: 2 VM AMD micro + hasta 4 ARM 24GB RAM, 200GB disco. La opción más potente; cuesta sysadmin setup y las VMs ARM a veces están agotadas por región.
- **GCP e2-micro**: 1 VM gratis, solo 3 regiones US, 1GB egress ajustado.

## Decisión rápida para un proyecto de curso

App PHP monolítica pequeña (gestion-estudiantes): InfinityFree como paso temporal ("x mientras") — configuración en minutos y cero costo; migrar a Alwaysdata/VPS barato cuando haya tráfico real o necesidad de cron/email/SSH. La BD va SIEMPRE en el mismo hosting que el PHP que la consume.
