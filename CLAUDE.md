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
- capturas de pantalla, imágenes generadas, máscaras o previews reales;
- fechas absolutas (años, trimestres, mes y año, "last updated"): las decisiones se datan por
  iteración (`**Iteration**: initial` / `revision`), nunca por calendario;
- vocabulario de sucesión de sistemas ("legacy system", "the new platform", "successor",
  "second organisation"): el repositorio documenta una arquitectura de referencia y sus
  revisiones, no una migración entre organizaciones;
- nombres de cultivo, especie, plaga, lugar, país, sensor o aeronave, y umbrales reales.

La lista de tokens privados que el gate rechaza vive **fuera** del repositorio
(`~/.config/public-safe/yolo-orchestration.tokens`, una entrada por línea). El gate solo
imprime `fichero:línea`. El hook local de pre-commit ejecuta el gate con
`PUBLIC_SAFE_STRICT=1`, que bloquea si la lista falta.

Usar siempre marcadores genéricos: `PLACEHOLDER_*`, `/app/shared/`, `<PROJECT_NAME>`,
`ProjectConfiguration`, `DetectionClass`, `ClassSet`, `DatasetConfiguration`.

Los valores numéricos que aparecen en ejemplos (mAP50, tiempos, tamaños de tile) son
**ilustrativos**; deben quedar marcados como tales y nunca presentarse como resultados medidos.

## Estructura real

```text
README.md                       Portada, argumento, "start here", stack, índice de documentos
CONTRIBUTING.md                 Reglas de contribución y sanitización
LICENSE                         MIT, cubre los scripts
LICENSE-DOCS                    CC BY 4.0, cubre prosa, diagramas e imágenes generadas

docs/
  README.md                     Índice de la carpeta docs
  architecture/                 01..21 documentos de arquitectura (fuente de verdad técnica)
    adr/                        README + ADR-001..ADR-008 (registros de decisión)
  operations/                   Solo README.md: calendario operativo retirado y adónde fue
  portfolio/                    PORTFOLIO_RESUME_CONTENT.md, PORTFOLIO_IMPLEMENTATION_GUIDE.md

diagrams/                       Fuentes Mermaid: architecture-overview, training-flow,
                                inference-flow, ci-training-flow (.mmd)
assets/
  src/                          Fuentes SVG de los visuales (generadas, no editar)
  diagrams/                     PNG de diagramas renderizados
  poster/                       PNG del póster renderizado
examples/
  api-payloads/                 training, ci-training y sahi-inference (.example.json)
  artifact-manifests/           best-model-reference, training-summary,
                                inference-output-manifest (.example.json)
  docker/                       docker-compose.conceptual.md, environment.example.env
scripts/                        validate-sanitization.sh (gate public-safe) y su
                                sanitization-allowlist.txt; build_visuals.py y
                                render-visuals.sh (visuales)
.github/                        public-safety-checklist.md, REPOSITORY-AUDIT-2026-08.md,
                                ARCHITECTURE-CRITICAL-REVIEW.md,
                                PUBLIC-RELEASE-SECURITY-AUDIT.md
.claude/skills/                 architecture-doc, diagram-studio, portfolio-pack,
                                public-safe-audit
```

### Documentos de arquitectura (`docs/architecture/`)

La numeración `01`..`21` es el orden de lectura y no tiene huecos ni duplicados:

| Rango | Contenido |
|---|---|
| 01-05 | Contexto y problema, arquitectura del sistema, responsabilidades, flujo, contratos de API |
| 06-08 | Runtime Docker, almacenamiento compartido y artefactos, configuración de datasets YOLO |
| 09-13 | Motor de entrenamiento, mejora continua, inferencia SAHI, ClearML, gestión de GPU |
| 14-18 | Errores y fallbacks, limitaciones y riesgos, roadmap de evolución, sanitización pública, responsabilidades técnicas |
| 19-21 | Sincronización de resultados de inferencia, estrategia de despliegue y coste, generación de datasets sintéticos |

### ADRs (`docs/architecture/adr/`)

- ADR-001 separar web y IA · ADR-002 almacenamiento compartido · ADR-003 FastAPI como
  frontera GPU · ADR-004 ClearML (decisión, arquitectura, migración; **leer primero**) ·
  ADR-005 SAHI · ADR-006 notebooks como investigación auxiliar · ADR-007 evaluación de
  herramientas de tracking (complementa a ADR-004, no lo duplica) · ADR-008 capa de
  traducción de rutas entre contenedores.
- El validador solo detecta prefijos duplicados en `docs/architecture/`, no en `adr/`. Al
  añadir un ADR, tomar el siguiente número libre y registrarlo en `adr/README.md`.

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

## Identificadores privados

El saneamiento público sustituyó nombres internos por genéricos. Los nombres válidos son
`ProjectConfiguration`, `DetectionClass`, `ClassSet`, `DatasetConfig` y las rutas de contenedor
`/app/compute_service` y `/app/web_service`.

Nunca reintroducir los originales, ni siquiera para explicar la sustitución: publicar la
correspondencia equivale a deshacer el saneamiento. Fue exactamente el fallo C1, que expuso un
acrónimo de institución cuya publicación no está autorizada. Si un documento necesita hablar del
cambio, describe la categoría, nunca el par original-reemplazo.

## Auditoría vigente

`.github/REPOSITORY-AUDIT-2026-08.md` recoge los hallazgos de la auditoría de agosto de 2026
(críticos C1-C2, altos H1-H7, medios M1-M11, bajos L1-L7). A fecha de septiembre de 2026 están
todos cerrados: archivo eliminado e historia reescrita, gate `validate-sanitization.sh`
operativo, cifras sin respaldo retiradas, índice del README y `docs/README.md` regenerados desde
disco, documentos renumerados `01`..`21`, diagrama de cola corregido, YOLOv8/v11 unificado,
credenciales de ejemplo leídas del entorno, licencia dual, ADR de traducción de rutas
renumerado a ADR-008 (M11). El único punto abierto es la exposición residual de C2, fuera del
control del repositorio: los objetos antiguos siguen accesibles por SHA hasta que GitHub los
recolecte.

`./scripts/validate-sanitization.sh` pasa en limpio (todas las comprobaciones bloqueantes y
advisory). Consultar el informe antes de tocar documentación.

Los ADRs viven solo en `docs/architecture/adr/`; la carpeta `docs/adr/` fue eliminada.
