---
name: diagram-studio
description: Crea, actualiza y renderiza los diagramas y pósters PNG de este repositorio para uso en portafolio. Usar cuando se pida un diagrama, un póster, un esquema visual, actualizar un gráfico existente, exportar a PNG, o preparar material visual para portafolio, LinkedIn o presentaciones. Cubre el pipeline SVG a PNG, el sistema de diseño compartido y la regla de fidelidad respecto a la documentación.
---

# Estudio de diagramas

## Pipeline

Los visuales se generan con código, no a mano:

```
scripts/build_visuals.py   →   assets/src/*.svg   →   rsvg-convert   →   assets/diagrams/*.png
                                                                          assets/poster/*.png
```

Un solo comando reconstruye todo:

```bash
./scripts/render-visuals.sh            # todo
./scripts/render-visuals.sh poster     # solo lo que coincida con "poster"
```

Requisitos: `python3` y `rsvg-convert` (paquete `librsvg2-tools` en Fedora,
`librsvg2-bin` en Debian/Ubuntu).

**Nunca editar los `.svg` ni los `.png` directamente.** Se regeneran y el cambio se perdería.
Toda modificación se hace en `scripts/build_visuals.py`.

## Cómo añadir un diagrama

1. Leer el documento de `docs/architecture/` que describe el tema. El diagrama debe ser fiel al
   documento; si discrepan, el documento manda o se corrige antes de dibujar.
2. Abrir `scripts/build_visuals.py` y añadir una función `def diagram_<slug>() -> str:` que
   devuelva el SVG completo, usando los helpers del módulo (`Canvas`, `box`, `arrow`, `chip`,
   `legend`, `footer`).
3. Registrarla en la lista `DIAGRAMS` al final del fichero, con su nombre de salida.
4. Ejecutar `./scripts/render-visuals.sh <slug>` y revisar el PNG.
5. Enlazarlo desde el README o el documento correspondiente.

## Sistema de diseño

Cargar `references/design-system.md` antes de dibujar. Resumen operativo:

- Fondo oscuro `#0A101C`, cajas `#141E31`, borde `#2A3B58`.
- El color codifica **capa**, nunca decoración: web `#4FA8FF`, servicio de IA `#FFB13D`,
  GPU `#7ED957`, tracking `#B98BFF`, almacenamiento `#FF7E8E`, datos `#35D6D0`, riesgo `#FF6B6B`.
- Montserrat para títulos, Lato para cuerpo, Liberation Mono para rutas y código.
- Flechas ortogonales de 2 px con marcador del color de la capa de destino.
- Una pregunta por diagrama. Máximo cuatro líneas de detalle por caja.

## Fidelidad al contenido

El repositorio es documentación public-safe; los diagramas heredan esa política completa.

- Sin rutas absolutas reales, credenciales, nombres de clientes ni hostnames.
- Sin métricas presentadas como reales. Si un diagrama muestra un valor (`mAP50 0.87`,
  `~20 tiles`, `640 px`), etiquetarlo como ilustrativo en el pie del lienzo.
- **No dibujar capacidades que la arquitectura declara ausentes.** El sistema no tiene cola de
  trabajos, ni worker pool, ni Kubernetes. Si un diagrama muestra una cola, debe ir en una banda
  rotulada como fase futura y con estilo discontinuo, no en el flujo actual.
- Mantener la distinción entre runtime multi-GPU y orquestación distribuida de trabajos.
- Todo lienzo lleva pie con `Public-safe · illustrative values`.

## Diagramas actuales

| Fichero | Pregunta que responde |
|---|---|
| `01-system-architecture` | ¿Cómo se separan las capas y qué habla con qué? |
| `02-training-flow` | ¿Qué ocurre entre la petición de entrenamiento y el modelo seleccionado? |
| `03-ci-training-flow` | ¿Cómo se decide si el modelo nuevo reemplaza al anterior? |
| `04-sahi-inference` | ¿Por qué el teselado mejora la detección de objetos pequeños? |
| `05-deployment-strategy` | Local, AWS o híbrido: ¿qué conviene y por qué? |
| `06-synthetic-dataset` | ¿Cómo se genera un dataset sintético a partir de datos reales escasos? |
| `07-evolution-roadmap` | ¿Qué se añade primero y qué disparador lo justifica? |
| `poster-architecture` | Póster de una página que resume el sistema completo |

## Origen Mermaid

`diagrams/*.mmd` contiene las fuentes Mermaid originales. Se conservan como referencia legible en
texto y para renderizado en GitHub, pero **no** son la fuente de los PNG. Al cambiar un flujo,
actualizar ambos y comprobar que no se contradicen.
