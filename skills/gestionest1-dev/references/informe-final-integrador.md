# Informe FINAL — docs/Informe_Final_Propuesta_Instituto_Argentina.pdf (2026-09-13, v3 simplificado)

## Qué ES este documento (correcciones del usuario, en orden cronológico)

1. **Integrador, no parche** (v1): la primera entrega añadió un capítulo a la
   Propuesta BD existente. Usuario: quería un documento NUEVO, completo, no
   técnico, todo sustentado.
2. **Re-enfoque a automatización** (v2, misma mañana): diagnóstico honesto —
   Jaguar en tesorería, DRELM para validar el voucher, Mesa de Partes Virtual
   (jedu.pe/tramite-externo), matrícula 100% presencial, canje presencial
   (comunicado 2025 de canje-por-correo DESACTUALIZADO) — y el flujo nuevo
   detallado + costos de deploy (VPS para WAHA).
3. **Simplificación a informe GENERAL** (v3, commit 66e97ed, 16 págs):
   "solo es un informe de la propuesta en general". Quedan FUERA:
   - costo del SIM ("innecesario" — fuera de 8.1, de 7.2 y del glosario)
   - montos de trámites para alumnos (matrícula 80, laboratorio 50, carné
     15, duplicado 10, extemporánea 20 → solo "el catálogo vigente")
   - cap. GARANTÍAS (las 112 comprobaciones en verde)
   - cap. PLAN DE IMPLEMENTACIÓN (4 semanas, fases, acompañamiento)
   => Regla de clase: un informe de propuesta para la dirección describe QUÉ
   se propone, CÓMO operará el día a día y CUÁNTO cuesta. Sin plan de
   adopción ni métricas internas de verificación — la evidencia técnica
   vive en el informe técnico hermano. También limpiar menciones sueltas:
   resumen ejecutivo, intro, guía del documento, objetivo 5, recomendación
   final (el "112" aparecía en 4 sitios además del capítulo entero).

## Estructura vigente (v3: 9 capítulos + glosario, 16 págs)

1. Resumen ejecutivo · 2. Los objetivos de la propuesta · 3. Cómo opera hoy
el instituto: Jaguar, la DRELM y la Mesa de Partes Virtual · 4. La propuesta
· 5. El nuevo proceso completo, paso a paso · 6. La memoria del proceso: las
tablas matrices · 7. La automatización por WhatsApp (opciones A/B, decisión,
lo ya construido) · 8. Los costos completos del despliegue (escenarios:
equipo propio = electricidad 10-15 soles/mes; VPS 20-45 soles/mes; 5 años;
vs Jaguar 6,000+IGV anual = 35,400/5 años) · 9. Conclusión · GLOSARIO.
Spec vivo: docs/informe_final_spec.json (~622 líneas → 129 elementos).

## Familia de 3 documentos por audiencia (no mezclar)

| Documento | PDF | Lector |
|---|---|---|
| Informe final (GENERAL) | Informe_Final_Propuesta_Instituto_Argentina.pdf (16 págs) | Dirección del instituto |
| Propuesta tabla por tabla | Propuesta_BD_y_Proceso_Instituto_Argentina.pdf | Cliente/validación del diseño |
| Informe técnico BD y flujos | Informe_Tecnico_BD_y_Flujos.pdf | Equipo de sistemas (aquí viven 112 checks, 60 tablas, etc.) |

## Edición estructural del spec JSON (receta verificada v3)

Para quitar capítulos ENTEROS sin romper el JSON, script Python (ver
/tmp/editar_informe.py de la sesión, patrón generalizable):
1. Encontrar la lista raíz de elementos por FIRMA DE CONTENIDO (la lista
   cuyos headings contienen '1. RESUMEN EJECUTIVO' y '11. CONCLUSIÓN') —
   no asumir la clave ("pages"/"elements").
2. Borrar el rango heading(cap N) → heading(cap M) INCLUYENDO el pagebreak
   que precede al primero; el pagebreak antes del cap. siguiente se queda.
3. Renumerar el heading del capítulo final ('11. CONCLUSIÓN' → '9.').
4. Replaces de texto RECURSIVOS sobre todos los dicts con 'text' (no solo
   párrafos: celdas de tabla, entradas de glosario).
5. Eliminar párrafos/entradas que quedaron con text='' (glosario SIM).
6. json.dump ensure_ascii=False indent=2, luego verificación inmediata
   contra patrones ANTES de regenerar el PDF.
Los replaces inline con sed/patch son frágiles: un replace de párrafo
puede dejar viva una celda o entrada de glosario con el mismo término.

## Falsos positivos de MONTOS al verificar (v3, nuevo)

Al verificar ausencia de montos con substring crudo:
'80 soles' matchea dentro de '7,080 soles' (licencia Jaguar — SÍ debe
quedar); '15 soles' dentro de '10 a 15 soles' (electricidad — SÍ queda);
'20 soles' dentro de '220 soles' (Opción B — SÍ queda); '112' dentro de
fechas tipo '12 de septiembre'. Patrón correcto: para cada match imprimir
la ventana ±60 chars y CLASIFICAR el hit antes de declarar fallido el
check. Los montos del despliegue y de la comparativa Jaguar son el sujeto
del cap. 8 — no son residuos.

## Recuperación de sesión cortada (patrón verificado)

"dime en qué me quedé" → session_search por el proyecto; luego comparar el
ÚLTIMO mensaje de usuario de esa sesión contra el estado real del repo
(git log + status). Si el repo está limpio en el último commit pero el
último mensaje pide cambios, el pedido quedó SIN EJECUTAR (la sesión murió
antes de actuar) — ejecutarlo de inmediato, no solo reportarlo. Así se
recuperó el pedido del SIM: enviado 2x sin respuesta, nunca aplicado,
detectado ~1h después en la sesión siguiente.

## Lecciones que se mantienen (v1/v2)

- **Jerga**: scanner RECURSIVO sobre el spec JSON ANTES de regenerar
  (dicts/listas/strings, path exacto por palabra prohibida: PHP, MariaDB,
  E2E, docker, commit...). Sustitutos: "el servidor web", "comprobaciones
  de extremo a extremo", "un solo comando". Falsos positivos: "git " dentro
  de "digital".
- **Falsos negativos pdfplumber**: 'Page 11' del pie se concatena con el
  heading siguiente → buscar el TEXTO del heading, no patrón numérico;
  buscar contra norm = re.sub(r'\s+',' ',full); página de imagen ≠ vacía
  (validar por fill geométrico).
- **Pipeline**: venv de /tmp MUERE entre sesiones — recrear
  (`uv venv /tmp/pdf_venv && uv pip install --python /tmp/pdf_venv/bin/python
  pypdf reportlab pdfplumber`); spec final SIEMPRE copiado a docs/.
  Generación: pdf_create.py spec.json -o salida.pdf; verificación: script
  /tmp con checks pdfplumber (mejor que python -c inline: evita flags del
  security scanner por "nested executable body" y timeouts de aprobación).
- **Sustento**: ningún número sin fuente medible (costos investigados
  12-13/09/2026, cotización Jaguar pública 2023). Las cifras técnicas
  (60 tablas, 446 CHECK, 112 e2e) ya no van en ESTE informe — viven en el
  informe técnico hermano.
- **Vision API caído ese día**: no fabricar verificación visual; sostenerse
  en texto + densidad. No convertir en regla ("no funciona") — es estado
  transitorio del provider.
