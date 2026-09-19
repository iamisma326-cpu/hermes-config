# belleza1 — app POLLERÍA (pedido de pollo)

App Android de curso: Kotlin + Jetpack Compose (Material3), Gradle wrapper 9.5,
ruta `~/projects/Desktop/belleza1`, package `com.example.appservicios`.
Compile check: `bash gradlew :app:compileDebugKotlin --console=plain`
(wrapper sin +x → invocar con bash).

## Qué es

Formulario de pedido de una pollería: `MainActivity` llama al composable
`servicios()` (en `app/src/main/java/com/example/appservicios/MainActivity.kt`),
una Column amarilla con:

- Título "POLLERIA" (20sp, centrado)
- CLIENTE, DNI: TextField (estados `cliente`, `dni`)
- PRODUCTO: Button "[Seleccione producto]" — `onClick` aún VACÍO
- CANTIDAD: TextField (estado `cantidad`)
- IMPORTE / DESCUENTO / TOTAL A PAGAR: etiquetas + TextField (estados
  `importe`, `descuento`, `total`) — añadidos a pedido del usuario con el
  mismo patrón `var x by remember { mutableStateOf(value="") }`

Todo el archivo está comentado línea por línea en español (nivel principiante,
cada concepto explicado UNA vez, sin `;` en comentarios, imports sin comentar).

## Estado de la sesión (2026-09-09)

Hecho y verificado compilando:
- Label "DNI"→"Cantidad" en el TextField de cantidad (copy-paste bug)
- "producto"→"PRODUCTO" (consistencia de mayúsculas)
- Estados + TextField de importe, descuento y total
- Comentarios línea por línea, deduplicados, `;`→`,`
- Última verificación: BUILD SUCCESSFUL en 7s

## Pendientes acordados (usuario los conoce, aún NO implementar sin señal)

1. Envolver `servicios()` en `AppServiciosTheme { }` dentro de setContent
   (el import ya existe).
2. `.verticalScroll(rememberScrollState())` en la Column — el contenido no
   cabe en pantalla con 6 TextField.
3. Botón PRODUCTO: acordado DropdownMenu (opción 1 de las 3 explicadas —
   no AlertDialog ni ExposedDropdownMenuBox). Estados previstos:
   `var producto by remember { mutableStateOf(value="") }` +
   `var menuAbierto by remember { mutableStateOf(value=false) }`,
   con `DropdownMenuItem` por producto y lista de precios tipo
   `listOf("Pollo entero" to 45.0, ...)` para alimentar el cálculo.
4. Cálculos: importe = cantidad × precio(producto), total = importe −
   descuento (el usuario quiere los campos iguales a los demás por ahora).
5. Cosmético: indentación irregular (bloque setContent y desde CANTIDAD),
   imports sin usar (`size`, `Scaffold`, `Preview`), espacio raro en
   `Modifier .fillMaxWidth()`, nombre composable en minúscula (convención:
   PascalCase `Servicios`).
6. Futuro: teclado numérico/validación para DNI y CANTIDAD.

## Preferencias del usuario en este proyecto

- "no hagas nada todavía, solo dime cómo sería" — modo explicar-antes-de-código.
- "sin hacer nada extra" — auditorías read-only, hallazgos numerados con
  path:line, él elige qué se corrige.
- Comentarios: cada concepto 1 vez (denunció redundancia), `,` no `;`,
  español principiante, conservar su indentación y comentarios propios.
