# Trámites virtuales + validación de vouchers DRELM (investigación verificada 2026-09-12)

Contexto: automatizar la validación de vouchers de tesorería del IESTP
Argentina. Hoy: alumno canjea voucher FÍSICO en tesorería; ellos validan en
el sistema de la DRELM. Objetivo del usuario: trámite virtual → notificación
WhatsApp al tesorero (datos del alumno según tipo de trámite) → validación
rápida → documento al alumno (Gmail/WhatsApp) → alumno continúa en Secretaría.

PREFERENCIA DEL USUARIO (primera clase): para decisiones de diseño que
dependen del contexto (Perú, sector público, DRELM), investigar en internet
EN TIEMPO REAL con fuentes citadas — NUNCA responder de memoria ("no quiero
datos incorrectos o desactualizados").

## El hallazgo que cambia el diseño

- **La DRELM ya tiene el "Sistema de Recaudación 2.0"** (recaudacion.drelm.gob.pe,
  módulo alumno /auth2/alumno) con canje 100% digital de vouchers. Otros IESTP
  de Lima ya lo usan: María Rosario Aráoz Pinto (nov-2025, acceso DNI/DNI).
  Manual oficial de 14 págs descargado de su link en gob.pe (si /tmp murió,
  regenerar desde la nota de prensa del IESTP MRAZP en gob.pe).
- **El propio IESTP Argentina YA autorizó canje virtual** (comunicado de
  Tesorería en su Facebook oficial, sep-2025).
- CONSECUENCIA: gestionest1 NO reemplaza el sistema DRELM — lo ORQUESTA. El
  cuello de botella ya no es "subir el voucher" (existe) sino que el tesorero
  se entera tarde, abre el sistema a mano y cruza datos.

## Cómo funciona el sistema DRELM (del manual oficial, leído completo)

1. Alumno entra con usuario/contraseña = DNI/DNI (alta la hace el responsable
   en el instituto; reset por tesorería deja DNI por defecto).
2. Registra un correo PERSONAL (cualquier Gmail/Hotmail) con código de
   verificación de 10 min → **RESUELVE el problema de ingresantes sin correo
   institucional**. El manual también pide "número de celular actual" al
   cargar el voucher.
3. Carga voucher con todos los datos → estado **Pendiente**.
4. Cajero/tesorero coteja → **Procesado** (emite recibo, visible en
   "Detalle de pagos") o **Rechazado** (con observación visible; el alumno
   puede eliminar y re-registrar). Cargar voucher ≠ registro: el cajero
   puede rechazar.

## Reglas duras del instituto (web oficial istpargentina.edu.pe)

- Pagos SOLO en Banco de la Nación: agencia 0000-288934 (ISTP "ARGENTINA"),
  Agente Multired 00000-288934 (DRELM). "No se aceptan transferencias".
- El voucher físico del BN sigue existiendo → el trámite virtual pide
  FOTO/PDF del voucher y mantiene "voucher físico presentado" como respaldo.
- Admisión: S/130 (examen marzo 2026); sin mensualidad; título a nombre de
  la Nación. IESTP público bajo jurisdicción DRELM (25 IESTP en Lima Metrop.).

## WhatsApp Cloud API — números verificados (sep-2026)

- Cobro POR MENSAJE ENTREGADO desde jul-2025 (murió el cobro por conversación).
- Perú: utility ≈ $0.020/msg, marketing ≈ $0.0773, authentication ≈ $0.022;
  service (respuestas dentro de ventana 24h) gratis — PERO Meta cobra
  service desde 1-oct-2026 (~$0.03; 1.000 gratis/mes/número). Volumen:
  ~300 trámites × 2 msgs ≈ $12/semestre → costo irrelevante.
- Fuera de la ventana 24h se requiere plantilla (template) aprobada por
  Meta; notificación de trámite = categoría UTILITY (utility con lenguaje
  promocional es rechazada; aprobación típica 5-15 min).
- **Reacciones emoji SÍ llegan por webhook** (`type:"reaction"`, con
  `reaction.message_id` + `emoji`), límite 30 días desde el mensaje original.
- NO automatizar WhatsApp Web no-oficial en un instituto público: ban del
  número = tesorería pierde el canal en plena matrícula. Cloud API requiere
  Meta Business Verification del instituto (burocrático pero otros
  organismos peruanos ya lo hacen).

## Decisiones de diseño ACORDADAS (con el usuario, validar antes de construir)

1. NO enviar el PDF del voucher por WhatsApp (crearía dos fuentes de verdad
   vs DRELM): enviar RESUMEN estructurado (DNI, nombre, semestre, tipo de
   trámite, monto, concepto, N° operación, hora) + LINK con token de un solo
   uso a la ficha del trámite. El PDF vive en la BD, no en el chat.
2. Emoji = shortcut, NO registro: la reacción dispara/abre panel de
   confirmación de un clic ("Validar y emitir recibo"); el CLIC es el acto
   auditado (bitácora). El emoji no identifica quién reaccionó (teléfono
   compartido) ni sirve a auditoría.
3. Validación AUTOMÁTICA previa (OCR del voucher: monto/fecha/N°
   operación/concepto) contra TUPA ANTES de notificar al tesorero: los
   rechazos tempranos van directo al alumno con motivo; el tesorero solo ve
   trámites pre-validados.
4. Privacidad (Ley 29733): mínimo de datos personales por WhatsApp; los
   documentos completos solo con login en el sistema.
5. El recibo oficial LO EMITE el tesorero en el sistema DRELM — gestionest1
   NUNCA emite recibos con valor oficial por su cuenta.
6. Estados del trámite en gestionest1 = mismos nombres que DRELM
   (Pendiente/Procesado/Rechazado) para lenguaje uniforme.
7. Ingresantes: credencial = DNI + celular + correo personal verificado
   (patrón DRELM). `usuarios` en "pre-registro" ANTES del correo
   institucional (personas ya tiene telefono/correo; faltan columnas
   *_verificado + estado pre-registro).

## API DRELM = no-camino a corto plazo

No existe API pública del Sistema de Recaudación 2.0. El camino formal es
interoperabilidad vía PIDE (Ley de Gobierno Digital DL 1412 + reglamento
DS 029-2021-PCM; Mesa Digital Perú, casilla única electrónica). Plazo
realista meses/años → DOCUMENTAR como roadmap institucional, no implementar.

## Plan de fases (acordado; Fase 1 = siguiente trabajo del sistema)

- **Fase 0** (1 sem, cero código): hablar con tesorería del Argentina — ¿ya
  usan Recaudación 2.0? ¿cómo llegan hoy los vouchers virtuales? ¿qué les
  demora? 30 min valida media arquitectura.
- **Fase 1** MVP (2-3 sem): "Mis trámites" del alumno (iniciar trámite,
  subir voucher + requisitos por tipo; BD ya tiene tramites/tipos_tramite/
  tramite_requisitos/requisitos_tipos_tramite) + panel tesorería (cola con
  filtros, ficha completa, Validar/Rechazar con observación) + notificación
  interna (tabla notificaciones ya existe) + correo al alumno.
- **Fase 2** (1-2 sem): WhatsApp Cloud API al tesorero (plantilla utility +
  link con token) + webhook de reacciones → confirmación → acción real.
- **Fase 3** (opcional): OCR del voucher (Tesseract o IA de visión).
- **Fase 4**: roadmap institucional (oficio DRELM/PIDE) — solo documento.

## Fuentes (verificadas 2026-09-12, regenerables)

- gob.pe → IESTP María Rosario Aráoz Pinto: "Trámites Académicos Renovados:
  Accede y Canjea tu Voucher Digitalmente" (link al sistema DRELM + manual
  en Drive: "Manual de Usuario Recaudación - Estudiantes 2025", 14 págs).
- Facebook oficial instituto.argentina: "Comunicado de TESORERÍA. Para
  canjear Voucher de forma virtual" (sep-2025).
- istpargentina.edu.pe /matricula y /admision: cuenta BN, no transferencias,
  S/130, cronograma.
- developers.facebook.com: pricing per-message (jul-2025) + webhooks
  (payload de reactions, límite 30 días).
- plivo.com/whatsapp/pricing/pe: tarifas Perú 2026.
- gob.pe: Reglamento Ley Gobierno Digital (DS 029-2021-PCM) — PIDE,
  Mesa Digital Perú, interoperabilidad.
- Casos hermano para no reinventar: IESTP Manuel Arévalo Cáceres (Google
  Forms tesorería + canje presencial), IESTP Naranjillo (voucher por
  correo), IESTP Pedro Pediano (recibo PDF en intranet + validación
  presencial), IESTP Daniel Villar (foto voucher en formulario de matrícula
  con advertencia de proceso administrativo por falsedad).
