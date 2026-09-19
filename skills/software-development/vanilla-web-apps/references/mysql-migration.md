# Migración vanilla-JS/localStorage → PHP + MySQL (playbook validado)

Ejecutado de punta a punta en gestionest1 (sept 2026): 22 entidades, 13 vistas,
5 roles, 7 flujos de negocio — UI intacta, E2E 32/32 + verificación de navegador real.

## Arquitectura que funcionó: adaptador Store remoto con caché

La UI es síncrona (`render()` lee y pinta) — reescribirla async es inviable.
El puente: **caché hidratada + escrituras remotas**:

1. `js/datos/api.js` define un `Store` con la MISMA interfaz (`leer/obtener/buscar`
   síncronos sobre caché en memoria; `insertar/actualizar/eliminar` async contra la API).
2. `App.entrarApp()` hace `await Store.hidratar()` (carga todas las entidades en
   paralelo con `Promise.all` — sistema demo-size) ANTES de `Router.iniciar()`.
3. Tras cada escritura: `await Store.recargar(["entidades", "afectadas"])` — la
   vista re-renderiza con datos frescos sin cambiar su código de lectura.
4. `NegocioRemoto` expone los workflows de API (subirFoto, darConformidad...) y
   los módulos de negocio quedan híbridos: lecturas de caché, escrituras async.
5. Sesión: token Bearer en localStorage `ia_token` + `GET /api/me` devuelve
   `{usuario, estudiante}` — el mapeo usuario↔estudiante lo resuelve el servidor
   (FK/lookup), reemplazando las heurísticas de DNI/nombre del frontend.

**Contrato API = contrato Store**: `{ok, registro}` | `{ok, errores: [...]}`
con los MISMOS textos de error. Esto mantiene los `UI.errores(res)` y toasts intactos.

## MySQL/MariaDB — decisiones expertas que pagaron

- **"Máx 1 vigente por (estudiante, semestre)"**: columna generada
  `estado_vigente VARCHAR(20) GENERATED ALWAYS AS (IF(estado='Anulada', NULL, estado)) STORED`
  + `UNIQUE (estudiante, semestre, estado_vigente)` — la Anulada colapsa a NULL
  (múltiples NULL permitidos), la vigente colisiona. Reemplaza validación de app.
- **Seed con FKs**: las notas históricas referencian semestres que deben EXISTIR
  (el récord 2025-II requería insertar ese semestre). En localStorage no había FK
  y semillas con datos históricos mueren con 1452 al importar.
- **Seed re-ejecutable**: `SET FOREIGN_KEY_CHECKS=0; TRUNCATE ... ; SET ...=1`
  al inicio — poder re-seedear entre rondas de pruebas sin DROP DATABASE.
- **TIME de MySQL vuelve "HH:MM:SS"** — normalizar a "HH:MM" en la capa de
  respuesta (filaAJs con regex `^\d{2}:\d{2}:\d{2}$` → substr 5) o la UI muestra
  "08:00:00-10:30:00".
- **Bcrypt + rehash-on-login**: si `clave_hash` empieza con 'h' (hashSimple djb2
  legacy), comparar el hash legacy y REHASHEAR a bcrypt en el mismo login.
  Puerto exacto del djb2 JS (`>>>0` = máscara `& 0xFFFFFFFF` en PHP).
- **Códigos secuenciales** (MAT-2026I-004): tabla `secuencias_codigo` con
  `SELECT ... FOR UPDATE` — y CRÍTICO: si el caller ya abrió transacción,
  UNIRSE a ella; `beginTransaction()` dentro de transacción activa lanza
  "There is already an active transaction" y rompe TODOS los inserts.
- **Blobs centralizados**: una tabla `archivos (entidad, registro, tipo_documento,
  mime, tamano, datos MEDIUMBLOB)` con endpoint `/api/archivos/{id}`; los GET de
  registro devuelven dataURL para no romper los `<img src=data:...>` de la UI.
- **phpMyAdmin como entregable**: el usuario administra la BD en phpMyAdmin
  (localhost/phpmyadmin). Generar los .sql (01_schema, 02_views, 03_seed)
  importables por la pestaña Importar; importar por CLI (`mariadb -u root <`)
  contra el MISMO servidor hace que aparezcan al instante en su phpMyAdmin.

## PHP 8.5 puro (PDO, sin framework) — estructura

```
api/index.php        front controller (dispatch por recurso+metodo)
api/router.php       dev server: /api/* → index.php, estáticos → raíz
api/config/config.php  PDO creds + matriz de permisos ESPEJO del Sesion JS
api/src/             Database (PDO singleton), Responder, Tablas (entidad↔tabla,
                      camelCase↔snake_case), Validador (puerto del ESQUEMA JS),
                      Codigos (secuencias), Auth, Transversal (bitácora/notif)
api/handlers/        uno por dominio (Auth, Entidades CRUD genérico, + workflows)
api/sql/             01_schema.sql 02_views.sql 03_seed.sql (phpMyAdmin-ready)
api/tests/e2e.py     smoke E2E completo por curl (todos los roles y flujos)
```

- **Validador**: puerto 1:1 del `ESQUEMA` JS a PHP (mismos campos, mensajes,
  orden) — la validación ya estaba diseñada data-driven, solo se traduce.
- **Handlers de dominio ANTES del CRUD genérico** en el dispatch: los workflows
  (foto, voucher, conformidad) tienen rutas propias; el CRUD genérico atiende
  catálogos. Si el genérico captura primero, se traga rutas de workflow.
- `php -l` sobre TODO tras escribir. PHP 8.5: método `: void` NO puede hacer
  `return self::x();` — quitar el retorno o la anotación.
- MySQL LIMITADO para el usuario de app: `GRANT SELECT,INSERT,UPDATE,DELETE`
  (nunca DDL/ALL).

## La parte peligrosa: migrar la UI de sync → async

Las vistas llaman `Store.insertar(...)` síncrono. Migración en 3 frentes:

### 1. Callbacks con await: el SyntaxError que mata TODO el script
Un `await` dentro de un callback no-async es SyntaxError **de archivo completo**
— el `<script>` no se carga y TODAS las vistas quedan `undefined` (síntoma:
`VistaEstudiantes is not defined` aunque el archivo exista). Los puntos donde
se cuelan:
- callbacks de `UI.confirmar(msg, () => { ...await... })`
- `FileReader.onload = ev => { ...await... }` / `img.onload`
- `arr.forEach(b => b.onclick = () => { ...await... })` (el async va en el
  onclick, no en el forEach)
- métodos de objeto que ganan await: `guardar(dlg) {` → `async guardar(dlg) {`

**`node --check` NO detecta esto** (valida script clásico, no módulo). Verificar
con módulo: escribir a `/tmp/chk_N.mjs` con `+ "\nexport {};"` y `node --check`
— falla en awaits inválidos. Guardar como script reutilizable (`check_await.js`).

### 2. Migración masiva por regex: SIEMPRE verificar después
Sustituir `=> {` por `=> async {` con regex produce `() => async {` — SINTAXIS
INVÁLIDA (async va antes de los paréntesis). Si se automatiza, corregir con
`\(\s*\)\s*=>\s*async\s*\{` → `async () => {` y `\((\w+)\)\s*=>\s*async\s*\{` →
`async (\1) => {`, luego correr el check de módulos + `node --check` de todo.

### 3. Métodos eliminados del negocio que las vistas siguen llamando
Al migrar módulos (p. ej. `validarPrecondiciones` se fue al backend), las vistas
que lo llaman explotan en runtime. Verificación programática: extraer todos los
`Modulo.metodo` usados en vistas/ y comparar contra los definidos en negocio/
(`grep -oE` + diff). Hacerla DESPUÉS de migrar y ANTES de probar en navegador.

### Verificación UI con navegador real (browser_exec)
Flujo validado: `new_tab(url)` → login despachando submit
(`form.dispatchEvent(new Event('submit', {cancelable:true}))`) → navegar hash →
afirmar sobre el DOM. Trampas:
- `js()` no acepta `await` top-level; usar `js("new Promise(r => setTimeout(r, N))")`
  (js resuelve promesas automáticamente).
- Un `<dialog>` MODAL ABIERTO bloquea el hashchange: cerrar el modal antes de
  navegar (`UI.cerrarModal()`).
- Los `<datalist>` no responden a eventos sintéticos para seleccionar opciones:
  setear `input.value = "CODIGO — etiqueta"` y disparar `Event('change')`
  directamente (el onchange del modal parsea el código antes del " — ").
- Cada rol requiere salir (botón + confirmar modal) y re-login — el botón de
  confirmación se encuentra por texto (Salir|Cerrar|Confirmar).

## Orden de migración que evitó romper todo
1. Backend completo + seed + E2E por curl (32 pruebas) — commit.
2. Adaptador api.js (Store remoto) + módulos de negocio async — sin tocar vistas.
3. Vistas: migración async de callbacks + fixes de métodos faltantes.
4. index.html: quitar store.js/semillas.js, poner api.js; app.js hidrata.
5. Verificar en navegador por rol, flujo completo UI→MySQL, commit.

Los tests de lógica Node antiguos (que cargaban store.js) quedan obsoletos con
el Store remoto: su valor migra a `api/tests/e2e.py` (curl contra la API real).
