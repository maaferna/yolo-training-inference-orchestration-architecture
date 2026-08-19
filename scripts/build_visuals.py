#!/usr/bin/env python3
"""Genera los SVG de diagramas y posters del repositorio.

Fuente de verdad de todos los visuales. Los SVG en assets/src/ y los PNG en
assets/diagrams/ y assets/poster/ son productos derivados: no editarlos a mano.

Uso:  python3 scripts/build_visuals.py [directorio_salida]

El sistema de diseno esta documentado en
.claude/skills/diagram-studio/references/design-system.md
"""

from __future__ import annotations

import os
import sys
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------
# Sistema de diseno
# --------------------------------------------------------------------------

CANVAS = "#0A101C"
BAND = "#0E1524"
PANEL = "#141E31"
PANEL2 = "#1B2942"
STROKE = "#2A3B58"
STROKE_SOFT = "#1F2E47"
TEXT = "#EAF0FA"
DIM = "#94A6C4"
FAINT = "#63799B"

WEB = "#4FA8FF"
API = "#FFB13D"
GPU = "#7ED957"
TRACK = "#B98BFF"
STORE = "#FF7E8E"
DATA = "#35D6D0"
WARN = "#FF6B6B"

ACCENTS = {
    "web": WEB, "api": API, "gpu": GPU, "track": TRACK,
    "store": STORE, "data": DATA, "warn": WARN,
    "dim": DIM, "faint": FAINT, "stroke": STROKE_SOFT, "text": TEXT,
}

DISPLAY = "Montserrat, 'DejaVu Sans', sans-serif"
BODY = "Lato, 'DejaVu Sans', sans-serif"
MONO = "'Liberation Mono', 'DejaVu Sans Mono', monospace"

FOOTNOTE = "Public-safe architecture documentation · all values illustrative"
REPO = "yolo-training-inference-orchestration-architecture"


def _slug(color: str) -> str:
    return color.replace("#", "m")


# --------------------------------------------------------------------------
# Nucleo de dibujo
# --------------------------------------------------------------------------


class Canvas:
    """Acumula fragmentos SVG y los envuelve con defs, fondo y pie."""

    def __init__(self, width: int, height: int, title: str, subtitle: str = "",
                 kicker: str = "", pad: int = 56):
        self.w = width
        self.h = height
        self.title = title
        self.subtitle = subtitle
        self.kicker = kicker
        self.pad = pad
        self.parts: list[str] = []

    def add(self, fragment: str) -> "Canvas":
        self.parts.append(fragment)
        return self

    # -- cabecera y pie ----------------------------------------------------

    def header(self, y: int = 58, rule: bool = True) -> int:
        """Dibuja titulo y subtitulo. Devuelve la Y libre bajo la cabecera."""
        x = self.pad
        cur = y
        if self.kicker:
            self.add(text(x, cur, self.kicker.upper(), 12, FAINT,
                          family=BODY, weight=700, spacing=1.6))
            cur += 26
        self.add(text(x, cur + 8, self.title, 36, TEXT, family=DISPLAY, weight=700))
        cur += 20
        if self.subtitle:
            cur += 32
            self.add(text(x, cur, self.subtitle, 15, DIM, family=BODY))
        cur += 26
        if rule:
            self.add(line(x, cur, self.w - self.pad, cur, STROKE_SOFT, 1))
            cur += 26
        return cur

    def footer(self) -> None:
        y = self.h - 26
        self.add(line(self.pad, y - 22, self.w - self.pad, y - 22, STROKE_SOFT, 1))
        self.add(text(self.pad, y, REPO, 11, FAINT, family=MONO))
        self.add(text(self.w - self.pad, y, FOOTNOTE, 11, FAINT,
                      family=BODY, anchor="end"))

    # -- salida ------------------------------------------------------------

    def render(self) -> str:
        markers = "\n".join(
            f'<marker id="a-{_slug(c)}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M0,0.5 L10,5 L0,9.5 z" fill="{c}"/></marker>'
            for c in sorted(set(ACCENTS.values()))
        )
        body = "\n".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n'
            f'<defs>\n{markers}\n'
            f'<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#16233A"/>'
            f'<stop offset="1" stop-color="#0C1322"/></linearGradient>\n'
            f'</defs>\n'
            f'<rect width="{self.w}" height="{self.h}" fill="{CANVAS}"/>\n'
            f"{body}\n</svg>\n"
        )


def text(x: float, y: float, content: str, size: float, fill: str,
         family: str = BODY, weight: int = 400, anchor: str = "start",
         spacing: float = 0.0, opacity: float = 1.0) -> str:
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
            f'{ls}{op}>{escape(content)}</text>')


def line(x1: float, y1: float, x2: float, y2: float, color: str,
         width: float = 1.5, dashed: bool = False) -> str:
    da = ' stroke-dasharray="6 5"' if dashed else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}"{da}/>')


def rect(x: float, y: float, w: float, h: float, fill: str,
         stroke: str = "none", rx: float = 10, width: float = 1.5,
         dashed: bool = False, opacity: float = 1.0) -> str:
    da = ' stroke-dasharray="7 6"' if dashed else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    sw = f' stroke-width="{width}"' if stroke != "none" else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}"{sw}{da}{op}/>')


def chip(x: float, y: float, label: str, color: str, size: float = 11) -> str:
    """Etiqueta en pastilla. y es el borde superior. Devuelve el SVG."""
    w = len(label) * size * 0.68 + 20
    h = size + 10
    return (rect(x, y, w, h, color, rx=999, opacity=0.16)
            + text(x + w / 2, y + h - (h - size) / 2 - 1.5, label, size, color,
                   family=BODY, weight=700, anchor="middle", spacing=0.7))


def chip_width(label: str, size: float = 11) -> float:
    return len(label) * size * 0.68 + 20


_CLIP_N = 0


def box(x: float, y: float, w: float, h: float, accent: str, title: str,
        lines: list[str] | None = None, fill: str = PANEL, dashed: bool = False,
        title_size: float = 17, line_size: float = 13, tag: str = "",
        centered: bool = False, line_color: str = DIM) -> str:
    """Caja estandar: barra de acento arriba, titulo, hasta 4 lineas de detalle."""
    lines = lines or []
    global _CLIP_N
    _CLIP_N += 1
    cid = f"clip{_CLIP_N}"
    out = [rect(x, y, w, h, fill, STROKE, rx=10, dashed=dashed)]
    # barra de acento superior, recortada al radio de la caja
    out.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" '
               f'height="{h}" rx="10"/></clipPath>')
    out.append(f'<g clip-path="url(#{cid})">'
               f'<rect x="{x}" y="{y}" width="{w}" height="5" fill="{accent}"/></g>')

    tx = x + w / 2 if centered else x + 18
    anchor = "middle" if centered else "start"

    ty = y + 20 + title_size
    if tag:
        out.append(text(tx, y + 26, tag.upper(), 10, accent, family=BODY,
                        weight=700, anchor=anchor, spacing=1.4))
        ty = y + 30 + title_size
    out.append(text(tx, ty, title, title_size, TEXT, family=DISPLAY,
                    weight=600, anchor=anchor))

    ly = ty + 21
    for entry in lines:
        color = line_color
        content = entry
        if entry.startswith("!"):
            color, content = WARN, entry[1:]
        elif entry.startswith("`"):
            out.append(text(tx, ly, content.strip("`"), line_size - 0.5, FAINT,
                            family=MONO, anchor=anchor))
            ly += line_size + 6
            continue
        out.append(text(tx, ly, content, line_size, color, family=BODY,
                        anchor=anchor))
        ly += line_size + 6
    return "\n".join(out)


def band(x: float, y: float, w: float, h: float, label: str, color: str,
         dashed: bool = False, note: str = "") -> str:
    """Contenedor de seccion con etiqueta vertical de color en el borde izquierdo."""
    out = [rect(x, y, w, h, BAND, STROKE_SOFT, rx=14, dashed=dashed)]
    out.append(rect(x + 1.5, y + 14, 4, h - 28, color, rx=2, opacity=0.75))
    out.append(text(x + 20, y + 27, label.upper(), 12, color, family=BODY,
                    weight=700, spacing=1.5))
    if note:
        out.append(text(x + w - 20, y + 27, note, 12, FAINT, family=BODY,
                        anchor="end"))
    return "\n".join(out)


def arrow(points: list[tuple[float, float]], color: str, label: str = "",
          dashed: bool = False, label_at: float = 0.5, width: float = 2,
          label_dx: float = 0, label_dy: float = -8) -> str:
    """Flecha ortogonal por una polilinea de puntos."""
    pts = " ".join(f"{px},{py}" for px, py in points)
    da = ' stroke-dasharray="6 5"' if dashed else ""
    out = [f'<polyline points="{pts}" fill="none" stroke="{color}" '
           f'stroke-width="{width}" stroke-linejoin="round"{da} '
           f'marker-end="url(#a-{_slug(color)})"/>']
    if label:
        # posiciona la etiqueta sobre el segmento mas largo
        best, blen = 0, -1.0
        for i in range(len(points) - 1):
            seg = abs(points[i + 1][0] - points[i][0]) + abs(points[i + 1][1] - points[i][1])
            if seg > blen:
                best, blen = i, seg
        (x1, y1), (x2, y2) = points[best], points[best + 1]
        lx = x1 + (x2 - x1) * label_at + label_dx
        ly = y1 + (y2 - y1) * label_at + label_dy
        wpx = len(label) * 5.9 + 14
        out.append(rect(lx - wpx / 2, ly - 12, wpx, 17, CANVAS, rx=4))
        out.append(text(lx, ly, label, 11, DIM, family=BODY, weight=700,
                        anchor="middle"))
    return "\n".join(out)


def legend(x: float, y: float, items: list[tuple[str, str]], gap: float = 22) -> str:
    """Leyenda horizontal de pares (color, etiqueta)."""
    out = []
    cx = x
    for color, label in items:
        out.append(rect(cx, y - 8, 11, 11, color, rx=3))
        out.append(text(cx + 18, y + 1, label, 12, DIM, family=BODY))
        cx += 18 + len(label) * 6.4 + gap
    return "\n".join(out)


def step_number(x: float, y: float, n: int, color: str, r: float = 15) -> str:
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.18"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="1.5"/>'
            + text(x, y + 5, str(n), 14, color, family=DISPLAY, weight=700,
                   anchor="middle"))


# --------------------------------------------------------------------------
# 01 · Arquitectura del sistema
# --------------------------------------------------------------------------


def diagram_system_architecture() -> str:
    c = Canvas(1600, 1000,
               title="System Architecture",
               subtitle="Web orchestration separated from GPU-intensive AI processing. "
                        "One synchronous HTTP boundary, one shared artifact contract.",
               kicker="Internal AI vision platform")
    c.header()

    MX, MW = 100, 936          # columna principal
    SX, SW = 1064, 480         # columna lateral
    cx = MX + MW / 2

    # -- usuarios y contexto de despliegue --------------------------------
    c.add(box(MX, 192, MW, 54, WEB, "Internal users · operations, research, technical staff",
              title_size=16, centered=True))
    c.add(box(SX, 192, SW, 54, DIM, "Docker Compose · single node",
              title_size=16, centered=True))

    # -- capa web ----------------------------------------------------------
    c.add(box(MX, 274, MW, 126, WEB, "Django Web Layer", tag="web orchestration", lines=[
        "Project and dataset configuration · authentication and permissions",
        "Training and inference request submission · request metadata",
        "Result visualization, artifact references, execution history",
        "!Does not execute GPU workloads inside the web process",
    ]))
    c.add(box(SX, 274, SW, 126, STORE, "Relational Database", tag="metadata store", lines=[
        "Users, projects, permissions",
        "ProjectConfiguration · DetectionClass",
        "ClassSet · DatasetConfiguration",
        "Request records and result references",
    ]))
    c.add(arrow([(MX + MW + 2, 337), (SX - 2, 337)], STORE))

    # -- servicio de IA ----------------------------------------------------
    c.add(arrow([(cx, 402), (cx, 444)], API,
                label="HTTP / REST · structured payload"))
    c.add(box(MX, 448, MW, 126, API, "FastAPI AI Service", tag="ai service boundary", lines=[
        "Request validation and artifact resolution · training orchestration",
        "Continuous improvement training · YOLO and SAHI inference dispatch",
        "Experiment coordination · artifact generation · error propagation",
        "!Synchronous execution: long-running jobs block the request",
    ]))
    c.add(box(SX, 448, SW, 126, TRACK, "Experiment Tracking", tag="clearml or equivalent", lines=[
        "Run metadata and configuration",
        "Metric logging and run comparison",
        "Model artifact references, lineage",
        "!Not a transactional model registry",
    ]))
    c.add(arrow([(MX + MW + 2, 511), (SX - 2, 511)], TRACK))

    # -- runtime GPU -------------------------------------------------------
    c.add(arrow([(cx, 576), (cx, 618)], GPU,
                label="dispatch · train · validate · infer"))
    c.add(band(MX, 622, MW, 160, "GPU compute runtime", GPU,
               note="Ubuntu · NVIDIA CUDA · PyTorch · Docker GPU access"))
    c.add(box(116, 664, 292, 104, GPU, "YOLO Training", lines=[
        "Multi-seed experimentation",
        "Validation-based model selection",
        "CUDA cleanup between runs",
    ], title_size=16, line_size=12.5))
    c.add(box(422, 664, 292, 104, GPU, "CI Training", lines=[
        "Resolves previous baseline",
        "Incremental fine-tuning",
        "Conditional reference update",
    ], title_size=16, line_size=12.5))
    c.add(box(728, 664, 292, 104, GPU, "SAHI Inference", lines=[
        "Tiling · per-tile detection",
        "Merge and NMS deduplication",
        "Preview and manifest output",
    ], title_size=16, line_size=12.5))
    c.add(arrow([(MX + MW + 2, 686), (1050, 686), (1050, 552), (SX - 2, 552)],
                TRACK, label="metrics", label_at=0.55, label_dx=0, label_dy=-9))

    # -- lo que deliberadamente no existe ---------------------------------
    c.add(box(SX, 622, SW, 160, FAINT, "Explicit non-goals", tag="scoped out by design",
              dashed=True, lines=[
                  "No job queue or background workers",
                  "No GPU-aware scheduler or worker pool",
                  "No Kubernetes, no multi-region",
                  "Added only on operational evidence",
              ]))

    # -- almacenamiento compartido ----------------------------------------
    c.add(arrow([(cx, 784), (cx, 808)], STORE))
    c.add(box(MX, 812, 1444, 96, STORE, "Shared Artifact Storage", tag="path contract", lines=[
        "models/ · training_runs/ · inference_runs/ · reports/   —   checkpoints, "
        "selected model reference, summaries, previews, manifests, GIS outputs",
        "!Risks: path mismatch across containers, concurrent writes to the model "
        "reference, stale references, unbounded growth",
    ], line_size=12.5))

    # -- retorno de artefactos --------------------------------------------
    c.add(arrow([(MX - 2, 860), (76, 860), (76, 337), (MX - 2, 337)], STORE, dashed=True))
    c.add(f'<text transform="rotate(-90 64 600)" x="64" y="600" '
          f'font-family="{BODY}" font-size="11" font-weight="700" fill="{FAINT}" '
          f'text-anchor="middle">artifact references and results</text>')

    c.add(legend(MX, 938, [
        (WEB, "Web layer"), (API, "AI service"), (GPU, "GPU runtime"),
        (TRACK, "Experiment tracking"), (STORE, "Storage and metadata"),
        (WARN, "Documented risk"),
    ]))
    c.footer()
    return c.render()


def lane(c: Canvas, y: float, h: float, label: str, color: str,
         x: float = 56, w: float = 1488) -> None:
    """Carril horizontal con etiqueta a la izquierda."""
    c.add(rect(x, y, w, h, BAND, STROKE_SOFT, rx=14))
    c.add(rect(x + 1.5, y + 14, 4, h - 28, color, rx=2, opacity=0.75))
    for i, part in enumerate(label.split("|")):
        c.add(text(x + 20, y + 30 + i * 18, part.strip().upper(), 12,
                   color if i == 0 else FAINT, family=BODY, weight=700,
                   spacing=1.3))


# --------------------------------------------------------------------------
# 02 · Flujo de entrenamiento
# --------------------------------------------------------------------------


def diagram_training_flow() -> str:
    c = Canvas(1600, 1000,
               title="Training Request Flow",
               subtitle="From a submitted request to a selected model reference. "
                        "Django blocks for the duration: the request is synchronous by design.",
               kicker="Multi-seed training · validation-based selection")
    c.header()

    COL = [240, 460, 680, 900, 1120, 1340]
    BW = 200

    lane(c, 192, 136, "Django | web layer", WEB)
    lane(c, 368, 136, "FastAPI | ai service", API)
    lane(c, 544, 156, "GPU runtime | pytorch · cuda · yolo", GPU)
    lane(c, 740, 136, "Artifacts | storage · tracking", STORE)

    c.add(box(COL[0], 200, BW, 120, WEB, "Submit request", tag="step 1", lines=[
        "Validate project and",
        "dataset configuration",
        "Persist request metadata",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[1], 376, BW, 120, API, "Dispatch", tag="step 2", lines=[
        "Validate payload",
        "Resolve dataset and paths",
        "Initialize tracking run",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[2], 552, BW, 140, GPU, "Train per seed", tag="step 3", lines=[
        "Loop over 3-5 seeds",
        "Epoch loop and validation",
        "Save checkpoint per run",
        "Release CUDA memory",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[3], 376, BW, 120, API, "Select model", tag="step 4", lines=[
        "Aggregate metrics",
        "across seeds",
        "Pick best by validation",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[2], 748, BW, 120, TRACK, "Log experiment", tag="continuous", lines=[
        "Per-epoch metrics",
        "Configuration and lineage",
        "Run comparison context",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[4], 748, BW, 120, STORE, "Persist artifacts", tag="step 5", lines=[
        "Checkpoint and summary",
        "Selected model reference",
        "Run identifier and manifest",
    ], title_size=16, line_size=12.5))

    c.add(box(COL[5], 200, BW, 120, WEB, "Expose results", tag="step 6", lines=[
        "Status and metric summary",
        "Artifact links and previews",
        "Execution history entry",
    ], title_size=16, line_size=12.5))

    # -- transiciones ------------------------------------------------------
    c.add(arrow([(340, 322), (340, 346), (560, 346), (560, 372)], API,
                label="HTTP request", label_at=0.5, label_dy=-7))
    c.add(arrow([(560, 498), (560, 522), (740, 522), (740, 548)], GPU,
                label="start training", label_at=0.5, label_dy=-7))
    c.add(arrow([(820, 548), (820, 514), (1000, 514), (1000, 502)], API,
                label="metrics per seed", label_at=0.5, label_dy=-7))
    c.add(arrow([(1000, 498), (1000, 520), (1220, 520), (1220, 744)], STORE,
                label="write", label_at=0.18, label_dy=-7))
    c.add(arrow([(780, 694), (780, 744)], TRACK, dashed=True))
    c.add(arrow([(1320, 808), (1400, 808), (1400, 326)], WEB,
                label="result references", label_at=0.62, label_dx=54, label_dy=4))

    # -- nota arquitectonica ----------------------------------------------
    c.add(box(56, 890, 1488, 56, WARN,
              "Synchronous boundary: the HTTP request stays open for the whole training run. "
              "Acceptable for scheduled internal jobs; a queue is justified once timeouts, "
              "concurrency or cancellation become routine.",
              title_size=14, centered=True, tag=""))
    c.footer()
    return c.render()


def diamond(cx: float, cy: float, rx: float, ry: float, color: str,
            lines: list[str], size: float = 14) -> str:
    pts = f"{cx},{cy - ry} {cx + rx},{cy} {cx},{cy + ry} {cx - rx},{cy}"
    out = [f'<polygon points="{pts}" fill="{PANEL2}" stroke="{color}" '
           f'stroke-width="2"/>']
    start = cy - (len(lines) - 1) * (size + 5) / 2 + size * 0.35
    for i, ln in enumerate(lines):
        fam = MONO if ln.startswith("`") else DISPLAY
        out.append(text(cx, start + i * (size + 5), ln.strip("`"),
                        size, TEXT if i == 0 else DIM, family=fam,
                        weight=600 if i == 0 else 400, anchor="middle"))
    return "\n".join(out)


# --------------------------------------------------------------------------
# 03 · Entrenamiento de mejora continua
# --------------------------------------------------------------------------


def diagram_ci_training() -> str:
    c = Canvas(1600, 1000,
               title="Continuous Improvement Training",
               subtitle="New data never silently replaces the production model. "
                        "The reference moves only when the improvement rule is satisfied.",
               kicker="Conditional model promotion")
    c.header()

    c.add(box(100, 245, 250, 170, DATA, "New data", tag="input", lines=[
        "Expanded dataset or",
        "updated configuration",
        "submitted for retraining",
    ], title_size=17, line_size=13))

    c.add(box(390, 245, 250, 170, STORE, "Resolve baseline", tag="previous state", lines=[
        "Read selected model",
        "reference from storage",
        "Capture historical",
        "validation metrics",
    ], title_size=17, line_size=13))

    c.add(box(680, 245, 250, 170, GPU, "Incremental training", tag="gpu runtime", lines=[
        "Fine-tune from the",
        "previous checkpoint",
        "Validate on the",
        "evaluation split",
    ], title_size=17, line_size=13))

    c.add(arrow([(352, 330), (388, 330)], STORE))
    c.add(arrow([(642, 330), (678, 330)], GPU))
    c.add(arrow([(932, 330), (978, 330)], API))

    c.add(diamond(1090, 330, 108, 84, API, [
        "Improvement",
        "rule satisfied?",
    ], size=15))
    c.add(chip(1090 - chip_width("new metric - baseline  >=  threshold") / 2, 438,
               "new metric - baseline  >=  threshold", API))

    c.add(box(1250, 230, 294, 96, GPU, "Promote new model", lines=[
        "Write checkpoint, update the selected",
        "model reference, log the improvement",
    ], title_size=16, line_size=12.5))
    c.add(box(1250, 350, 294, 96, DIM, "Keep previous model", lines=[
        "Retain the existing reference, record",
        "the run and the rejected comparison",
    ], title_size=16, line_size=12.5))

    c.add(arrow([(1198, 330), (1222, 330), (1222, 278), (1248, 278)], GPU,
                label="yes", label_at=0.5, label_dx=-6, label_dy=-8))
    c.add(arrow([(1198, 330), (1222, 330), (1222, 398), (1248, 398)], DIM,
                label="no", label_at=0.5, label_dx=-6, label_dy=14))

    # -- lo que queda registrado ------------------------------------------
    c.add(band(100, 525, 1444, 150, "Recorded for every run, promoted or not", TRACK))
    reg = [
        (TRACK, "Experiment metadata", ["Run identifier, configuration,", "environment context"]),
        (TRACK, "Metric comparison", ["Baseline versus candidate,", "decision and threshold"]),
        (STORE, "Artifact manifest", ["Checkpoint paths, summaries,", "generated outputs"]),
        (DATA, "Dataset lineage", ["Dataset version, class mapping,", "configuration reference"]),
    ]
    for i, (col, title_, ls) in enumerate(reg):
        c.add(box(116 + i * 356, 569, 342, 90, col, title_, lines=ls,
                  title_size=15, line_size=12))

    # -- riesgo ------------------------------------------------------------
    c.add(box(100, 730, 1444, 116, WARN, "Known risk · file-based model reference",
              tag="documented limitation", lines=[
                  "Two promotions running at once can race on the same reference file, "
                  "leaving a checkpoint and its metadata out of sync.",
                  "Mitigation path: move the selected-model pointer into the database as a "
                  "transactional record before parallel training becomes routine.",
              ], line_size=13))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 04 · Inferencia SAHI
# --------------------------------------------------------------------------


def diagram_sahi_inference() -> str:
    c = Canvas(1600, 1000,
               title="SAHI Tiled Inference",
               subtitle="A small object covering a few pixels of a 4K frame is nearly invisible "
                        "to a 640-pixel detector. Tiling restores its apparent scale.",
               kicker="High-resolution small-object detection")
    c.header()

    # -- panel de teselado -------------------------------------------------
    c.add(band(100, 240, 420, 340, "1 · slice", DATA))
    ix, iy, isz = 190, 306, 240
    c.add(rect(ix, iy, isz, isz, "#101A2C", STROKE, rx=6))
    for k in range(1, 4):                                  # retícula de paso
        c.add(line(ix + k * 60, iy, ix + k * 60, iy + isz, STROKE_SOFT, 1))
        c.add(line(ix, iy + k * 60, ix + isz, iy + k * 60, STROKE_SOFT, 1))
    # dos teselas solapadas
    c.add(rect(ix + 30, iy + 60, 120, 120, DATA, DATA, rx=4, width=2, opacity=0.10))
    c.add(rect(ix + 30, iy + 60, 120, 120, "none", DATA, rx=4, width=2))
    c.add(rect(ix + 90, iy + 60, 120, 120, GPU, GPU, rx=4, width=2, opacity=0.10))
    c.add(rect(ix + 90, iy + 60, 120, 120, "none", GPU, rx=4, width=2))
    c.add(rect(ix + 90, iy + 60, 60, 120, API, "none", rx=0, opacity=0.20))
    for ox, oy in [(118, 118), (135, 152), (176, 92), (64, 176), (208, 150)]:
        c.add(f'<circle cx="{ix + ox}" cy="{iy + oy}" r="4.5" fill="{WARN}"/>')
    c.add(text(310, 578 - 12, "overlap keeps boundary objects whole in at least one tile",
               11.5, DIM, family=BODY, anchor="middle"))
    c.add(text(310, 292, "4096 px frame  ·  640 px tiles  ·  50% overlap", 12, FAINT,
               family=MONO, anchor="middle"))

    # -- inferencia por tesela --------------------------------------------
    c.add(band(560, 240, 380, 340, "2 · detect", GPU))
    c.add(box(576, 286, 348, 128, GPU, "Per-tile YOLO inference", lines=[
        "Each tile is resized to the model",
        "input and inferred independently",
        "A 20 px object in the frame becomes",
        "a well-sized object inside its tile",
    ], title_size=16, line_size=12.5))
    c.add(box(576, 430, 348, 134, WARN, "Cost of the strategy", lines=[
        "Tile count grows with overlap:",
        "50% overlap on a 2x2 grid means",
        "roughly 4x the forward passes",
        "GPU memory stays flat, time does not",
    ], title_size=16, line_size=12.5))

    # -- reconstruccion ----------------------------------------------------
    c.add(band(980, 240, 564, 340, "3 · reconstruct", API))
    c.add(box(996, 286, 532, 128, API, "Merge and deduplicate", lines=[
        "Tile-local coordinates are mapped back to full-frame coordinates,",
        "then detections from overlapping tiles are merged with NMS over IoU",
        "so the same object seen in two tiles is reported once.",
    ], title_size=16, line_size=12.5))
    c.add(box(996, 430, 532, 134, STORE, "Output artifacts", lines=[
        "Detection manifest: class, confidence, box, tile provenance",
        "Compressed preview for web visualization",
        "Run summary and counts per class",
        "GIS-compatible vector output when applicable",
    ], title_size=16, line_size=12.5))

    c.add(arrow([(522, 410), (558, 410)], GPU))
    c.add(arrow([(942, 410), (978, 410)], API))

    # -- configuraciones ---------------------------------------------------
    c.add(band(100, 620, 1444, 180, "Configuration trade-off", API,
               note="direction of effect only · no measured values"))
    cfgs = [
        (DATA, "Throughput first", "1024 px tiles · 25% overlap",
         ["Fewest forward passes, lowest latency",
          "Weakest recall on the smallest objects"]),
        (GPU, "Balanced", "800 px tiles · 33% overlap",
         ["Documented starting point for batch work",
          "Tune from measurements, not from defaults"]),
        (TRACK, "Recall first", "640 px tiles · 50% overlap",
         ["Strongest small-object recall",
          "Highest compute cost per frame"]),
    ]
    for i, (col, title_, cfg, ls) in enumerate(cfgs):
        x = 116 + i * 475
        c.add(box(x, 664, 461, 120, col, title_, tag="", lines=[f"`{cfg}`"] + ls,
                  title_size=16, line_size=12.5))

    c.add(box(100, 830, 1444, 76, WARN,
              "Tile size and overlap are the only two knobs that matter, and they trade "
              "compute against small-object recall. Measure on the real image distribution "
              "before fixing them.", title_size=14, centered=True))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 05 · Estrategia de despliegue y coste
# --------------------------------------------------------------------------


def diagram_deployment_strategy() -> str:
    c = Canvas(1600, 1000,
               title="Deployment and Cost Strategy",
               subtitle="Where training runs and where the application lives are two separate "
                        "decisions. Treating them as one is what makes GPU cloud bills grow.",
               kicker="Local · cloud · hybrid")
    c.header()

    opts = [
        (100, DIM, "Option A", "Fully local GPU", False, [
            "Fixed, predictable cost",
            "Raw imagery never leaves the site",
            "No transfer charges on large datasets",
        ], [
            "No elastic scaling",
            "Hardware and maintenance are owned",
            "Remote access must be built",
        ], [
            "Datasets are large and stay on site",
            "Cost must be fixed and predictable",
        ]),
        (596, DIM, "Option B", "Fully cloud GPU", False, [
            "Elastic capacity on demand",
            "Native fit with an existing cloud intranet",
            "No hardware ownership",
        ], [
            "Multi-day training is expensive",
            "Uploading raw campaigns costs bandwidth",
            "Idle GPU time is billed unless ephemeral",
        ], [
            "No GPU hardware is owned",
            "Workloads are short and bursty",
        ]),
        (1092, API, "Option C", "Hybrid", True, [
            "Training stays next to the data and the GPU",
            "Application and metadata stay next to the users",
            "Only selected artifacts cross the boundary",
        ], [
            "Two environments to govern",
            "Model lineage must span both sides",
            "Sync rules must be explicit",
        ], [
            "Training is heavy and data is local",
            "Users already live in the cloud",
        ]),
    ]
    for x, col, tag_, title_, rec, pros, cons, best in opts:
        accent = API if rec else DIM
        c.add(box(x, 225, 452, 400, accent, title_, tag=tag_, lines=[], dashed=not rec))
        if rec:
            c.add(chip(x + 452 - chip_width("recommended baseline") - 18, 233,
                       "recommended baseline", API))
        y = 320
        c.add(text(x + 18, y, "STRENGTHS", 11, GPU, family=BODY, weight=700, spacing=1.3))
        y += 24
        for pro in pros:
            c.add(text(x + 18, y, "+   " + pro, 12.5, DIM, family=BODY))
            y += 24
        y += 18
        c.add(text(x + 18, y, "LIMITATIONS", 11, WARN, family=BODY, weight=700, spacing=1.3))
        y += 24
        for con in cons:
            c.add(text(x + 18, y, "-   " + con, 12.5, DIM, family=BODY))
            y += 24
        y += 18
        c.add(text(x + 18, y, "BEST WHEN", 11, accent, family=BODY, weight=700, spacing=1.3))
        y += 24
        for bw in best:
            c.add(text(x + 18, y, bw, 12.5, TEXT if rec else DIM, family=BODY))
            y += 24

    # -- que cruza la frontera --------------------------------------------
    c.add(band(100, 660, 1444, 156, "What crosses the boundary", DATA))
    c.add(box(116, 704, 700, 96, DATA, "Stays local", lines=[
        "Raw drone imagery · training datasets · intermediate checkpoints ·",
        "heavy batch inference over full campaigns · synthetic generation runs",
    ], title_size=16, line_size=12.5))
    c.add(box(844, 704, 684, 96, WEB, "Synchronized to the cloud", lines=[
        "Selected checkpoint with its metadata · class mapping · dataset version ·",
        "validation summary · compact previews · reports · artifact manifest",
    ], title_size=16, line_size=12.5))
    c.add(arrow([(820, 752), (840, 752)], WEB))

    c.add(box(100, 846, 1444, 62, API,
              "Train where the data and the GPU cost make sense. "
              "Serve where the users and the application already are.",
              title_size=19, centered=True))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 06 · Pipeline de dataset sintetico
# --------------------------------------------------------------------------


def diagram_synthetic_dataset() -> str:
    c = Canvas(1600, 1000,
               title="Synthetic Dataset Generation",
               subtitle="When annotated examples of a class are scarce, cut real objects out of "
                        "the images that exist and recompose them into new labelled scenes.",
               kicker="Dataset engineering · auxiliary research workflow")
    c.header()

    steps = [
        (DATA, "Load configuration", ["Read the YAML contract:", "paths, classes, parameters",
                                      "Create the version directory"]),
        (DATA, "Resolve dataset", ["Detect the YOLO layout", "Count images and labels",
                                   "Map class IDs to names"]),
        (TRACK, "Box to mask", ["SAM turns each bounding box", "into a segmentation mask",
                                "Save binary and colour masks"]),
        (TRACK, "Extract shapes", ["Apply the mask to the source", "Recrop to the tight rectangle",
                                   "Save an RGBA cutout per object"]),
        (WARN, "Filter quality", ["Drop objects below the", "minimum size, cap the",
                                  "maximum area fraction"]),
        (GPU, "Prepare backgrounds", ["Load and validate the", "background pool",
                                      "Cache for random selection"]),
        (GPU, "Compose scenes", ["Scale, rotate and jitter", "Check bounds and overlap",
                                 "Alpha blend onto background"]),
        (API, "Normalize labels", ["Emit COCO annotations", "Validate image and annotation",
                                   "correspondence"]),
        (API, "Export formats", ["COCO to YOLO conversion", "Generate dataset.yaml",
                                 "Re-emit the image tree"]),
        (STORE, "Hand off", ["CVAT for review", "Roboflow for management",
                             "or straight into training"]),
    ]
    xs = [100 + i * 292 for i in range(5)]
    for i, (col, title_, ls) in enumerate(steps):
        row, colidx = divmod(i, 5)
        x = xs[colidx]
        y = 245 if row == 0 else 485
        c.add(box(x, y, 272, 170, col, title_, tag=f"step {i + 1}", lines=ls,
                  title_size=15.5, line_size=12))
        if colidx < 4:
            c.add(arrow([(x + 274, y + 85), (x + 290, y + 85)], col))

    c.add(arrow([(1372, 417), (1372, 450), (236, 450), (236, 483)], GPU,
                label="continue", label_at=0.5, label_dy=-7))

    # -- entradas y salidas ------------------------------------------------
    c.add(band(100, 700, 1444, 160, "Inputs and outputs", DATA))
    io = [
        (DATA, "Input", ["A small real dataset in YOLO", "format plus a background pool"]),
        (TRACK, "Intermediate", ["SAM masks and an album of", "RGBA object cutouts by class"]),
        (GPU, "Output", ["Synthetic images with COCO", "and YOLO annotations"]),
        (WARN, "Boundary", ["Auxiliary research path, not", "the production execution model"]),
    ]
    for i, (col, title_, ls) in enumerate(io):
        c.add(box(116 + i * 356, 744, 342, 100, col, title_, lines=ls,
                  title_size=15, line_size=12))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 07 · Hoja de ruta de evolucion
# --------------------------------------------------------------------------


def diagram_evolution_roadmap() -> str:
    c = Canvas(1600, 1000,
               title="Production Evolution Roadmap",
               subtitle="Every stage names the operational evidence that justifies it. "
                        "Nothing on this path is scheduled; each item waits for its trigger.",
               kicker="Scale by evidence, not by default")
    c.header()

    c.add(box(100, 230, 280, 310, WEB, "Current state", tag="today", lines=[
        "Django web layer",
        "FastAPI AI service",
        "Synchronous HTTP boundary",
        "Shared artifact storage",
        "GPU-backed training runtime",
        "Experiment tracking and manifests",
        "Docker Compose on a single node",
        "Ubuntu GPU runtime baseline",
    ], title_size=18, line_size=13))
    c.add(text(118, 522, "Sufficient while volume is predictable", 11.5, FAINT, family=BODY))

    stages = [
        (GPU, "Priority 1", "Operational reliability", [
            "Preflight checks: dataset,",
            "checkpoint, storage, GPU",
            "Explicit job status records",
            "Structured logs, correlation IDs",
            "Artifact manifest per run",
        ], "Do this first. It costs little and removes most silent failures."),
        (API, "Priority 2", "Background execution", [
            "Lightweight queue",
            "Single GPU worker",
            "Job status polling",
            "Retry policy, GPU locking",
        ], "Trigger: repeated timeouts, jobs competing for the GPU, cancellation needed."),
        (TRACK, "Priority 3", "Artifact governance", [
            "Model reference in the database",
            "Dataset version registry",
            "Immutable run identifiers",
            "Retention policy for outputs",
        ], "Trigger: lineage questions become hard to answer from storage alone."),
        (FAINT, "Optional", "Scale-out", [
            "GPU worker pool",
            "Object storage",
            "Kubernetes or equivalent",
            "Centralized monitoring",
        ], "Trigger: concurrent long-running jobs, storage beyond local capacity, "
           "uptime becomes business-critical."),
    ]
    for i, (col, tag_, title_, ls, trig) in enumerate(stages):
        x = 420 + i * 286
        c.add(box(x, 230, 264, 310, col, title_, tag=tag_, lines=ls,
                  title_size=16, line_size=12.5, dashed=(col is FAINT)))
        words, cur, out = trig.split(), "", []
        for wd in words:
            if len(cur) + len(wd) + 1 > 34:
                out.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        out.append(cur)
        ty = 540 - 16 - len(out) * 17
        c.add(line(x + 18, ty - 22, x + 246, ty - 22, STROKE_SOFT, 1))
        for ln in out:
            c.add(text(x + 18, ty, ln, 11.5, FAINT, family=BODY))
            ty += 17
        if i < 3:
            c.add(arrow([(x + 266, 385), (x + 282, 385)], stages[i + 1][0]))
    c.add(arrow([(382, 385), (416, 385)], GPU))

    # -- cuando no anadir infraestructura ---------------------------------
    c.add(band(100, 596, 1444, 150, "When not to add distributed infrastructure", WARN))
    nots = [
        "Workload volume is predictable and low",
        "Users understand that jobs run long",
        "One GPU is not yet contended",
        "No uptime commitment exists yet",
        "Traceability is the real gap, not throughput",
        "The team cannot operate a scheduler today",
    ]
    for i, txt_ in enumerate(nots):
        col_, row_ = divmod(i, 2)
        c.add(text(132 + col_ * 480, 654 + row_ * 36, "✕", 13, WARN, family=BODY))
        c.add(text(154 + col_ * 480, 654 + row_ * 36, txt_, 13.5, DIM, family=BODY))

    c.add(box(100, 800, 1444, 64, WEB,
              "Reliability, traceability and artifact governance return more, at this scale, "
              "than any distributed component added ahead of the evidence for it.",
              title_size=15, centered=True))
    c.footer()
    return c.render()


def section(c: Canvas, y: float, label: str, color: str,
            x: float = 88, w: float = 1064, note: str = "") -> None:
    """Encabezado de seccion del poster: marca de color, rotulo y filete."""
    c.add(rect(x, y - 11, 5, 15, color, rx=2))
    c.add(text(x + 16, y, label.upper(), 14, TEXT, family=DISPLAY, weight=700,
               spacing=1.4))
    lx = x + 16 + len(label) * 9.6 + 18
    if note:
        c.add(text(x + w, y, note, 12, FAINT, family=BODY, anchor="end"))
        c.add(line(lx, y - 5, x + w - len(note) * 6.1 - 16, y - 5, STROKE_SOFT, 1))
    else:
        c.add(line(lx, y - 5, x + w, y - 5, STROKE_SOFT, 1))


def chip_row(c: Canvas, x: float, y: float, max_w: float,
             items: list[tuple[str, str]], gap: float = 8,
             line_gap: float = 30) -> float:
    """Coloca pastillas con salto de linea. Devuelve la Y bajo la ultima fila."""
    cx, cy = x, y
    for color, label in items:
        wd = chip_width(label)
        if cx + wd > x + max_w:
            cx, cy = x, cy + line_gap
        c.add(chip(cx, cy, label, color))
        cx += wd + gap
    return cy + line_gap


# --------------------------------------------------------------------------
# Poster · resumen de una pagina
# --------------------------------------------------------------------------


def poster_architecture() -> str:
    c = Canvas(1240, 1754, title="", pad=88)
    X, W = 88, 1064

    # -- cabecera ----------------------------------------------------------
    c.add(rect(0, 0, 1240, 400, "url(#glow)"))
    c.add(text(X, 104, "ARCHITECTURE POSTER · PUBLIC-SAFE DOCUMENTATION", 13, API,
               family=BODY, weight=700, spacing=2.2))
    c.add(text(X, 182, "YOLO Training & Inference", 58, TEXT, family=DISPLAY, weight=800))
    c.add(text(X, 246, "Orchestration Architecture", 58, TEXT, family=DISPLAY, weight=800))
    c.add(text(X, 292, "An internal AI vision platform that keeps web orchestration and "
                       "GPU-intensive", 16, DIM, family=BODY))
    c.add(text(X, 316, "machine learning behind one deliberate, synchronous service boundary.",
               16, DIM, family=BODY))
    chip_row(c, X, 342, W, [
        (WEB, "Django"), (WEB, "Django REST"), (API, "FastAPI"), (GPU, "PyTorch"),
        (GPU, "CUDA"), (GPU, "Ultralytics YOLO"), (GPU, "SAHI"), (TRACK, "SAM"),
        (TRACK, "ClearML"), (STORE, "PostgreSQL"), (DATA, "Docker Compose"),
        (DATA, "Ubuntu"),
    ])

    # -- seccion A · el sistema -------------------------------------------
    section(c, 452, "The system", WEB, note="one HTTP boundary · one artifact contract")
    MW, SW, SX = 700, 340, 812
    cx = X + MW / 2

    c.add(box(X, 478, W, 42, WEB, "Internal users · operations, research, technical staff",
              title_size=15, centered=True))
    c.add(arrow([(cx, 522), (cx, 536)], WEB))

    c.add(box(X, 540, MW, 104, WEB, "Django Web Layer", tag="web orchestration", lines=[
        "Configuration, authentication, request submission",
        "Metadata persistence and result visualization",
    ], title_size=19, line_size=13))
    c.add(box(SX, 540, SW, 104, STORE, "Relational Database", tag="metadata", lines=[
        "Users, projects, permissions",
        "Dataset and class configuration",
    ], title_size=17, line_size=12.5))
    c.add(arrow([(X + MW + 2, 592), (SX - 2, 592)], STORE))

    c.add(arrow([(cx, 646), (cx, 662)], API, label="HTTP / REST", label_dy=-6))
    c.add(box(X, 666, MW, 104, API, "FastAPI AI Service", tag="ai service boundary", lines=[
        "Validation, training orchestration, inference dispatch",
        "Artifact generation and error propagation",
    ], title_size=19, line_size=13))
    c.add(box(SX, 666, SW, 104, TRACK, "Experiment Tracking", tag="clearml", lines=[
        "Run metadata, metrics, lineage",
        "Not a transactional registry",
    ], title_size=17, line_size=12.5))
    c.add(arrow([(X + MW + 2, 718), (SX - 2, 718)], TRACK))

    c.add(arrow([(cx, 772), (cx, 788)], GPU))
    c.add(band(X, 792, MW, 136, "GPU compute runtime", GPU))
    for i, (t, ls) in enumerate([
        ("YOLO Training", ["Multi-seed runs", "Validation-based pick"]),
        ("CI Training", ["Baseline comparison", "Conditional promotion"]),
        ("SAHI Inference", ["Tiling and merge", "Small-object recall"]),
    ]):
        c.add(box(104 + i * 226, 832, 214, 82, GPU, t, lines=ls,
                  title_size=14, line_size=11.5))
    c.add(box(SX, 792, SW, 136, FAINT, "Explicit non-goals", tag="scoped out", dashed=True,
              lines=["No job queue or workers", "No GPU scheduler",
                     "No Kubernetes", "Added on evidence only"],
              title_size=17, line_size=12.5))

    c.add(arrow([(cx, 930), (cx, 944)], STORE))
    c.add(box(X, 948, W, 62, STORE, "Shared Artifact Storage", lines=[
        "models · training_runs · inference_runs · reports — "
        "checkpoints, selected model reference, summaries, previews, manifests",
    ], title_size=17, line_size=12.5))

    # -- seccion B · los tres flujos --------------------------------------
    section(c, 1062, "Three execution flows", API)
    flows = [
        (GPU, "Training", [
            "1  Django validates and submits",
            "2  FastAPI resolves the dataset",
            "3  GPU trains 3-5 seeds",
            "4  Best run picked by validation",
            "5  Checkpoint and reference written",
            "6  Django exposes the summary",
        ]),
        (API, "Continuous improvement", [
            "1  New data or configuration arrives",
            "2  Previous baseline is resolved",
            "3  Incremental fine-tuning runs",
            "4  New metrics meet the baseline",
            "5  Reference moves only on gain",
            "6  Every run is recorded either way",
        ]),
        (TRACK, "SAHI inference", [
            "1  High-resolution frame arrives",
            "2  Sliced into overlapping tiles",
            "3  YOLO runs on every tile",
            "4  Boxes mapped back to the frame",
            "5  NMS removes overlap duplicates",
            "6  Manifest and preview persisted",
        ]),
    ]
    outcomes = ["Model ready for review",
                "Production model protected",
                "Small objects recovered"]
    for i, (col, t, ls) in enumerate(flows):
        x = X + i * 362
        c.add(box(x, 1088, 340, 212, col, t, lines=ls, title_size=19, line_size=13))
        c.add(line(x + 18, 1256, x + 322, 1256, STROKE_SOFT, 1))
        c.add(text(x + 18, 1280, outcomes[i], 13.5, col, family=BODY, weight=700))

    # -- seccion C · decisiones -------------------------------------------
    section(c, 1352, "Decisions that define the system", TRACK)
    decisions = [
        (WEB, "Separated services", "GPU work never runs inside the web process, "
                                    "so a long training job cannot take the site down."),
        (API, "Synchronous on purpose", "A queue is real complexity. It is deferred until "
                                        "timeouts or GPU contention actually appear."),
        (STORE, "Storage as a contract", "Shared volumes are practical and coupling. "
                                         "Path validation and manifests are the price."),
        (GPU, "Runtime is not a platform", "Multi-GPU DataParallel and DDP are training "
                                           "runtime. Neither makes this a distributed system."),
    ]
    for i, (col, t, bodytxt) in enumerate(decisions):
        x = X + i * 270
        c.add(box(x, 1378, 254, 152, col, t, title_size=15.5))
        words, cur, out = bodytxt.split(), "", []
        for wd in words:
            if len(cur) + len(wd) + 1 > 30:
                out.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        out.append(cur)
        for j, ln in enumerate(out):
            c.add(text(x + 18, 1442 + j * 19, ln, 12.5, DIM, family=BODY))

    # -- seccion D · evolucion --------------------------------------------
    section(c, 1572, "Evolution path", GPU, note="each stage waits for its trigger")
    stages = [
        (GPU, "Priority 1", "Reliability", "preflight checks, job status, structured logs"),
        (API, "Priority 2", "Background exec", "only once timeouts or contention are routine"),
        (TRACK, "Priority 3", "Governance", "model reference and dataset versions in the DB"),
        (FAINT, "Optional", "Scale-out", "queue pool, object storage, orchestrator"),
    ]
    for i, (col, tag_, t, note) in enumerate(stages):
        x = X + i * 270
        c.add(rect(x, 1598, 254, 84, PANEL, STROKE, rx=10,
                   dashed=(col is FAINT)))
        c.add(rect(x, 1598, 4, 84, col, rx=2))
        c.add(text(x + 18, 1620, tag_.upper(), 10, col, family=BODY, weight=700, spacing=1.3))
        c.add(text(x + 18, 1642, t, 15, TEXT, family=DISPLAY, weight=600))
        words, cur, out = note.split(), "", []
        for wd in words:
            if len(cur) + len(wd) + 1 > 32:
                out.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        out.append(cur)
        for j, ln in enumerate(out[:2]):
            c.add(text(x + 18, 1660 + j * 15, ln, 11, FAINT, family=BODY))

    # -- pie ---------------------------------------------------------------
    c.add(line(X, 1706, X + W, 1706, STROKE_SOFT, 1))
    c.add(text(X, 1728, "github.com/maaferna/" + REPO, 12, FAINT, family=MONO))
    c.add(text(X + W, 1728, "Public-safe · no code, datasets, weights, credentials or "
                            "real metrics · all values illustrative", 12, FAINT,
               family=BODY, anchor="end"))
    return c.render()


# --------------------------------------------------------------------------
# Registro y punto de entrada
# --------------------------------------------------------------------------

DIAGRAMS = [
    ("diagrams", "01-system-architecture", diagram_system_architecture),
    ("diagrams", "02-training-flow", diagram_training_flow),
    ("diagrams", "03-ci-training-flow", diagram_ci_training),
    ("diagrams", "04-sahi-inference", diagram_sahi_inference),
    ("diagrams", "05-deployment-strategy", diagram_deployment_strategy),
    ("diagrams", "06-synthetic-dataset", diagram_synthetic_dataset),
    ("diagrams", "07-evolution-roadmap", diagram_evolution_roadmap),
    ("poster", "poster-architecture", poster_architecture),
]


def main() -> int:
    out_root = sys.argv[1] if len(sys.argv) > 1 else "assets/src"
    os.makedirs(out_root, exist_ok=True)
    for _group, name, fn in DIAGRAMS:
        path = os.path.join(out_root, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print(f"  svg  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
