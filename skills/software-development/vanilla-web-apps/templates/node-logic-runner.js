/* node-logic-runner.js — plantilla: probar capas datos+negocio de una app
 * vanilla JS (localStorage) en Node, sin navegador.
 *
 * USO:
 *   1. Copiar a <proyecto>/tests/pruebas-logicas.js
 *   2. Ajustar CONFIG: raíz js/ y lista de archivos a cargar (solo datos/ + negocio/).
 *   3. node tests/pruebas-logicas.js   → exit 0 si todo pasa.
 *
 * Por qué este diseño (lecciones de una sesión real):
 *   - eval() bajo "use strict" NO comparte const/function con el caller:
 *     se concatena todo (shim + fuentes + cuerpo de pruebas) en UN solo new Function.
 *   - El shim de localStorage debe ser FUNCIONAL (Proxy), no stub vacío:
 *     las apps llaman Object.keys(localStorage) para purgar claves.
 *   - El cuerpo de pruebas se separa del runner con un marcador construido por
 *     concatenación ("/*==" + "CORTE==*/") para que el propio runner no lo
 *     contenga completo (si no, el split corta a mitad de línea del runner).
 *   - Con DOM puro fuera del alcance, no hace falta stub de document/window.
 */
"use strict";

const fs = require("fs");
const path = require("path");

/* ======== CONFIG — ajustar al proyecto ======== */
const BASE_JS = path.join(__dirname, "..", "sistema", "js");
const ARCHIVOS = [
  "datos/esquema.js", "datos/store.js", "datos/semillas.js",
  "negocio/autenticacion.js", "negocio/pagos.js", "negocio/matriculas.js",
  "negocio/tramites.js", "negocio/notas.js"
];
/* ============================================= */

const fuente = ARCHIVOS.map(a => fs.readFileSync(path.join(BASE_JS, a), "utf8")).join("\n");
const MARCADOR = "/*==" + "CORTE==*/";
const partes = fs.readFileSync(__filename, "utf8").split(MARCADOR);
const cuerpo = partes[partes.length - 1];

/* localStorage funcional vía Proxy (no stub) */
const shim =
  'const __almacen = {};\n' +
  'globalThis.localStorage = new Proxy({}, {\n' +
  '  get: (t, k) => {\n' +
  '    if (k === "getItem") return key => (key in __almacen ? __almacen[key] : null);\n' +
  '    if (k === "setItem") return (key, v) => { __almacen[key] = String(v); };\n' +
  '    if (k === "removeItem") return key => { delete __almacen[key]; };\n' +
  '    if (k === "key") return i => Object.keys(__almacen)[i];\n' +
  '    if (k === "length") return Object.keys(__almacen).length;\n' +
  '    return __almacen[k];\n' +
  '  },\n' +
  '  set: (t, k, v) => { __almacen[k] = String(v); return true; },\n' +
  '  deleteProperty: (t, k) => { delete __almacen[k]; return true; },\n' +
  '  has: (t, k) => k in __almacen,\n' +
  '  ownKeys: () => Object.keys(__almacen),\n' +
  '  getOwnPropertyDescriptor: (t, k) => (k in __almacen ? { enumerable: true, configurable: true, writable: true, value: __almacen[k] } : undefined)\n' +
  '});\n';

new Function("require", "console", "process", "globalThis",
  '"use strict";\n' + shim + fuente + "\n" + cuerpo
)(require, console, process, globalThis);
return;

/*==CORTE==*/
/* ===================== CUERPO DE PRUEBAS (reemplazar) =====================
   Vive en el mismo alcance que las capas cargadas: Store, Sesion, etc. están
   disponibles directamente. Mini framework mínimo: */

let pasadas = 0, fallidas = 0;
function prueba(nombre, fn) {
  try { fn(); pasadas++; console.log("  ✓ " + nombre); }
  catch (e) { fallidas++; console.log("  ✗ " + nombre + " → " + e.message); }
}
function afirmar(cond, msg) { if (!cond) throw new Error(msg || "afirmación fallida"); }
function iguales(a, b, msg) {
  if (JSON.stringify(a) !== JSON.stringify(b))
    throw new Error((msg || "no iguales") + " | " + JSON.stringify(a) + " vs " + JSON.stringify(b));
}

/* --- ejemplo de estructura (adaptar al dominio del proyecto) --- */
console.log("== SEMILLAS ==");
prueba("Semillas cargadas", () => {
  afirmar(Store.leer("usuarios").length > 0, "usuarios sembrados");
});
console.log("== NEGOCIO ==");
prueba("Ejemplo: precondición de negocio", () => {
  afirmar(true);
});

console.log("\n===== RESULTADO: " + pasadas + " pasaron, " + fallidas + " fallaron =====");
process.exit(fallidas ? 1 : 0);
