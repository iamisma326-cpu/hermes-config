# Informe para el CLIENTE en PDF + auditoría de maquetado sin visión (verificado 2026-09-12)

Genera `docs/Propuesta_BD_y_Proceso_Instituto_Argentina.pdf` (14 págs A4) —
la versión NO técnica del informe (lector: dirección del instituto), desde
`docs/informe_cliente_spec.json` (spec reportlab, 164 elementos; venv y
comando en `informe-tecnico-pdf.md` §2, misma receta). Diferencia con el
informe técnico: CERO terminología de implementación — se audita con lista de
PALABRAS PROHIBIDAS (migraci, MariaDB, MySQL, PHP, E2E, GLIBC, skill, "la app",
"auditoría post") — y SÍ glosario para el lector no técnico (13 términos).

## Estructura que pasó todos los checks

Portada con Objetivo/Alcance/Cómo leer este documento · 1. Resumen ejecutivo ·
2. Beneficios (independencia del proveedor, contraseñas cifradas de forma
irreversible) · 3. Las 56 tablas POR MÓDULO (7 módulos funcionales) · 4. Roles
del instituto · 5. Proceso completo extremo a extremo (narrativa de la
trayectoria de un alumno) · 6. Garantías del diseño · GLOSARIO · ANEXO con
diagrama ER (`{"type":"image","width":480}`).

## Auditoría de maquetado SIN visión (métrica geométrica)

Tres falsos que rompieron la v4 — y su corrección:

1. **Char-count por página miente en páginas con imagen**: la página del
   diagrama ER tenía 118 chars extraídos pero estaba 96% llena (la imagen no
   produce texto). NUNCA diagnosticar huecos solo con
   `len(page.extract_text())` — medir ocupación geométrica:
   ```python
   ys = [c['bottom'] for c in page.chars] + [im['bottom'] for im in page.images]
   fill = max(ys) / page.height   # >0.9 = página llena, aunque el texto sea poco
   ```
2. **Frases cortadas en el salto de página = falso negativo**: "independencia
   del proveedor" partido entre p2/p3 hacía fallar el check de presencia.
   Normalizar SIEMPRE el documento completo antes de buscar frases:
   ```python
   full = ' '.join(re.sub(r'\s+', ' ', (p.extract_text() or '')) for p in pdf.pages)
   ```
3. **Verificar sección ≠ verificar página**: el "FALTAN" del glosario mirando
   solo p13 era artefacto — el glosario EMPIEZA a mitad de p12. Los checks de
   contenido van contra el documento completo, no contra una página suelta.

## Estrategia de pagebreaks (lo que fijó v4→v5: 15→14 págs, todas 96% llenas)

- Pagebreak explícito antes de una sección grande deja huérfana la página
  previa si no estaba llena (síntoma: 2 líneas de texto + 96% vacío, o heading
  que abre página con <3 líneas encima).
- Por defecto: SIN pagebreaks (dejar fluir el contenido). Agregar SOLO donde
  el contenido medido necesita página propia — calcular ANTES de decidir:
  ```python
  alto_pt = ancho_pt_destino * h_px / w_px   # diagrama 5270x2400px a 480pt → 219pt
  # A4 útil con márgenes ≈ 742pt → heading + intro + imagen SÍ caben juntos
  ```
- Al reconstruir el spec por contenido (no por índice), colapsar pagebreaks
  consecutivos duplicados.

## Checks finales (todos deben dar verde antes de entregar)

- 56/56 tablas del catálogo mencionadas en el texto (catálogo regenerable:
  una línea por tabla desde la BD + notas de denormalización de meta).
- 0 palabras prohibidas (terminología de implementación) en el texto completo.
- Portada (Objetivo/Alcance/Cómo leer), glosario 13/13 términos, 5 secciones clave.
- Frases de venta (independencia del proveedor, cifrado irreversible) — con
  whitespace normalizado entre páginas.
- Ninguna página de texto con llenado geométrico bajo (~<0.9); las páginas
  de imagen se validan por fill, no por chars.

## Artefactos y versionado

- El spec se itera versionado en /tmp (v1..v5); SIEMPRE copiar la versión
  FINAL a `docs/informe_cliente_spec.json` — /tmp muere con la sesión.
- `docs/prompt_diagrama_bd.txt` (54KB): prompt para regenerar el ERD
  relacional en otra IA. Regenerable con: pg_dump de la BD + conteos de
  pg_constraint + los 7 módulos (extraíbles del propio informe_cliente_spec.json,
  sección 3: párrafos `<b>tabla (N).</b>` bajo cada heading de módulo).
  Pitfall crítico del pg_dump de PG 18: las FKs salen en UNA línea
  (`ADD CONSTRAINT fk_x FOREIGN KEY (col) REFERENCES public.t(cod);`) — un
  regex multilínea esperando `REFERENCES` en línea propia devuelve 0;
  gate obligatorio: len(regex) == conteo de pg_constraint antes de usar el DDL.
  Contar con anclaje de línea al verificar el prompt armado: `grep -c "^CREATE TABLE"`
  (un conteo sobre todo el texto suma las menciones en prosa).
