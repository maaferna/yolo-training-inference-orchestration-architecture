# CLAUDE.md

Guía operativa para trabajar en este repositorio.

## Qué es este repositorio

Repositorio **solo de documentación**. Documenta la arquitectura pública y anonimizada de una
plataforma interna de visión por computador: orquestación web (Django) separada de procesamiento
de ML sobre GPU (FastAPI + PyTorch/CUDA + YOLO + SAHI), con seguimiento de experimentos (ClearML)
y almacenamiento compartido de artefactos.

**No contiene** código ejecutable, datasets, pesos entrenados, métricas reales, credenciales,
nombres de clientes/instituciones, rutas absolutas reales ni ficheros de despliegue productivos.

Público objetivo: revisores de portafolio, reclutadores técnicos, ingenieros de backend/plataforma
y de ML/CV. El repositorio es una **pieza de portafolio**, no un producto.

## Regla número uno: seguridad pública (public-safe)

Toda contribución —texto, diagrama, ejemplo JSON, imagen— debe pasar la política de
`docs/architecture/17-public-release-sanitization.md` y `.github/public-safety-checklist.md`.

Nunca introducir:

- rutas absolutas reales (`/home/<usuario>/...`, `C:\Users\...`);
- nombres de clientes, instituciones, campos, fincas, proyectos o personas;
- credenciales, tokens, claves, nombres de workspace de ClearML/CVAT/Roboflow;
- IPs, hostnames o identificadores de infraestructura reales;
- métricas reales de producción, coordenadas, detecciones o resultados reales;
- capturas de pantalla, imágenes generadas, máscaras o previews reales.

Usar siempre marcadores genéricos: `PLACEHOLDER_*`, `/app/shared/`, `<PROJECT_NAME>`,
`ProjectConfiguration`, `DetectionClass`, `ClassSet`, `DatasetConfiguration`.

Los valores numéricos que aparecen en ejemplos (mAP50, tiempos, tamaños de tile) son
**ilustrativos**; deben quedar marcados como tales y nunca presentarse como resultados medidos.

## Estructura real

```text
README.md                       Portada, stack, resumen de arquitectura, índice
CONTRIBUTING.md                 Reglas de contribución y sanitización
LICENSE

docs/
  architecture/                 01..20 documentos de arquitectura (fuente de verdad técnica)
    adr/                        ADR-001..ADR-007 (registros de decisión, contenido real)
  operations/                   MLOps: roadmap, estado, migración, referencia rápida
  portfolio/                    Contenido de CV / LinkedIn / ficha de portafolio
  README.md                     Índice de la carpeta docs

diagrams/                       Fuentes Mermaid (.mmd)
assets/
  src/                          Fuentes SVG de los visuales (editables)
  diagrams/                     PNG de diagramas renderizados
  poster/                       PNG del póster renderizado
examples/
  api-payloads/                 Payloads conceptuales de request
  artifact-manifests/           Manifiestos de artefactos de ejemplo
  docker/                       Compose conceptual y .env de ejemplo
scripts/                        validate-sanitization.sh (gate public-safe),
                                build_visuals.py y render-visuals.sh (visuales)
.github/                        Revisiones, checklist de seguridad, auditorías, archive/
```

**Numeración de documentos**: los ficheros de `docs/architecture/` van de `01` a `20`, pero hay
**dos ficheros con prefijo `08`** y el índice del README está desincronizado. Antes de citar un
documento por número, verificar el nombre real en disco.

## Convenciones de documentación

- Un documento por tema, en inglés, con prefijo numérico de dos dígitos.
- Cada documento de arquitectura empieza con un `# Título` y, si aplica, un aviso public-safe.
- Diagramas embebidos en Markdown: bloques ```text con arte ASCII, o ```mermaid.
- Tablas para matrices de decisión, responsabilidades y comparativas.
- Tono: descriptivo y honesto sobre límites y riesgos. El repositorio explícitamente documenta
  lo que **no** hace (sin cola de trabajos, sin Kubernetes, ejecución síncrona).
- Enlaces internos relativos y verificados; no inventar ficheros que no existen.

## Arquitectura en una frase

`Usuario → Django (web, metadatos, visualización) → HTTP → FastAPI (frontera del servicio de IA)
→ runtime YOLO/SAHI sobre GPU CUDA → almacenamiento compartido de artefactos + ClearML → Django`

Distinción clave que el repositorio insiste en mantener: **runtime multi-GPU** (DataParallel/DDP
dentro de un entrenamiento) **≠ orquestación distribuida de trabajos** (colas, workers, Kubernetes).
Lo primero existe; lo segundo se documenta como opcional y condicionado a evidencia operativa.

## Visuales (diagramas y póster)

La fuente de verdad es `scripts/build_visuals.py`. Los SVG de `assets/src/` y los PNG de
`assets/diagrams/` y `assets/poster/` son productos derivados:

```
scripts/build_visuals.py  →  assets/src/*.svg  →  rsvg-convert  →  assets/{diagrams,poster}/*.png
```

```bash
./scripts/render-visuals.sh          # regenera todo
./scripts/render-visuals.sh 01       # solo lo que coincida con "01"
```

Requiere `python3` y `rsvg-convert` (`librsvg2-tools` en Fedora, `librsvg2-bin` en Debian).
El sistema de diseño (paleta, tipografía, retícula) está en
`.claude/skills/diagram-studio/references/design-system.md`.
**No editar los SVG ni los PNG a mano**: se regeneran y el cambio se pierde.

## Skills disponibles

| Skill | Cuándo usarla |
|---|---|
| `public-safe-audit` | Antes de publicar cambios; auditar fugas de datos y consistencia |
| `architecture-doc` | Crear o modificar documentos de `docs/architecture/` y ADRs |
| `diagram-studio` | Crear o actualizar diagramas y pósters PNG |
| `portfolio-pack` | Generar contenido de portafolio, CV, LinkedIn o ficha de proyecto |

## Al terminar cualquier cambio

1. Ejecutar `./scripts/validate-sanitization.sh`. Si sale distinto de 0, no se publica.
   Para un análisis más profundo que los barridos automáticos, usar la skill `public-safe-audit`.
2. Verificar que los enlaces internos nuevos existen.
3. Si se tocó la estructura de `docs/`, actualizar el índice del README y `docs/README.md`.
4. Si se tocó un visual, editar `scripts/build_visuals.py`, ejecutar
   `./scripts/render-visuals.sh` y versionar el SVG y el PNG resultantes.

## Auditoría vigente

`.github/REPOSITORY-AUDIT-2026-08.md` recoge 16 hallazgos, 2 ya resueltos. Los de mayor impacto
siguen abiertos: cifras sin respaldo presentadas como resultados, el índice del README
desincronizado respecto a los ficheros reales, la colisión de prefijo `08`, un diagrama Mermaid
que muestra una cola de trabajos que la arquitectura declara inexistente, y una ruta absoluta
real en `docs/operations/MLOPS_QUICK_REFERENCE.md:147`. Consultarlo antes de tocar documentación.

Los ADRs viven solo en `docs/architecture/adr/`; la carpeta `docs/adr/` fue eliminada.
