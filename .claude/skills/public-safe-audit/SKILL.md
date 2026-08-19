---
name: public-safe-audit
description: Audita este repositorio de documentación contra su política public-safe y su consistencia interna. Detecta rutas absolutas reales, credenciales, nombres de clientes o instituciones, métricas presentadas como reales, enlaces rotos, ficheros vacíos, duplicados y desincronización entre el índice del README y los ficheros en disco. Usar antes de publicar o commitear cambios, cuando se pida "auditar", "revisar el contenido", "verificar que es seguro publicar", o al añadir documentos, ejemplos o imágenes nuevas.
---

# Auditoría public-safe

Este repositorio es material de portafolio público. Una fuga de datos o una inconsistencia visible
daña directamente la credibilidad profesional que el repositorio intenta demostrar. La auditoría
tiene dos mitades igual de importantes: **fugas** (¿es seguro publicarlo?) y **consistencia**
(¿resiste una lectura crítica?).

## Alcance

Por defecto audita todo salvo `.git/`. Incluir siempre `.github/archive/`: está versionado y es
público, aunque su nombre sugiera lo contrario. Si el usuario pide auditar solo lo modificado,
usar `git diff --name-only` como lista de entrada.

## Parte 1 — Fugas

Ejecutar cada barrido y clasificar cada hallazgo como **fuga real**, **ejemplo ilustrativo** o
**mención de la propia política** (los documentos de sanitización citan patrones prohibidos como
ejemplos; eso es correcto, no un hallazgo).

```bash
# Rutas absolutas reales
grep -rnE '/home/[a-z][a-z0-9_-]+|/Users/[A-Za-z]|C:\\Users' --include='*.md' --include='*.json' --include='*.env' --include='*.svg' . | grep -v '^./.git/'

# Credenciales y tokens con valor aparente
grep -rniE '(api[_-]?key|secret|password|token|access[_-]?key)\s*[:=]\s*["\x27]?[A-Za-z0-9_/+-]{8,}' --include='*.md' --include='*.json' --include='*.env' . | grep -v '^./.git/'

# IPs y hostnames concretos
grep -rnE '\b(([0-9]{1,3}\.){3}[0-9]{1,3})\b' --include='*.md' --include='*.json' --include='*.env' . | grep -v '^./.git/' | grep -vE '0\.0\.0\.0|127\.0\.0\.1'

# Correos
grep -rnE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' --include='*.md' --include='*.json' . | grep -v '^./.git/' | grep -v 'example\.com'

# Binarios e imágenes: no debe existir ninguna captura o salida real de modelo
find . -path ./.git -prune -o -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.pt' -o -iname '*.pth' -o -iname '*.onnx' \) -print
```

Para las imágenes: los PNG generados desde `assets/src/*.svg` son **diagramas sintéticos** y son
aceptables. Cualquier otra imagen (captura de pantalla, preview de inferencia, máscara, foto de
dron) es una fuga y debe eliminarse.

Marcadores aceptados como seguros: `PLACEHOLDER_*`, `<...>`, `[..._PLACEHOLDER]`, `example.com`,
`0.0.0.0`, `127.0.0.1`, `/app/...`, `/data/shared/`, `/host/shared_artifacts`.

### Nombres propios

Buscar nombres de organizaciones, personas, fincas, campos o proyectos. No hay regex fiable para
esto: leer los documentos modificados. Los únicos nombres propios legítimos son tecnologías
(Django, FastAPI, PyTorch, CUDA, YOLO, SAHI, SAM, ClearML, CVAT, Roboflow, Docker, Ubuntu, AWS)
y los identificadores públicos del propio autor.

## Parte 2 — Consistencia

```bash
# Ficheros vacíos versionados
find . -path ./.git -prune -o -type f -empty -print

# Enlaces internos rotos
grep -rnoE '\]\(\.?[./][^)]*\.md[^)]*\)' --include='*.md' . | grep -v '^./.git/' | \
  sed 's/](/\t/' | tr -d ')' | while IFS=$'\t' read -r src link; do
    f="${src%%:*}"; rest="${src#*:}"; ln="${rest%%:*}"; t="${link%%#*}"
    [ -z "$t" ] && continue
    case "$t" in /*) p=".$t";; *) p="$(dirname "$f")/$t";; esac
    [ -e "$p" ] || echo "ROTO $f:$ln -> $link"
  done | sort -u

# Prefijos numéricos duplicados en docs/architecture
ls docs/architecture/*.md | sed 's#.*/##' | cut -c1-2 | sort | uniq -d

# Índice del README frente a la realidad
ls docs/architecture/*.md | sed 's#.*/##' | sort > /tmp/real.txt
grep -oE '^\| \`[0-9]{2}-[a-z0-9-]+\.md\`' README.md | tr -d '|` ' | sort > /tmp/declarado.txt
diff /tmp/declarado.txt /tmp/real.txt
```

Revisar además:

- **Métricas presentadas como reales.** El README afirma que no hay métricas reales. Cualquier
  cifra concreta (`mAP50: 0.87`, `reducción del 80% de OOM`, `~60% de ahorro`) debe ir marcada
  como ilustrativa o hipotética, o eliminarse. Es la inconsistencia más dañina del repositorio:
  un revisor que la detecte pone en duda todo lo demás.
- **Contradicciones entre documentos.** Ejemplo típico: un documento afirma "sin cola de trabajos"
  y un diagrama muestra `Queue training job`.
- **Duplicación de contenido.** Dos documentos que cubren el mismo tema (dos ADR de ClearML, dos
  ficheros `08-`) deben fusionarse o diferenciarse explícitamente en su encabezado.
- **Carpetas fantasma.** Directorios con ficheros vacíos que duplican una ruta real.

## Salida

Entregar una tabla ordenada por severidad, y nada más hasta que el usuario decida:

| # | Severidad | Categoría | Fichero:línea | Hallazgo | Acción propuesta |

Severidades:

- **Crítica** — fuga publicable: credencial, ruta real, nombre de cliente, imagen real.
- **Alta** — daño de credibilidad: métrica falsa presentada como real, contradicción entre documentos.
- **Media** — enlace roto, índice desincronizado, fichero vacío, duplicado.
- **Baja** — inconsistencia de formato o de estilo.

No aplicar correcciones sin confirmación, salvo que el usuario haya pedido explícitamente
"auditar y corregir". Si hay hallazgos **críticos**, decirlo en la primera línea de la respuesta.
