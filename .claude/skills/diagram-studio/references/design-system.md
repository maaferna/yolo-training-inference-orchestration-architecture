# Sistema de diseño visual

Un único sistema para diagramas y pósters, de modo que el conjunto se lea como una sola pieza
de portafolio. Fondo oscuro en todo: contrasta bien tanto en GitHub claro como oscuro, y funciona
igual en pantalla y en presentación.

## Paleta

Superficies y texto:

| Token | Hex | Uso |
|---|---|---|
| `canvas` | `#0A101C` | Fondo del lienzo |
| `band` | `#0E1524` | Bandas de sección y encabezados |
| `panel` | `#141E31` | Relleno de caja estándar |
| `panel2` | `#1B2942` | Caja destacada o anidada |
| `stroke` | `#2A3B58` | Borde de caja |
| `strokeSoft` | `#1F2E47` | Separadores y retícula |
| `text` | `#EAF0FA` | Texto principal |
| `textDim` | `#94A6C4` | Texto secundario |
| `textFaint` | `#63799B` | Etiquetas, notas al pie |

Acentos, uno por capa arquitectónica. El color codifica **capa**, nunca decoración:

| Token | Hex | Capa |
|---|---|---|
| `web` | `#4FA8FF` | Django / capa web y usuarios |
| `api` | `#FFB13D` | FastAPI / frontera del servicio de IA |
| `gpu` | `#7ED957` | Runtime GPU: PyTorch, CUDA, YOLO, entrenamiento |
| `track` | `#B98BFF` | ClearML / seguimiento de experimentos |
| `store` | `#FF7E8E` | Almacenamiento compartido, artefactos, base de datos |
| `data` | `#35D6D0` | Datos: datasets, imágenes, pipeline sintético |
| `warn` | `#FF6B6B` | Riesgos, condiciones de fallo, cuellos de botella |

Regla: una caja usa su acento en el borde y en una barra superior de 4 px; el relleno se mantiene
en `panel`. Rellenos saturados solo para el chip de una etiqueta, nunca para un bloque grande.

## Tipografía

| Rol | Familia | Peso | Tamaño (unidades de lienzo) |
|---|---|---|---|
| Título de póster | Montserrat | 800 | 64–86 |
| Título de diagrama | Montserrat | 700 | 34–40 |
| Título de sección | Montserrat | 600 | 20–24 |
| Título de caja | Montserrat | 600 | 16–19 |
| Cuerpo | Lato | 400 | 13–15 |
| Etiqueta / chip | Lato | 700 | 11–12, `letter-spacing: 0.08em`, mayúsculas |
| Código / rutas | Liberation Mono | 400 | 12–13 |

Declarar siempre con respaldo: `Montserrat, 'DejaVu Sans', sans-serif`.

## Retícula y forma

- Base de 8 px. Márgenes exteriores del lienzo: 56 px en diagramas, 88 px en pósters.
- Radio de esquina: 10 px en cajas, 14 px en contenedores, 999 px en chips.
- Grosor de borde: 1.5 px en cajas, 1 px en separadores.
- Separación mínima entre cajas: 24 px; entre bandas de sección: 40 px.

## Flechas

- Trazo de 2 px, con `marker-end` triangular del mismo color.
- Flujo principal: color de la capa de destino, opacidad 1.
- Flujo secundario o de retorno: `strokeSoft`, `stroke-dasharray="6 5"`.
- Etiquetas de flecha: Lato 700 a 11 px, en `textDim`, sobre un rectángulo de fondo `canvas`
  para que el trazo no atraviese el texto.
- Preferir recorridos ortogonales (codos) sobre diagonales, salvo en diagramas radiales.

## Composición

- Un diagrama responde **una** pregunta. Si necesita dos títulos, son dos diagramas.
- Flujo de arriba abajo para capas; de izquierda a derecha para secuencias temporales.
- Toda caja lleva título y, como máximo, cuatro líneas de detalle. Lo que no cabe va al documento.
- Leyenda abajo a la izquierda, siempre que haya más de tres acentos en uso.
- Pie de lienzo: nombre del repositorio a la izquierda, aviso `Public-safe · illustrative` a la
  derecha, en `textFaint` a 11 px. Obligatorio: recuerda al lector que las cifras no son reales.

## Formatos de salida

| Pieza | Lienzo SVG | PNG renderizado |
|---|---|---|
| Diagrama estándar | 1600 × 1000 | 3200 × 2000 |
| Diagrama alto | 1600 × 1300 | 3200 × 2600 |
| Póster | 1240 × 1754 (proporción A2) | 2480 × 3508 |

El póster a 2480 × 3508 imprime a A2 con 150 dpi o a A3 con 212 dpi.
