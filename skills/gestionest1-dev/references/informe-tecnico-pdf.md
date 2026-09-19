# Informe técnico del sistema en PDF (receta verificada 2026-09-12)

Genera `docs/Informe_Tecnico_Sistema_Gestion_Estudiantes.pdf` (~12 págs A4) con
datos REALES del sistema vivo — nunca de memoria. Producto final entregado en esa
fecha: 9 secciones (resumen ejecutivo, arquitectura, BD 3NF, 8 flujos de negocio,
seguridad, verificación E2E, diagrama ER, hallazgos, conclusión).

## 1. Recolectar inventario vivo (antes de redactar)

Todo por SQL directo / conteos — el informe se sustenta con cifras medidas:

```sql
-- Tablas, motor, charset
SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='gestion_estudiantes';
-- FKs, CHECKs, índices
SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA='...' AND REFERENCED_TABLE_NAME IS NOT NULL;
SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_TYPE='CHECK' AND TABLE_SCHEMA='...';
SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='...';
-- Tamaño, conteos por tabla, usuarios por rol, denormalizaciones
SELECT ROUND(SUM(data_length+index_length)/1024/1024,1) FROM information_schema.TABLES WHERE TABLE_SCHEMA='...';
SELECT * FROM meta;  -- denormalizaciones_aceptadas, schema_version
```

Más: `git log --oneline` + `git rev-list --count HEAD` (evolución), `wc -l` de
api/ y js/ (LOC), conteos de `beginTransaction` por handler (transacciones),
última salida E2E (112 checks OK por sección — awk sobre la salida), ventana de
navegación CDP ya verificada en la sesión.

## 2. Generar el PDF (entorno sin pip global — PEP 668)

```bash
cd ~/projects/gestionest1/docs
uv venv .venv_pdf
uv pip install --python .venv_pdf/bin/python reportlab pypdf pdfplumber
# spec JSON: {"title","author","page_size":"A4","elements":[heading|paragraph|table|image|pagebreak]}
.venv_pdf/bin/python ~/.hermes/skills/productivity/pdf/scripts/pdf_create.py informe_tecnico_spec.json -o Informe_Tecnico_Sistema_Gestion_Estudiantes.pdf
```

- El ER del sistema ya existe: `docs/diagrama_bd.png` → elemento `{"type":"image","width":480}`.
- Cuidado con JSON: escribir cada parte como objeto válido y fusionar arrays en Python (un archivo de solo-array falla la validación de write_file).

## 3. Pitfall del glifo "→" (reportlab + Helvetica)

ReportLab renderiza "→" con la fuente Symbol integrada: **se VE bien en el PDF**
pero al extraer/copiar texto sale como "fi" (verificado con pdfplumber
`page.chars` → fontname Symbol). En un informe técnico que se va a copiar o
indexar, reemplazar "→" por "->" en todos los textos/celdas del spec ANTES de
generar (verificación posterior: 0 líneas con " fi " suelto).

## 4. Verificación del PDF (siempre)

```bash
.venv_pdf/bin/python ~/.hermes/skills/productivity/pdf/scripts/pdf_read.py Informe...pdf --meta   # page_count, título, autor
# spot-check de texto: 18 strings de secciones clave → 18/18 presentes
# página del diagrama: pdfplumber page.images == 1, ancho 480
# última página con contenido: la conclusión debe terminar con la línea de fecha de generación
```

Cosmético conocido: un pagebreak tras la imagen del ER deja una última página
casi vacía (solo folio) — aceptable, o quitar el salto final.

## 5. Limpieza

Borrar `.venv_pdf/`, renders de verificación y specs parciales; conservar
`informe_tecnico_spec.json` (fuente regenerable) junto al PDF en `docs/`.
