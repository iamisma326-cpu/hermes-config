# Módulo WhatsApp (WAHA) — implementado 2026-09-12/13, commit 499b859

Automatización de trámites por WhatsApp (Opción A del análisis v5:
`docs/analisis_whatsapp_automatizacion_v5.md` — fuente de diseño, NO borrar
del repo: WahaNotificador.php y 11_whatsapp.sql la citan).

## Qué existe (verificado, e2e 112/112)

- **BD**: 4 tablas `whatsapp_plantillas` / `whatsapp_registrados` /
  `whatsapp_mensajes` / `whatsapp_despachos` en AMBOS motores:
  `api/sql/11_whatsapp.sql` (PostgreSQL) y `api/sql/mariadb/11_whatsapp.sql`
  (MariaDB). Migración v2.1.0→v2.2.0, con sección ROLLBACK comentada al
  final. Con esto: MariaDB y PG quedan en 60 tablas.
- **PHP**: `api/src/WahaNotificador.php` (adapter Notificador→WAHA):
  `encolarRol()` fire-and-forget (NUNCA bloquea el flujo del trámite),
  `procesarCola()` worker con reintentos ≤20 y SKIP LOCKED,
  `recibir()` webhook (POST /api/whatsapp/inbox, token propio, sin auth de
  sesión), `activo()` health-check contra WAHA (env WAHA_URL, default
  http://127.0.0.1:3000).
- **Disparadores**: `TramitesHandler` — WP-TRAM-NUEVO al crear trámite (→
  Tesorería) y WP-TRAM-LISTO al pasar a "Listo para recojo".
- **Comandos del bot** (deterministas, sin IA): `pendientes` (lista con
  códigos), `validar T-0008|T0008|0008` (pasa trámite a En proceso + bitácora),
  `resumen`, `ayuda`; reacción ✅ a una alerta = avanzar trámite. Whitelist:
  solo `whatsapp_registrados` (rol); números desconocidos se ignoran.
- **API**: GET /api/whatsapp/estado (waha_activo + contadores cola/enviado/error)
  + 4 entidades CRUD genéricas en `$genericas` (whatsappPlantillas...).
- **Frontend**: vista `js/ui/vistas/whatsapp.js` (estado servidor/cola +
  plantillas + probadores), entrada de menú para TODOS los roles.
- **Plantillas seed**: WP-TRAM-NUEVO, WP-PAGO-VALIDADO, WP-TRAM-LISTO,
  WP-MATR-OK, WP-AYUDA, WP-UNKNOWN — con {marcadores}, editables en el
  catálogo sin programadores.

## Pendiente (NO construido aún)

1. WAHA real: `docker run -d --restart=always --name waha -p 3000:3000 -e WHATSAPP_DEFAULT_ENGINE=WEBJS -e WHATSAPP_API_KEY=... -v waha-sessions:/app/.sessions devlikeapro/waha:chrome` + SIM nueva + escanear QR 1 vez (sesión persistente en volumen).
2. `RouterIA.php` (capa IA opcional, failover 3 capas estilo OmniRoute): diseño completo con cadena probada en §4-§6 del análisis v5. Commands-first: el MVP va SIN IA.

## Pitfalls verificados en la sesión de implementación

1. **Seed whatsapp con INSERT IGNORE no borra**: re-seedear no elimina el
   teléfono demo ya registrado; un INSERT manual del mismo número da
   `ERROR 1062 Duplicate entry` — es el seed HACIENDO su trabajo, no un bug.
   Para un estado limpio: TRUNCATE manual de las 4 tablas antes del seed.
2. **`incidencias` no tiene columna `id`** (PK es `codigo`): `ORDER BY id`
   falla con `Unknown column`. Ordenar por `codigo`.
3. **Comparar "antes vs después" con git stash es baseline inválida cuando
   el cambio AGREGA tablas**: el stash corre la suite contra una BD que YA
   tiene datos seedeados de las tablas nuevas → el estado "antes" falla por
   la BD, no por el código. Conclusión correcta de la sesión: el "antes"
   roto no prueba nada sobre el "después"; el veredicto real es la suite
   completa con BD re-seededa (112/112).
4. **Re-seedeo completo con módulo whatsapp** (orden verificado):
   `03_seed.sql` + `05_seed_soporte.sql` + `06_seed_egresados.sql` +
   `api/sql/mariadb/11_whatsapp.sql` (el seed de soporte re-crea RES-0004
   que la suite usa — sin él hay 10 FAILs de datos duplicados/acumulados).
5. **Router del frontend**: `Router.ir(vista)` setea el hash
   (`"#/"+vista`); si el hash ya estaba, `hashchange` NO dispara. Tras un
   `location.reload()` la sesión muere (token expira) y
   `Router.renderizar()` revienta en `Sesion.usuario.nombre` null — el
   camino real del usuario es re-login (tarjeta de rol → credenciales) y
   click en el menú lateral; para automatización: ver secuencia CDP en el
   pitfall 9 del SKILL.md.

## Informe final para el instituto

`docs/Informe_Final_Propuesta_Instituto_Argentina.pdf` (19 págs, spec
`docs/informe_final_spec.json`) — el documento integrador NO técnico:
análisis + BD + proceso + automatización + evidencia + costos + plan.
Corrección del usuario (2026-09-13): NO parchar la propuesta vieja con un
capítulo — el "informe final" es un documento NUEVO completo, todo
sustentado con cifras medidas (60 tablas/103 FK/446 CHECK/23 UNIQUE/169
índices sobre la BD real, 112/112 e2e, 61 commits). Familia de 3 docs:
informe final integrador (dirección) / propuesta tabla-por-tabla
(cliente) / informe técnico (sistemas). Receta de maquetado y auditoría:
`informe-cliente-pdf.md` en esta misma skill.
