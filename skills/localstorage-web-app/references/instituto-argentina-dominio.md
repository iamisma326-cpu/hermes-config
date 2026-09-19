# Instituto Argentina — dominio para el simulador modulo04 (extraído 2026-09-15)

Fuentes vivas: `/home/isma/projects/gestionest1/` → `api/sql/01_schema.sql`, `api/handlers/*Handler.php`,
`api/sql/03_seed.sql`, y los PDFs oficiales `TUPA-2026.pdf`, `RI.pdf`, `PEI`, `POLITICAS-DE-CALIDAD`.
El simulador (HTML/CSS/JS + localStorage) replica SOLO el proceso matrícula + trámites con 3 roles:
Alumno, Secretaría Académica, Tesorería.

## Entidades y estados (schema real → sim)
- `personas` (raíz 3NF) → `usuarios` (rol: Administrador|Secretaría|Tesorería|Estudiante|Docente|Soporte|Practicante; 'Egresado' NO es rol) → `estudiantes` (fotoEstado: Sin foto|Pendiente|Aprobada|Rechazada, reintentos ≤3).
- Catálogos: `carreras` (DSI/GA admiten ingreso según PEI; CEI/ADM historial con carrera_predecesora), `turnos` (M Diurno 08:10-14:10, N Nocturno 16:30-22:30), `ciclos` C1-C6, `semestres` (2026-I activo), `feriados` (10 feriados 2026 para días hábiles), `conceptos_pago` (CP01.., CT* TUPA con monto), `tipos_matricula` (TM1..TM6, TM6=Reserva), `tipos_tramite` (TA01-TA55 + TT02, con codigoTupa/categoria/plazoDias/calificacion/autoridad/aplicaA), `requisitos_tipos_tramite`.
- `vacantes` (2026-I-{carrera}-{turno}, total/ocupadas) — la matrícula `En trámite` NO consume vacante; la consume la CONFORMIDAD final.
- `matriculas`: estado `En trámite|Matriculado|Reservada|Anulada`; condicion `Ingresante|Promovido|Promovido con curso a cargo|Repitente|Reingresante|Traslado`; unicidad "máx 1 no-anulada por estudiante+semestre" (columna generada estado_vigente).
- `pagos`: voucher_estado `Sin voucher|Pendiente|Aprobado|Rechazado` (con motivo_rechazo, validadoCod, fechaValidacion, intentos).
- `tramites`: estado `Pendiente|En proceso|Aprobado|Rechazado|Listo para recojo`; campo `datos` JSON por tipo (turnoActual/turnoDeseado, carrera, ciclo, tipoEmision...); ficha TUPA embebida (precio/codigoTupa/plazoDias/autoridad/fechaLimite/vencido/diasRestantes).
- `tramite_requisitos` (entregado/validado/observacion/nombreArchivo), `carnes` (tipoEmision Nueva|Renovación; estado Emitido|Entregado; 1 por trámite uq_carnes_tramite), `expedientes`/`expedientes_detalle` (fuera de alcance, solo mención), `avisos`+`avisos_destinatarios` (fan-out, leída individual), `whatsapp_*` (4 tablas; en el sim solo panel visual con nota "Simulación").

## Reglas de negocio con fuente (RI = Reglamento Institucional, TUPA = código de procedimiento)
- Art. 24: ingresante debe matricularse o reservar en 20 días hábiles; si no → liberar vacante en orden de mérito (handler: `GET /matriculas/por-liberar` + `POST /liberar`; solo Secretaría/Admin).
- Art. 26: tope 24 créditos/periodo (incl. repitencia); matrícula hasta 30 días calendario tras iniciar el semestre.
- Art. 27: repetir un semestre máx 2 veces.
- Art. 28: traslados solo con vacante; cambio de turno vía FUT por mesa de partes.
- Art. 36-38: reserva/licencia por FUT con pago y sustento; reservas+licencias NO exceden 4 ciclos consecutivos (reserva = POST /matriculas/{cod}/reservar, fija TM6; el PUT genérico lo salta → SIEMPRE ir por la ruta real).
- Art. 40-42: quien no reserva pierde derechos; abandono = 20 días hábiles sin asistir sin licencia.
- Art. 83: nota mínima 13 para certificación modular. Art. 84: certificados modulares ≤30 días hábiles.
- Flujo matrícula real: iniciar trámite (no consume vacante) → alumno sube voucher+foto → Tesorería valida voucher / Secretaría valida foto (rechazo exige motivo) → conformidad (voucherOk+fotoOk, fechaConformidad, conformidadCod) → Matriculado + vacante++.
- Transiciones trámite reales: Pendiente→[En proceso|Aprobado|Rechazado]; En proceso→[Aprobado|Rechazado]; Aprobado genera efectos según tipo (carné emitido para Carné de Medio Pasaje, cambio de turno aplicado a matrícula); Listo para recojo tras emisión.

## TUPA 2026 — importes y plazos clave (Anexo 01)
Matrícula ingresante S/200 · Traslado interno S/200 · Traslado interno (cambio de turno) S/120 · Traslado externo S/250 · Ratificación S/200 · Fraccionamiento S/100 · Reserva (4.8) S/30 · Convalidación S/100 · Repitencia S/50-70 · Reingreso S/50 · Reporte record S/60 · Constancia de ingreso S/20 · Constancia de estudios S/60 · Constancia 1ª matrícula S/30 · Constancia de egresado (11.5/11.6) S/60 · Constancia de título en trámite S/60 · Constancia de tercio superior S/30 · Carta de presentación S/15 · Certificado de estudios 1ª vez GRATUITO (paga formato S/15) · Certificado 2ª+ S/180 · Certificado 1 semestre S/30 · Carpeta de prácticas S/30 · Constancia de prácticas S/30 · Certificado por módulo S/50 · por 3 módulos S/120 · Carpeta titulación (propios S/50 / otros S/70) · Examen suficiencia inglés S/100 · Titulación (propios S/150 / otros S/250) · Expedición título (S/250 / S/300) · Duplicado de título S/250 · Diploma de egresado S/50 · Silabus (S/50 / S/60) · Boleta de notas duplicado S/15 · Rectificación de nombre S/30 · GRATUITOS: duplicado de recibo de caja, fedateo, copia simple 1 hoja. Calificación: Aprobación Automática (admisión/reserva/carpetas) o Previa evaluación/verificación (Secretaría Académica / Tesorería / Dirección / Comisión Central).

## Cuentas demo (replicar en seed)
admin/admin123 · secretaria/sec123 · tesoreria/tes123 · 74296138/74296138 (Estudiante, Carlos Ismael Espinoza — usuario y clave = DNI). Otras: docente/doc123, soporte/soporte123, 71112233/71112233 (Practicante), 71893456/71893456 (Estudiante egresada, entra por tarjeta Estudiante).

## Convenciones de rol del usuario (aplican al simulador)
- Login con pantalla de selección de rol ANTES del formulario (tarjetas con branding; la cuenta debe coincidir con el rol elegido).
- Un apartado por ROL; nunca una vista compartida con permisos distintos sin separarla.
- Reglas de negocio SIEMPRE en `negocio/`, nunca en vistas/store — para que la futura migración a PHP+MySQL sea mecánica (los handlers reales son el destino).
- Claves en texto plano = aceptable en simulación, documentado; no replicar en producción.