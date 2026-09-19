---
name: vanilla-web-apps
description: Build/test vanilla HTML+CSS+JS apps with localStorage CRUD — and migrate them to PHP+MySQL later.
version: 1.0.0
author: Hermes Agent (auto-curated)
license: MIT
metadata:
  hermes:
    tags: [javascript, web, crud, localStorage, testing, frontend]
    related_skills: [python-patterns, e2e-testing]
---

# Vanilla JS web apps with simulated persistence (CRUD sin backend)

## When to Use
- El usuario pide un sistema/app en HTML5 + CSS3 + JavaScript (sin frameworks, sin PHP/DB): "CRUD simulado", "por ahora sin base de datos", típico de sistemas administrativos/académicos.
- Hay que verificar la lógica de negocio de una app así SIN abrir un navegador.

## Arquitectura: 3 capas con nombres migrable 1:1 a un backend futuro

```
index.html
css/  base.css | layout.css | componentes.css | print.css
js/datos/    esquema.js  store.js  semillas.js
js/negocio/  <entidad>.js          (reglas, transiciones, precondiciones)
js/ui/       componentes.js documentos.js router.js app.js
js/ui/vistas/<vista>.js
```

- `Store` expone `leer/escribir/insertar/actualizar/eliminar/obtener/buscar/validar` — nombres espejo de una capa DAL (listar/insertar/actualizar/eliminar) para que migrar a PHP+MySQL sea un cambio 1:1, no una reescritura.
- Un objeto `ESQUEMA` (por entidad: `id`, `campos[{n,req,tipo,ref,opciones,pk,patron,min,max,soloLectura}]`) es la ÚNICA fuente de verdad: impulsa tanto la validación (`Store.validar`) como el render genérico de formularios (`UI.formulario`).
- `semillas.js`: seeding versionado (clave `version` en localStorage; si coincide, no resiembra), usuarios demo por rol + datos realistas locales.
- La UI nunca toca localStorage directo: todo pasa por `Store` / capa negocio. Códigos autogenerados y fechas de operación nunca editables por el usuario.
- Sesión + roles: hash router (`#/vista/param`), menú declarativo filtrado por rol, sesión persistida en una clave localStorage separada de los datos.

## Gotchas que producen bugs reales (encontrados por pruebas, no en teoría)
1. **Autogenerar el ID ANTES de validar** en `Store.insertar` — si validas primero, un campo id `required` falla siempre en los INSERT.
2. **Códigos con guiones** (`MAT-2026I-004`): `siguienteId` debe extraer los dígitos del ÚLTIMO segmento tras el guion, no de todo el string (tomar todos da `2026004`).
3. **Shorthand `{ semestre, ... }`** referencia una variable llamada `semestre`; si la local se llama `sem` es un ReferenceError solo en runtime. Preferir siempre `{ semestre: sem }`.
4. Tras un `Store.actualizar` dentro del mismo flujo, **re-obtener el registro** (`Store.obtener`) antes de calcular valores derivados: el objeto en mano quedó desactualizado.
5. Comillas anidadas: strings JS en comillas simples y atributos HTML en dobles; una sola anidación del mismo tipo = SyntaxError (se cuela hasta `node --check`).
6. **Semillas versionadas: cambiar contenido de `semillas.js` SIN subir `version` = los cambios no existen.** Si solo cambias usuarios/credenciales/demo data y dejas la misma clave `ia_version`, los navegadores conservan el localStorage viejo y el usuario reporta "el login me dice usuario incorrecto y lo pongo bien" / "no veo que se actualizó el apartado". **Recurrencia: esto falló 3× en el mismo proyecto.** Regla endurecida: el bump de versión va en el MISMO lote de edición que el contenido nuevo, y la clave aparece DOS veces en semillas.js — el guard (`if (localStorage.getItem(...) === "X") return;` arriba) y el `localStorage.setItem(..., "X")` (abajo). Actualizar solo el setItem deja el guard stale (FATAL: no resembra); solo el guard, deja el setItem stale. También actualizar strings que mencionen la versión (detalle de bitácora). Y decirle al usuario que recargue (Ctrl+Shift+R).
7. **Selectores por entidad+clave con ciclo de vida**: si una entidad puede tener varias filas por la misma clave (matrícula Anulada vieja + trámite En trámite nuevo), `buscar()[0]` devuelve la equivocada. Definir prioridad: `{ "En trámite": 0, "Matriculado": 1, "Reservada": 1, "Anulada": 2 }` y ordenar antes de tomar la primera.
8. **Códigos autogenerados en lógica manual**: si la capa negocio inserta un registro directamente con `Store.insertar`, debe generar el código con el MISMO formato que el resto del sistema (`MAT-2026I-004`), no confiar en el autogenerado genérico (`0004`). Inconsistencia de formato rompe sorts, regex de tests y `siguienteId`.
9. **Context overflow por patches repetitivos**: cuando un cambio coordinado toca 5+ archivos (agregar rol, nuevo módulo), cada llamada individual a `patch` consume contexto. Con 10+ patches, la sesión puede agotarse antes de terminar. Solución: usar `execute_code` con `from hermes_tools import patch` para batch de todas las ediciones en UNA sola llamada.
10. **patch sin cambio = desperdicio de contexto**: si `old_string === new_string` (lectura stale), `patch` retorna "already applied" pero igual consume contexto. Siempre verificar contenido actual antes de parchear, especialmente tras otras ediciones en la misma sesión.
11. **Nuevo archivo de negocio → agregarlo a la lista `archivos` del runner de pruebas.** Síntoma cuando falta: TODOS los tests nuevos (y algunos viejos) fallan con "X is not defined" — no es un bug de la app, es que el runner no carga el módulo. Fix de una línea, pero hay que reconocer el síntoma en vez de empezar a "arreglar" la app.
12. **Anclas de patch: no arrastrar la firma del método siguiente.** Si el `old_string` termina en la línea de firma del método que sigue (p. ej. `leerFormulario(contenedor) {`), el `new_string` DEBE re-emitirla; olvidarla = SyntaxError inmediato que parte el archivo. Anclar en un límite estable (fin de método + coma) o re-emitir lo arrastrado.
13. `btoa()` existe en Node ≥16 — útil para sembrar PDFs dataURL mínimos (silabos de ejemplo) sin archivos binarios en el repo.

## Impresión de documentos (fichas, nóminas, constancias, recibos)
Truco `@media print` que imprime solo el documento:
```css
@media print{
  body *{visibility:hidden}
  #area-documento,#area-documento *{visibility:visible}
  #area-documento{position:absolute;left:0;top:0;width:100%}
  .doc-acciones{display:none!important}
}
```
Overlay con el documento + botones Imprimir/Cerrar; solo `#area-documento` sale en el PDF impreso.

## Probar la lógica en Node SIN navegador — plantilla: `templates/node-logic-runner.js`
Copiar la plantilla a `tests/pruebas-logicas.js`, ajustar la CONFIG (rutas y lista de archivos) y ejecutar `node tests/pruebas-logicas.js`. Puntos clave que la plantilla ya resuelve:
- Cargar solo las capas `datos/` + `negocio/` (sin dependencias de DOM). No hace falta stub de document/window si la UI queda fuera.
- `eval()` bajo `"use strict"` NO comparte declaraciones `const`/`function` con el caller: hay que concatenar fuentes + cuerpo de pruebas dentro de UN solo `new Function(...)`.
- El shim de localStorage debe ser funcional, no stub: Proxy con `getItem/setItem/removeItem/key/length/ownKeys` — las apps llaman `Object.keys(localStorage)` para purgar claves.
- Separar el cuerpo de pruebas del runner con un marcador construido por concatenación (`"/*==" + "CORTE==*/"`) para que el propio runner no contenga el marcador completo (si no, el split corta a mitad de línea del runner).
- Este enfoque encontró 5 bugs reales en una sola sesión, antes de cualquier prueba visual.

## Secuencia de verificación
1. `for f in $(find js -name '*.js'); do node --check "$f"; done` — sintaxis de todo antes de nada.
2. Pruebas de lógica en Node (plantilla) — negocio completo: precondiciones, transiciones de estado, validaciones, conteos/orden de reportes.
3. Recién entonces navegador (servidor estático `python -m http.server` + E2E manual).

## Disciplina de verificación
- Pruebas de lógica pasando ≠ verificación visual. Si el tool de navegador queda a la espera de aprobación del usuario (popup de depuración remota), reportarlo como pendiente: nunca afirmar que la UI fue verificada.

## Probar el FLUJO de punta a punta (no solo reglas sueltas)
Las pruebas unitarias de negocio pueden estar verdes y aun así el flujo completo estar roto (huecos de orquestación: nadie llama a X, la etapa nunca avanza, un módulo no se integra). Complementar con una simulación de flujo: un script que ejecuta el recorrido del usuario paso a paso contra los módulos de negocio y imprime el estado tras cada paso. Plantilla: `templates/node-flow-sim.js`. Esta técnica encontró en una sesión: un helper que devolvía el registro equivocado, un código malformado, una etapa que nunca se actualizaba y un módulo de notificaciones nunca invocado — con las pruebas unitarias en verde.

## Verificación headless de VISTAS (render real sin navegador)

Pruebas de negocio verdes ≠ la vista renderiza. Un dashboard puede quedar en blanco por un
`ReferenceError` en el render (variable declarada dentro de una rama `if/else` y usada después
a nivel de función — bug real encontrado así). Ejecutar el `render()` REAL de la vista contra
un contenedor falso y afirmar sobre el HTML generado:

```js
let html = "";
const cont = { set innerHTML(v) { html = v; }, get innerHTML() { return html; } };
try { VistaX.render(cont, ["subvista"]); } catch (e) { console.log("ERROR:", e.message); }
afirmar(html.includes("texto esperado"), "la vista pinta la sección");
```

Setup (el bundle declara sus PROPIOS globals `const UI/Documentos/Router` en componentes.js,
documentos.js, router.js — NO pasarlos como parámetros de `new Function(...)`: SyntaxError
"Identifier 'X' has already been declared"). Lo que sí se necesita como globals reales antes
de invocar: `localStorage` (shim funcional), `location = { hash: "#/vista" }`,
`window = { scrollTo(){} }`, y un `document` falso (`querySelectorAll: () => []`,
`getElementById: () => null`, `createElement`, `addEventListener`). Cargar solo
datos/ + negocio/ + componentes/documentos + la vista bajo test (no app.js ni router.js:
llaman a `document.addEventListener`/`getElementById` al iniciar). Flujo real de la sesión:
render lanza excepción → se corrige el alcance de la variable → render OK y el HTML contiene
las secciones esperadas. Verifica PINTADO sin navegador y sin permisos de depuración remota.

### "No veo los cambios" — escalera de diagnóstico (en este orden, 2-3 min)
1. **Disco**: `grep -c "<marca>" archivo` — ¿el cambio está en el archivo? (si no, falta commit o la edición no aplicó).
2. **Servido**: `curl -s http://localhost:PUERTO/ruta/archivo.js | grep -c "<marca>"` — ¿el servidor sirve la versión nueva? Un puerto puede estar sirviendo OTRO proyecto (en esta máquina :80 era Apache/LAMP ajeno al proyecto).
3. **Puerto vivo**: `ss -tlnp | grep <puerto>` y `curl -s -o /dev/null -w "%{http_code}"`. Si murió, relanzar `python3 -m http.server <puerto>` — OBLIGATORIO con `terminal(background=true)` (foreground rechaza procesos long-lived) y verificar con curl en un comando aparte.
4. Solo entonces: caché del navegador (Ctrl+Shift+R) o versión de semillas (gotcha 6).

## Verificación E2E en navegador REAL (Chrome + CDP) — la prueba definitiva

Cuando la escalera anterior no cierra la disputa ("sigo sin ver los botones" tras varias rondas),
deja de argumentar y DEMUÉSTRALO manejando un Chrome real por CDP. Técnica validada de punta a
punta en este proyecto:

1. **Servidor primero**: lanzar `python3 -m http.server <puerto>` con `terminal(background=true)`
   (foreground rechaza long-lived) y verificar con `curl` en comando aparte. En esta máquina el
   :80 era Apache sirviendo OTRO proyecto (LAMP) y el puerto del proyecto estaba muerto — causa
   real de un "no lo veo" de 3 rondas.
2. **Chrome con puerto de depuración** (ver `desktop:linux-desktop-automation` y su
   `scripts/fcc_cdp.py` — cliente CDP listo): `--remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-agent --ozone-platform=wayland --remote-allow-origins=*` con `terminal(background=true)`,
   luego `curl -s http://localhost:9222/json` para confirmar el target.
3. **Conducir el flujo por `Runtime.evaluate`**: elegir rol (`querySelector('[data-rol=…]').click()`),
   login despachando el submit (`form.dispatchEvent(new Event('submit', {cancelable:true}))`),
   navegar por hash, abrir modales, y AFIRMAR sobre el DOM real (¿existe el botón?, ¿cuántos
   inputs file?, ¿qué chips?, ¿qué dice el toast?).
4. **Simular selección de archivo SIN diálogo del SO**: `new File([bytes], 'nombre.pdf', {type:'application/pdf'})` → `DataTransfer` → `input.files = dt.files; input.dispatchEvent(new Event('change'))`. Así se prueba el circuito completo de subida (FileReader → dataURL → store) sin tocar el filesystem del host.
5. Reportar con la salida textual del CDP (verificado punto por punto) en lugar de "debería funcionar": en esta sesión esto cerró el ciclo y demostró que el problema era de servido/caché, no de código.

Límite de cortesía: 3 rondas de "no lo veo" sin evidencia de navegador = saltar directo a esta técnica.

## Coordinated multi-file changes (adding a new role, new module, etc.)

When a change touches 5+ files as a unit (e.g. adding a new role touches esquema.js,
autenticacion.js, index.html, semillas.js, plus vista files), individual `patch` calls
inflate context fast and can cause session timeout before the change is complete.

**Preferred approach**: use `execute_code` with `from hermes_tools import patch, read_file`
to batch all edits in a single call. The script reads each file, applies the patch
programmatically, and reports success/failure — one context entry instead of N.

**Adding a new role — checklist (all must change together)**:
1. `esquema.js` → add to `ROLES` array
2. `index.html` → add role-selector card (button[data-rol] + SVG icon + description)
3. `autenticacion.js` → update `menuPorRol()`: add role-specific menu items, update
   existing `"TODOS"` entries to explicit role lists (a new role seeing everything
   via TODOS is a bug)
4. `semillas.js` → add demo user for the new role + bump version
5. Vista files → create placeholder vistas for new menu items (or show "próximamente")
6. Tests → add role to login test, menu-filter test

**cp -r pitfall with existing directories**: if the target directory already exists,
`cp -r source dest` creates `dest/source/` (nested). Use `cp -r source/. dest/` or
`rsync -a source/ dest/` instead. Always verify with `ls dest/` after copying.

## Roles: gobernanza, no solo menús
- La matriz de roles vive en TRES lugares y deben coincidir: `ROLES` en esquema.js, menú en autenticacion.js, y guardas en cada vista/botón (`Sesion.esRol/puedeEditar...`). Un botón visible a un rol sin permiso en capa negocio = error confuso en runtime.
- Patrón validado para login con selector de rol (pantalla previa de tarjetas de rol): validar credenciales primero y LUEGO comparar `Sesion.usuario.rol` con el rol elegido; si difiere, hacer `Sesion.salir()` y mostrar error — nunca dejar sesión activa con rol no elegido.
- El mapeo usuario-demo ↔ estudiante-demo debe ser determinista (por DNI/usuario = DNI), no por nombre: los nombres cambian, los DNI no.
- Simular lo que requiere backend, aislado para migrar: SMTP → módulo notificaciones con flag `emailSimulado`; archivos → dataURL comprimidos (canvas: resize + JPEG 0.85, límites 1–2.5MB); PDF real del lado cliente → jsPDF. Cada pieza en su propio módulo de negocio con validaciones de formato/tamaño/reintentos.
- Flujos con estados documentales (subir voucher/foto → validación en paralelo por roles distintos → conformidad): sincronizar flags derivados en la entidad madre desde cada validador, y notificar al estudiante en cada evento. Verificar que TODAS las transiciones de etapa ocurren realmente (bug típico: la etapa declarada en el esquema nunca se asigna en el código).
- **Formularios self-service: identidad derivada de la sesión, no seleccionable.** Cuando el rol logueado crea registros sobre sí mismo (solicitud de trámite, reclamos), el campo de identidad se muestra de solo lectura ("Solicitante: <nombre> (<código>)") y la capa negocio toma el código vía el mapeo usuario↔estudiante — un selector de estudiante dentro del portal del estudiante no tiene sentido (corrección explícita del usuario). El selector solo existe para roles de atención (Secretaría/Admin registran en nombre de otros).
- **Paneles de subida de documentos: sección independiente visible en TODAS las etapas.** Voucher/foto deben vivir en su propia tarjeta ("Mis documentos") al final de la vista, visible sin matrícula, en trámite y ya matriculado — no incrustados en la rama de un estado concreto (el usuario lo pidió dos veces; la foto del carné se carga antes o después del trámite).
- **Catálogos de enlaces externos (cursos gratuitos, recursos):** una tarjeta por PLATAFORMA distinta — varias tarjetas con la misma URL de destino no tiene sentido (corrección del usuario); los cursos internos de un portal se mencionan en el nombre de la tarjeta. Verificar cada enlace con búsqueda web antes de sembrarlo (plataformas mueren: Google Actívate migró a Grow with Google; el Aula Virtual de Fundación Telefónica ya no ofrece cursos abiertos; los nombres de cursos del MTPE son los publicados en su web). Agregar test que afirme: sin URLs duplicadas y todas https.
- **Requisitos con archivo dentro del formulario de creación, no en un paso posterior.** Si un trámite/solicitud pide adjuntos (DNI, foto, voucher), el modal de creación muestra cada requisito con su botón "Adjuntar" + input file oculto (accept según regla: PDF-only lleva chip "PDF obligatorio"); al registrar se valida formato ANTES de crear el registro (un adjunto inválido bloquea, no se crea "para corregir después") y los archivos se inyectan como requisito entregado post-inserción (FileReader → dataURL). El modal posterior de "Requisitos" queda para revisión/validación del rol atención, no como única vía de carga (corrección del usuario: "ahi mismo esté los botones para subir").
- **Sembrar demo-PDFs sin binarios en el repo:** `btoa()` de un PDF mínimo de una página (objeto catálogo + página + fuente Helvetica) como dataURL; suficiente para probar "Descargar PDF" real en el navegador.
- **web_search ANTES de sembrar catálogos externos y al dudar de vigencia:** los agregadores y plataformas educativas cambian rápido; verificar que la URL exista hoy y que los nombres de cursos coincidan con los publicados. Un catálogo con enlaces muertos destruye la credibilidad del módulo entero.
