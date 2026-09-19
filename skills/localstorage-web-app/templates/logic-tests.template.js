/* pruebas-logicas.template.js — headless business-logic harness for vanilla JS + localStorage apps.
   Copy into <app>/tests/, adapt the ARCHIVOS list and the test bodies. Run: node tests/pruebas-logicas.js

   How it works: this file is BOTH the loader and the tests. Everything after the /*==CORTE==*/ marker
   is the test body; the loader reads its own source, splits on the marker, concatenates the app
   sources + test body into a single scope, and evals them with a working localStorage shim. */
"use strict";

const fs = require("fs");
const path = require("path");

/* EDIT: relative paths from <app>/js to every source file, in load order */
const ARCHIVOS = [
  "datos/esquema.js", "datos/store.js", "datos/semillas.js",
  "negocio/autenticacion.js", "negocio/pagos.js", "negocio/matriculas.js", "negocio/tramites.js"
];
const base = path.join(__dirname, "..", "js");

const fuente = ARCHIVOS.map(a => fs.readFileSync(path.join(base, a), "utf8")).join("\n");
const MARCADOR = "/*==" + "CORTE==*/";            /* split marker (assembled so it can't match itself) */
const partes = fs.readFileSync(__filename, "utf8").split(MARCADOR);
const cuerpo = partes[partes.length - 1];

/* functional localStorage shim for Node (Proxy over a plain object) */
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
/* ===== mini framework ===== */
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

console.log("== SEMILLAS Y CATÁLOGOS ==");
prueba("Semillas cargadas: entidades y conteos esperados", () => {
  afirmar(Store.leer("usuarios").length === 4, "4 usuarios");
  afirmar(Store.leer("semestres").length === 2, "2 semestres");
  /* EDIT: replace with this app's entities and expected seed counts.
     Do NOT assert with [0]-style indexing into collections that demo data can reorder —
     pick records explicitly: Store.obtener("estudiantes", "E0005") */
});

console.log("== AUTENTICACIÓN Y ROLES ==");
prueba("Login por rol y menú filtrado", () => {
  /* EDIT: app credentials; assert BOTH positive and negative logins (removed roles must fail) */
  afirmar(Sesion.entrar("admin", "admin123").ok, "login admin");
  afirmar(!Sesion.entrar("admin", "malaclave").ok, "clave incorrecta rechazada");
  afirmar(Sesion.menuPorRol().some(m => m.id === "catalogos"), "rol operativo ve catálogos");
  /* EDIT: second role — assert it does NOT see the first role's exclusive views */
});

console.log("== FLUJO DE NEGOCIO (reemplazar por el flujo de esta app) ==");
prueba("Precondición bloquea y luego permite", () => {
  /* pattern: prove the precondition FAILS without its requirement, add the requirement, assert success */
});

console.log("\n===== RESULTADO: " + pasadas + " pasaron, " + fallidas + " fallaron =====");
process.exit(fallidas ? 1 : 0);
