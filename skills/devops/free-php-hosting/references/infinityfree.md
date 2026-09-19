# InfinityFree — guía de deploy y límites exactos (verificado 2026-09)

## Lo que ofrece (gratis, sin tarjeta)

- PHP 8.3, MySQL 8/MariaDB, SSL Let's Encrypt gratis, dominio propio o subdominio gratis (rf.gd, ct.ws, etc.)
- 5 GB disco, hasta 400 BDs, "bandwidth ilimitado" con fair-use
- Subida por FTP (o file manager web); phpMyAdmin propio para importar SQL

## Límites duros (verificados en foro oficial + reviews 2026)

| Límite | Valor | Consecuencia |
|---|---|---|
| Hits diarios | ~50,000/día (cada request HTTP cuenta: páginas, JS, CSS, imágenes, llamadas API) | Excedido → suspensión automática 24 h sin aviso |
| Tamaño de archivo | 10 MB máx (PHP/HTML ~1 MB, .htaccess 10 KB) | Fotos/vouchers de apps deben comprimirse antes |
| SSH | NO existe | Todo por FTP o file manager |
| Cron jobs | NO (eliminados 2023) | Tareas programadas imposibles nativamente |
| Email saliente | mail() y SMTP bloqueados | Notificaciones solo in-app |
| PHP execution time | ~10 s | Reports pesados no caben |
| MySQL remoto | BLOQUEADO — sqlXXX.infinityfree.com solo accesible desde su hosting | Nunca apuntar código local ni tests ahí |
| php.ini | No editable | memory_limit y upload_max de casa |

## Paso a paso de deploy (patrón config-split)

1. **Cuenta y subdominio**: registrar en infinityfree.com → "Create Account" → elegir subdominio o dominio propio → anotar credenciales FTP (usuario if0_XXXXXXX).
2. **BD**: panel VistaPanel → "MySQL Databases" → crear. Anotar EXACTO: nombre (con prefijo if0_XXXXXXX_), usuario, password, host (sqlXXX.infinityfree.com).
3. **Importar BD**: SU phpMyAdmin (botón desde el panel, no phpmyadmin.net) → pestaña Import → subir en orden: 01_schema.sql → 02_views.sql → 03_seed.sql. Archivos >10MB (con BLOBs) hay partirlos o subir assets a disco.
4. **Config**: subir el proyecto por FTP a htdocs/ (index.html, api/, css/, js/, componentes/). El archivo de credenciales de producción se sube RENOMBRADO como config.php (en el repo vive como config.produccion.php para no pisar el dev).
5. **Routing**: el router de `php -S` NO aplica en shared hosting. Verificar que /api/ funciona directo; si la app depende del router.php (ej. reescritura de rutas), añadir .htaccess con las reglas equivalentes en la raíz y en api/.
6. **Smoke**: abrir la URL pública, login con credenciales demo, 1 CRUD y el flujo crítico del negocio.

## Diagnóstico rápido

- `SQLSTATE[HY000] [2002] getaddrinfo for sqlXXX.infinityfree.com failed` desde DEV → el config local quedó apuntando a producción. Restaurar credenciales locales y re-ejecutar tests.
- 403/blank en /api/ → falta .htaccess o el docroot espera carpeta public/.
- Sitio caído 24h sin cambios → casi seguro suspensión por hits: revisar el panel.
