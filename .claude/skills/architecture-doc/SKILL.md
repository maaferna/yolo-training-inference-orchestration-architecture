---
name: architecture-doc
description: Crea o modifica documentos de arquitectura y ADRs en este repositorio siguiendo sus convenciones de numeración, estructura, tono y política public-safe. Usar al añadir un documento a docs/architecture/, escribir un Architecture Decision Record, reestructurar la documentación, o cuando se pida "documentar" un componente, flujo, riesgo o decisión técnica.
---

# Autoría de documentos de arquitectura

## Antes de escribir

1. Listar `docs/architecture/` (o `docs/evolution/`, o `docs/architecture/adr/`) y comprobar el
   siguiente número libre en disco. El validador solo detecta duplicados en `docs/architecture/`.
2. Comprobar si el tema ya está cubierto. La duplicación fue el defecto crónico de este
   repositorio. Ampliar un documento existente es preferible a crear uno nuevo.
   Los documentos de `docs/evolution/` describen una **revisión posterior** de la misma
   arquitectura: a nivel de categoría, sin nombres de módulo ni de tabla, sin fechas, sin
   vocabulario de sucesión ("legacy", "new platform", "migration" entre sistemas).
3. Leer `docs/architecture/02-system-architecture.md`: es la fuente de verdad sobre las fronteras
   entre capas. Un documento nuevo no puede contradecirla sin justificarlo explícitamente.

## Estructura de un documento de arquitectura

```markdown
# <Título en inglés, sin numeración en el título>

> Nota public-safe cuando el documento toque datos, rutas, métricas o infraestructura.

## Purpose            — por qué existe el documento, en 2-4 frases
## Context            — el problema operativo real que motiva el diseño
## <Secciones propias del tema>
## Constraints        — qué limita esta solución hoy
## Risks              — qué puede fallar y con qué consecuencia
## Recommended Improvements  — mejoras ordenadas por prioridad
## Summary            — cierre en un párrafo
```

Convenciones:

- Nombre de fichero: `NN-kebab-case-en-ingles.md`, dos dígitos.
- Idioma del contenido: inglés (todo el repositorio lo está).
- Diagramas: bloques ```text con arte ASCII de caja, o ```mermaid. Mantener el ancho por debajo
  de 78 caracteres para que se lea sin scroll horizontal.
- Tablas para matrices de decisión, responsabilidades y comparativas de opciones.
- Enlaces internos relativos, verificados contra el disco antes de escribirlos.

## Estructura de un ADR

Los ADRs viven en `docs/architecture/adr/`. Es la única ubicación válida.

```markdown
# ADR-NNN: <Decisión en voz activa>

**Status**: Proposed | Accepted | Accepted — not implemented | Superseded by ADR-NNN
**Iteration**: initial | revision
**Public-Safe**: Yes
**Supersedes** / **Amends**: ADR-NNN (cuando aplique; nunca una fecha)

## Context
El problema, las fuerzas en juego y las restricciones. Sin nombrar la solución todavía.

## Decision
Qué se decidió, en una frase, seguida del detalle.

## Alternatives Considered
Una subsección por alternativa, cada una con por qué se descartó. Un ADR sin alternativas
descartadas no demuestra criterio.

## Consequences
### Positive / ### Negative / ### Neutral

## Revisit When
Las condiciones operativas concretas que obligarían a reabrir la decisión.
```

`Revisit When` es la sección que distingue estos ADRs. La tesis del repositorio es "escalar por
evidencia operativa, no por defecto"; un ADR debe nombrar el disparador medible, no una intuición.

## Tono

El repositorio documenta un sistema interno honesto, no un producto. Mantener:

- **Explícito sobre lo que no hace.** Sin cola de trabajos, sin Kubernetes, ejecución síncrona,
  observabilidad básica. Se declara como decisión adecuada al contexto, no como carencia.
- **Distinción runtime vs plataforma.** Multi-GPU (DataParallel/DDP dentro de un entrenamiento)
  no es orquestación distribuida (colas, workers, schedulers). Nunca mezclarlas.
- **Adecuación al contexto.** Usuarios internos limitados, trabajos programados o esporádicos,
  trabajos largos esperados y aceptados.
- Sin superlativos de marketing, sin cifras de rendimiento inventadas.

## Regla de las cifras

Cualquier número concreto (mAP, tiempos, tamaños, porcentajes de ahorro) debe ir precedido de
"illustrative" o "hypothetical", o expresarse como rango cualitativo. El repositorio declara en
su README que no contiene métricas reales; una cifra sin marcar contradice esa declaración.

## Al terminar

1. Verificar que cada enlace nuevo apunta a un fichero existente.
2. Añadir la entrada al índice de `README.md` y a `docs/README.md`.
3. Ejecutar la skill `public-safe-audit` sobre el documento nuevo.
4. Si el documento describe un flujo o una topología, valorar un diagrama con `diagram-studio`.
