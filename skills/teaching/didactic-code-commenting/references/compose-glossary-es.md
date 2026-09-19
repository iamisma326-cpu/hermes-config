# Glosario Compose/Kotlin en español (frases aprobadas por el usuario)

Frases ya validadas en sesión para comentar código Jetpack Compose de sus
trabajos de curso. Reutilizar textualmente para mantener su voz.

## Patrón de estado
- `var X by remember { mutableStateOf(value="") }`:
  - `var` = variable mutable (val no permitiría cambiarla). `by` = delega la lectura/escritura al objeto que devuelve remember.
  - `remember` = conserva el valor mientras VIVA LA PANTALLA (sin él se reiniciaría a "" en cada recomposición).
  - `mutableStateOf` = vuelve el valor OBSERVABLE: al cambiar, Compose redibuja automáticamente todo lo que lo muestra.
- Repeticiones: solo `// DNI del cliente`, `// cantidad pedida`, etc.

## Estructura
- `class MainActivity : ComponentActivity()` = la PANTALLA PRINCIPAL de la app, hereda de ComponentActivity (":" se lee "es un/extends").
- `onCreate`: se ejecuta UNA sola vez al crear la pantalla (punto de entrada). `override` = reemplaza el de la clase padre. `Bundle?` = puede ser null.
- `super.onCreate`: deja que la clase padre termine su configuración interna primero.
- `enableEdgeToEdge()`: dibujar también detrás de las barras del sistema.
- `setContent`: define QUÉ se muestra en pantalla (reemplaza al viejo layout XML).
- `@Composable`: anotación OBLIGATORIA en funciones que dibujan UI, Compose las re-ejecuta cuando cambia un estado (recomposición).
- `fun`: declara la función, no recibe parámetros.

## UI
- `Column`: contenedor que apila sus hijos en VERTICAL, uno debajo de otro.
- `modifier = Modifier`: encadena ajustes visuales, cada ".algo()" agrega uno.
- `.fillMaxSize()`: ocupa el 100% del ancho Y del alto disponibles (toda la pantalla).
- `.fillMaxWidth()`: ocupa todo el ancho disponible.
- `.background(Color.Yellow)`: pinta el fondo.
- `.padding(20.dp, 40.dp)`: margen interno, 20 a los lados, 40 arriba/abajo (dp = pixel independiente de densidad).
- `.padding(top = 10.dp)`: margen solo ARRIBA (separa de lo anterior).
- `Text`: muestra texto NO editable (como un Label). `text` = contenido a mostrar.
- `fontSize = 20.sp`: tamaño de letra (sp = unidad de texto que respeta el tamaño de fuente del usuario).
- `fontWeight = FontWeight.Bold`: letra en NEGRITA.
- `textAlign = TextAlign.Center`: alinea el texto al centro de su espacio.
- `TextField`: caja donde el usuario ESCRIBE. `value` = texto actual (viene del estado), `onValueChange` = se ejecuta con cada tecla presionada/borrada, `it` = el texto NUEVO completo que quedó en la caja, que guardamos en el estado para que se redibuje.
- `label = { Text("...") }`: pista dentro de la caja (va en { } porque dibuja UI). Alternativas: sin label (el Text de arriba basta), `placeholder` (desaparece al escribir), `supportingText` (fijo debajo), `prefix`/`suffix` (fijo dentro, no editable).
- `Button`: botón táctil, entre sus { } va lo que muestra. `onClick` = acción al presionarlo. `shape = RoundedCornerShape(0.dp)` = esquinas rectas.

## Cierres
- `} // cierra la Column`, `} // cierra la función servicios()`, etc.

## Imports (regla: un solo comentario colectivo + los del patrón de estado)
- `import androidx.compose.runtime.Composable` // para la anotación @Composable
- `import androidx.compose.runtime.getValue` // obligatorio para LEER una var con "by"
- `import androidx.compose.runtime.setValue` // obligatorio para ESCRIBIR una var con "by"
- `import androidx.compose.runtime.mutableStateOf` // crea el estado observable
- `import androidx.compose.runtime.remember` // conserva el valor mientras viva la pantalla
