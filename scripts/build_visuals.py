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


def _wrap(txt: str, width: int) -> list[str]:
    """Corte de palabras a un ancho maximo en caracteres."""
    words, cur, out = txt.split(), "", []
    for wd in words:
        if len(cur) + len(wd) + 1 > width:
            out.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    out.append(cur)
    return out


def diagram_evolution_roadmap() -> str:
    c = Canvas(1600, 1000,
               title="Production Evolution Roadmap",
               subtitle="Every stage names the evidence that justifies it. In a later revision "
                        "the triggers fired, and the answer was not a queue: job records, polling, "
                        "a registry, contracts and tests.",
               kicker="Scale by evidence, not by default · outcome per stage")
    c.header()

    BOX_Y, BOX_H = 222, 360
    BOT = BOX_Y + BOX_H

    c.add(box(100, BOX_Y, 280, BOX_H, WEB, "Initial iteration", tag="starting point", lines=[
        "Django web layer",
        "FastAPI AI service",
        "Synchronous HTTP boundary",
        "Shared artifact storage",
        "GPU-backed training runtime",
        "Experiment tracking and manifests",
        "Docker Compose on a single node",
        "Ubuntu GPU runtime baseline",
    ], title_size=18, line_size=13))
    c.add(line(118, BOT - 94, 362, BOT - 94, STROKE_SOFT, 1))
    c.add(chip(118, BOT - 82, "discarded · tracker only", WEB))
    for j, ln in enumerate(_wrap("Tracker withdrawn (ADR-012). Services, boundary, "
                                 "storage and Compose all kept.", 40)):
        c.add(text(118, BOT - 48 + j * 17, ln, 11.5, FAINT, family=BODY))

    stages = [
        (GPU, "Priority 1", "Operational reliability", [
            "Preflight checks: dataset,",
            "checkpoint, storage, GPU",
            "Explicit job status records",
            "Structured logs, correlation IDs",
            "Artifact manifest per run",
        ], "Do this first. It costs little and removes most silent failures.",
         "realised",
         "Job records, manifests, backups; preflight became validation at submit."),
        (API, "Priority 2", "Background execution", [
            "Lightweight queue",
            "Single GPU worker",
            "Job status polling",
            "Retry policy, GPU locking",
        ], "Trigger: repeated timeouts, jobs competing for the GPU, cancellation needed.",
         "realised differently",
         "Submit/poll on in-process pools, not a queue. GPU admission is the open trigger."),
        (TRACK, "Priority 3", "Artifact governance", [
            "Model reference in the database",
            "Dataset version registry",
            "Immutable run identifiers",
            "Retention policy for outputs",
        ], "Trigger: lineage questions become hard to answer from storage alone.",
         "realised",
         "Transactional registry, human promotion; retention as a batch cascade."),
        (FAINT, "Optional", "Scale-out", [
            "GPU worker pool",
            "Object storage",
            "Kubernetes or equivalent",
            "Centralized monitoring",
        ], "Trigger: concurrent long-running jobs, storage beyond local capacity, "
           "uptime becomes business-critical.",
         "not triggered",
         "One host, one device. Compose overlays; no broker, no Kubernetes."),
    ]
    for i, (col, tag_, title_, ls, trig, outcome, note) in enumerate(stages):
        x = 420 + i * 286
        c.add(box(x, BOX_Y, 264, BOX_H, col, title_, tag=tag_, lines=ls,
                  title_size=16, line_size=12.5, dashed=(col is FAINT)))
        # resultado en la revision posterior: pastilla + nota, anclados al pie de la caja
        note_lines = _wrap(note, 36)
        ny = BOT - 16 - (len(note_lines) - 1) * 17
        for ln in note_lines:
            c.add(text(x + 18, ny, ln, 11.5, DIM, family=BODY))
            ny += 17
        chip_y = BOT - 16 - len(note_lines) * 17 - 30
        c.add(chip(x + 18, chip_y, outcome, col))
        c.add(line(x + 18, chip_y - 12, x + 246, chip_y - 12, STROKE_SOFT, 1))
        # disparador declarado en la iteracion inicial, encima del resultado
        trig_lines = _wrap(trig, 34)
        ty = chip_y - 12 - 14 - (len(trig_lines) - 1) * 17
        c.add(line(x + 18, ty - 22, x + 246, ty - 22, STROKE_SOFT, 1))
        for ln in trig_lines:
            c.add(text(x + 18, ty, ln, 11.5, FAINT, family=BODY))
            ty += 17
        if i < 3:
            c.add(arrow([(x + 266, 385), (x + 282, 385)], stages[i + 1][0]))
    c.add(arrow([(382, 385), (416, 385)], GPU))

    # -- cuando no anadir infraestructura ---------------------------------
    c.add(band(100, 622, 1444, 130, "When not to add distributed infrastructure", WARN))
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
        c.add(text(132 + col_ * 480, 676 + row_ * 34, "✕", 13, WARN, family=BODY))
        c.add(text(154 + col_ * 480, 676 + row_ * 34, txt_, 13.5, DIM, family=BODY))

    c.add(box(100, 792, 1444, 64, WEB,
              "Reliability, traceability and artifact governance return more, at this scale, "
              "than any distributed component added ahead of the evidence for it.",
              title_size=15, centered=True))
    c.add(legend(100, 900, [
        (GPU, "Realised"), (API, "Realised differently"), (FAINT, "Not triggered"),
        (WEB, "Discarded (tracker only)"),
    ]))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 08 · Ciclo de vida submit/poll (revision posterior)
# --------------------------------------------------------------------------


def diagram_submit_poll_lifecycle() -> str:
    c = Canvas(1600, 1000,
               title="Submit/Poll Execution Lifecycle",
               subtitle="The request returns a run identifier in milliseconds; the job runs on an "
                        "in-process pool and the console polls. No queue, no broker, no second "
                        "process.",
               kicker="Later revision · ADR-009 amends the synchronous boundary")
    c.header()

    COL = [240, 460, 680, 900, 1120, 1340]
    BW = 200

    lane(c, 196, 80, "Web database | web layer", STORE)
    lane(c, 292, 136, "Console | web layer", WEB)
    lane(c, 456, 160, "AI service | fastapi · feature pools", API)
    lane(c, 640, 120, "Shared volume | records · outputs", STORE)

    # -- base de datos web -------------------------------------------------
    c.add(box(COL[0], 204, 860, 64, STORE, "Job-history table", lines=[
        "One row per submit, inserted before the HTTP call; status written back on every "
        "poll · the operator's source of truth",
    ], title_size=16, line_size=12.5))

    # -- consola -----------------------------------------------------------
    c.add(box(COL[0], 300, BW, 120, WEB, "Insert history row", tag="step 1", lines=[
        "status = submitted",
        "Before the HTTP call, so a lost",
        "request still leaves a trace",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[2], 300, BW, 120, WEB, "Receive 202", tag="step 3", lines=[
        "{ run_id } in milliseconds",
        "The request no longer waits",
        "for the job to finish",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[3], 300, BW, 120, WEB, "Poll status", tag="step 4", lines=[
        "Batched query, many run_ids",
        "Every few seconds",
        "Status written to history row",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[5], 300, BW, 120, WEB, "Read outputs", tag="step 6", lines=[
        "Straight from the shared",
        "volume; only what the",
        "manifest lists is rendered",
    ], title_size=16, line_size=12.5))

    # -- servicio de IA ----------------------------------------------------
    c.add(box(COL[1], 464, BW, 144, API, "Validate and record", tag="step 2", lines=[
        "Validate inputs synchronously",
        "Create run_id",
        "Write one job record (atomic)",
        "Hand to the feature pool",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[3], 464, BW, 144, API, "Answer status query", tag="step 4", lines=[
        "Read the job records",
        "{ run_id: status, ... }",
        "One request, many run_ids",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[4], 464, BW, 144, API, "Run on a pool thread", tag="step 5", lines=[
        "After the response, in-process",
        "Write manifest + outputs (atomic)",
        "Job record → done | failed",
        "!Admission is not controlled",
    ], title_size=16, line_size=12.5))

    # -- volumen compartido -----------------------------------------------
    c.add(box(COL[1], 648, 640, 104, STORE, "Job record", lines=[
        "`jobs/<feature>/<run_id>.json`",
        "Created exclusively, updated by temp file + rename · the AI service's only state",
        "Startup reconciliation: anything still running is swept to failed; nothing resumes",
    ], title_size=16, line_size=12.5))
    c.add(box(COL[4], 648, BW, 104, STORE, "Run outputs", lines=[
        "`<run_id>/manifest.json`",
        "+ outputs/, written atomically",
        "Only listed files are shown",
    ], title_size=16, line_size=12.5))

    # -- transiciones ------------------------------------------------------
    c.add(arrow([(340, 298), (340, 270)], STORE,
                label="insert", label_dx=40, label_dy=4))
    c.add(arrow([(1000, 298), (1000, 270)], STORE, dashed=True,
                label="status on every poll", label_dx=92, label_dy=4))
    c.add(arrow([(442, 352), (560, 352), (560, 462)], API,
                label="POST /<feature>/submit", label_dx=12))
    c.add(arrow([(640, 462), (640, 442), (780, 442), (780, 422)], WEB,
                label="202 · run_id"))
    c.add(arrow([(882, 352), (898, 352)], WEB))
    c.add(arrow([(960, 422), (960, 462)], API,
                label="status { run_ids }", label_dx=-40, label_dy=5))
    c.add(arrow([(1050, 462), (1050, 422)], WEB, dashed=True,
                label="{ run_id: status, ... }", label_dx=56, label_dy=5))
    c.add(arrow([(560, 610), (560, 646)], STORE,
                label="write · atomic", label_dy=4))
    c.add(arrow([(960, 610), (960, 646)], STORE, dashed=True,
                label="read", label_dy=4))
    c.add(arrow([(1150, 610), (1150, 630), (1080, 630), (1080, 646)], STORE, dashed=True))
    c.add(arrow([(1240, 610), (1240, 646)], STORE,
                label="write · atomic", label_dy=4))
    c.add(arrow([(1322, 700), (1440, 700), (1440, 422)], WEB,
                label="outputs from the volume", label_at=0.5))

    # -- lo que no se ofrece y el riesgo abierto ---------------------------
    c.add(box(56, 790, 700, 112, FAINT, "Not provided", tag="what this is not",
              dashed=True, lines=[
                  "Retry: a person re-submits after reading the failure reason",
                  "Cancellation and resume after restart: not triggered; running jobs are "
                  "swept to failed",
                  "A broker or a second worker process: one device, nothing to dispatch across",
              ], title_size=16, line_size=12.5))
    c.add(box(780, 790, 764, 112, WARN, "Open risk · admission is not controlled",
              tag="next trigger", lines=[
                  "One pool per feature admits several jobs at once; two that need the device "
                  "compete for its memory.",
                  "Recommendation: a single GPU admission lane before a second device job type "
                  "is enabled.",
              ], title_size=16, line_size=12.5))

    c.add(legend(56, 934, [
        (WEB, "Console · web layer"), (API, "AI service · in-process pools"),
        (STORE, "Job records, history table, outputs"), (WARN, "Open risk"),
    ]))
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
        (TRACK, "Run manifests"), (STORE, "PostgreSQL"), (DATA, "Docker Compose"),
        (DATA, "Ubuntu"),
    ], gap=6)

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
    c.add(box(SX, 666, SW, 104, TRACK, "Experiment Tracking", tag="tracker · metadata only", lines=[
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
        (API, "Synchronous on purpose", "The queue stayed deferred. When timeouts arrived, "
                                        "the later revision answered with submit/poll on "
                                        "in-process pools."),
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
    section(c, 1572, "Evolution path", GPU,
            note="the triggers fired in a later revision · the answer was not a queue")
    stages = [
        (GPU, "Priority 1", "Reliability", "preflight checks, job status, structured logs",
         "realised"),
        (API, "Priority 2", "Background exec", "only once timeouts or contention are routine",
         "realised differently · no queue"),
        (TRACK, "Priority 3", "Governance", "model reference and dataset versions in the DB",
         "realised"),
        (FAINT, "Optional", "Scale-out", "queue pool, object storage, orchestrator",
         "not triggered"),
    ]
    for i, (col, tag_, t, note, outcome) in enumerate(stages):
        x = X + i * 270
        c.add(rect(x, 1598, 254, 100, PANEL, STROKE, rx=10,
                   dashed=(col is FAINT)))
        c.add(rect(x, 1598, 4, 100, col, rx=2))
        c.add(text(x + 18, 1620, tag_.upper(), 10, col, family=BODY, weight=700, spacing=1.3))
        c.add(text(x + 18, 1642, t, 15, TEXT, family=DISPLAY, weight=600))
        for j, ln in enumerate(_wrap(note, 32)[:2]):
            c.add(text(x + 18, 1660 + j * 15, ln, 11, FAINT, family=BODY))
        c.add(text(x + 18, 1690, outcome.upper(), 10, col, family=BODY, weight=700,
                   spacing=1.3))

    # -- pie ---------------------------------------------------------------
    c.add(line(X, 1714, X + W, 1714, STROKE_SOFT, 1))
    c.add(text(X, 1734, "github.com/maaferna/" + REPO, 12, FAINT, family=MONO))
    c.add(text(X + W, 1734, "Public-safe · no code, datasets, weights, credentials or "
                            "real metrics · all values illustrative", 12, FAINT,
               family=BODY, anchor="end"))
    return c.render()


# --------------------------------------------------------------------------
# 09 · Registro de modelos y promocion (revision posterior)
# --------------------------------------------------------------------------


def diagram_model_registry() -> str:
    c = Canvas(1600, 1000,
               title="Model Registry and Promotion",
               subtitle="The model reference stops being a file any training run could rewrite. "
                        "It becomes a version row with a fingerprint, a stage and a promotion "
                        "event that names who decided and why.",
               kicker="Later revision · ADR-010 · two records, one transaction")
    c.header()

    # -- ciclo de vida de una version -------------------------------------
    c.add(band(100, 200, 760, 350, "Model version lifecycle · stage state machine", STORE))

    c.add(box(116, 244, 220, 128, WEB, "Import weights", tag="side entry", lines=[
        "Weights trained outside",
        "Fingerprint on arrival",
        "Family, size, resolution",
        "Registered as candidate",
    ], title_size=16, line_size=12.5))

    SY, SH, SW = 262, 60, 130
    c.add(box(372, SY, SW, SH, STORE, "candidate", title_size=16, centered=True))
    c.add(box(540, SY, SW, SH, STORE, "serving", title_size=16, centered=True, fill=PANEL2))
    c.add(box(708, SY, SW, SH, STORE, "retired", title_size=16, centered=True, dashed=True))

    c.add(arrow([(338, 292), (370, 292)], STORE))
    c.add(arrow([(504, 292), (538, 292)], STORE, label="promote", label_dy=-40))
    c.add(arrow([(672, 292), (706, 292)], STORE, label="demoted", label_dy=-40))
    c.add(arrow([(605, 324), (605, 356), (437, 356), (437, 324)], STORE, dashed=True,
                label="rollback · same transaction, kind = rollback", label_dy=16))

    c.add(box(116, 396, 728, 138, STORE,
              "One transaction, one event, promotion is a human act", tag="the rule",
              lines=_wrap("Promoting a version demotes the previous serving version and "
                          "writes the promotion event inside a single database transaction; "
                          "rollback is the same operation with the roles reversed.", 100)
              + _wrap("The selection score is computed and shown, never acted on. There is "
                      "no state in which two versions are serving, or none.", 100),
              title_size=16, line_size=12.5))

    # -- los dos registros -------------------------------------------------
    c.add(box(890, 200, 315, 236, STORE, "Model version", tag="record · web database", lines=[
        "name + version · unique together",
        "weights fingerprint · SHA-256",
        "stage · candidate | serving | retired",
        "family · size · input resolution",
        "dataset configuration reference",
        "tracking run id · optional",
        "immutable once registered",
    ], title_size=17, line_size=12.5))
    c.add(box(1229, 200, 315, 236, STORE, "Promotion event", tag="record · web database", lines=[
        "model version promoted",
        "previous serving version · nullable",
        "decided by · user",
        "reason · free text, required",
        "kind · promote | rollback",
        "written inside the transaction",
    ], title_size=17, line_size=12.5))

    c.add(box(890, 456, 654, 94, WARN,
              "Closes the file-reference race of the initial iteration (doc 10)",
              lines=_wrap("No shared mutable reference is left to race for: no lock was "
                          "added, the thing two runs used to rewrite no longer decides "
                          "anything.", 92),
              title_size=15, line_size=12.5))

    # -- como llega al servicio de IA -------------------------------------
    c.add(band(100, 590, 1444, 230, "How the registry reaches the AI service", API,
               note="the AI service holds no database · a file it can trust"))
    c.add(box(116, 634, 420, 160, WEB, "Registry in the web database",
              tag="web layer · source of truth", lines=[
                  "Version rows and promotion event rows",
                  "Export triggered by the promotion itself",
                  "Hashes at registration and at export",
                  "Small window between promotion and export",
              ], title_size=16, line_size=12.5))
    c.add(box(580, 634, 420, 160, TRACK, "Exported serving list",
              tag="artifact on the shared volume", lines=[
                  "`models/serving.json`",
                  "identifier · path under the volume",
                  "fingerprint · input resolution",
                  "The only list the AI service may load from",
              ], title_size=16, line_size=12.5))
    c.add(box(1044, 634, 484, 160, API, "AI service resolver",
              tag="ai service · no database", lines=[
                  "Resolves a model only through the list",
                  "Verifies the fingerprint; a mismatch is refused",
                  "Refuses unknown paths and directory walks",
                  "Fingerprint actually used goes into the run manifest",
              ], title_size=16, line_size=12.5))
    c.add(arrow([(538, 714), (578, 714)], TRACK, label="export", label_dy=-9))
    c.add(arrow([(1002, 714), (1042, 714)], API, label="read", label_dy=-9))

    c.add(box(100, 846, 1444, 60, STORE,
              "One serving version per model name · the registry is a web-layer concern · "
              "the validation summary stored with a version is provenance, not a benchmark",
              title_size=14, centered=True))

    c.add(legend(100, 938, [
        (STORE, "Records · web database"), (WEB, "Web layer"),
        (TRACK, "Exported artifact"), (API, "AI service"),
        (WARN, "Race condition closed"),
    ]))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 10 · Metrologia de detecciones (revision posterior)
# --------------------------------------------------------------------------


def diagram_detection_metrology() -> str:
    c = Canvas(1600, 1000,
               title="Detection Metrology",
               subtitle="From pixel boxes to physical quantities, using only the detections and "
                        "the image metadata. Every quantity says whether it was measured, "
                        "estimated or withheld.",
               kicker="Later revision · ADR-013 · a CPU job type of the AI service")
    c.header()

    # -- entradas ----------------------------------------------------------
    c.add(box(100, 200, 460, 78, DATA, "Image metadata", tag="input", lines=[
        "Height above ground · focal length · sensor size",
    ], title_size=16, line_size=12.5))
    c.add(box(590, 200, 954, 78, DATA, "Detections in pixel coordinates", tag="input", lines=[
        "Boxes per DetectionClass in the original image frame · sliced inference is "
        "reconstructed to full-image coordinates first",
    ], title_size=16, line_size=12.5))

    # -- las seis etapas ---------------------------------------------------
    stages = [
        (DATA, "Scale", ["Height above ground,", "focal length, sensor width",
                         "→ ground sampling distance", "(physical length per pixel)"]),
        (DATA, "Size", ["Box width, height × GSD", "→ physical size per",
                        "DetectionClass instance", "Per image: count, distribution"]),
        (TRACK, "Foci", ["Density-based clustering", "of detection centres",
                         "→ clusters with extent,", "member count, centroid"]),
        (TRACK, "Coverage", ["Grid over the image footprint", "→ occupied cells,",
                             "occupancy fraction,", "per-cell counts"]),
        (TRACK, "Density", ["Count per unit area,", "per image and per batch",
                            "→ only where the footprint", "is known"]),
        (API, "Gates", ["Uncertainty checks that", "refuse to extrapolate",
                        "→ every quantity carries", "a status and its reason"]),
    ]
    STAGE_Y, STAGE_H, STAGE_W, STEP = 316, 176, 218, 245
    for i, (col, title_, ls) in enumerate(stages):
        x = 100 + i * STEP
        c.add(box(x, STAGE_Y, STAGE_W, STAGE_H, col, title_, tag=f"stage {i + 1}", lines=ls,
                  title_size=16, line_size=12))
        if i < 5:
            c.add(arrow([(x + STAGE_W + 2, STAGE_Y + 88), (x + STEP - 2, STAGE_Y + 88)],
                        stages[i + 1][0]))

    c.add(arrow([(209, 278), (209, 314)], DATA, label="scale inputs", label_dx=52, label_dy=4))
    c.add(arrow([(700, 278), (700, 298), (454, 298), (454, 314)], DATA))

    # -- nivel sin escala y estados ----------------------------------------
    c.add(arrow([(209, 492), (209, 546)], DIM, dashed=True,
                label="metadata missing", label_dx=64, label_dy=4))
    c.add(box(100, 548, 464, 100, DIM, "Scale-free tier", tag="no typical value is assumed",
              dashed=True, lines=_wrap("Counts, relative sizes and clustering are still "
                                       "produced; physical sizes and densities are withheld "
                                       "and marked as such.", 64),
              title_size=16, line_size=12.5))

    c.add(band(590, 548, 710, 100, "Status carried by every quantity", API))
    states = [
        (GPU, "measured", "every input it depends on was present"),
        (API, "estimated", "a documented fallback was used"),
        (FAINT, "withheld", "not supported; the reason is recorded"),
    ]
    for i, (col, name, note) in enumerate(states):
        x = 606 + i * 230
        c.add(chip(x, 588, name, col))
        c.add(text(x, 626, note, 11.5, DIM, family=BODY))

    # -- salidas -----------------------------------------------------------
    c.add(arrow([(1434, 492), (1434, 674)], STORE, label="outputs", label_dx=36, label_dy=4))
    outs = [
        ("Per-image and per-batch tables", ["Sizes, foci, coverage, density; each value",
                                            "with its status, so a reader can filter"]),
        ("GeoJSON per batch", ["Detections and foci with physical attributes;",
                               "rendered on the console map (doc 05)"]),
        ("Manifest entries", ["Detection run consumed, parameters, gate outcomes;",
                              "clustering is deterministic and replayable"]),
    ]
    for i, (title_, ls) in enumerate(outs):
        c.add(box(100 + i * 490, 676, 464, 92, STORE, title_, lines=ls,
                  title_size=16, line_size=12.5))

    # -- donde corre y lo que falta ---------------------------------------
    c.add(box(100, 796, 900, 114, API, "Runs as a CPU job type of the AI service",
              tag="adr-013 · placement", lines=[
                  "Submitted, tracked and manifested like inference; reads a batch's detections "
                  "from the shared volume and writes beside them",
                  "Own CPU pool, never touches the device; the web layer renders what the "
                  "manifest lists and computes nothing",
              ], title_size=16, line_size=12.5))
    c.add(box(1024, 796, 520, 114, WARN, "Ground-truth validation pending",
              tag="open item", lines=[
                  "No field measurement has confirmed the sizes or densities",
                  "reported: every value is computed, with a documented",
                  "derivation, and the repository says so",
              ], title_size=16, line_size=12.5))

    c.add(legend(100, 938, [
        (DATA, "Inputs and scale"), (TRACK, "Spatial statistics"), (API, "AI service · gates"),
        (STORE, "Output artifacts"), (WARN, "Open item"),
    ]))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# 11 · Pruebas y CI sin GPU (revision posterior)
# --------------------------------------------------------------------------


def diagram_testing_ci() -> str:
    c = Canvas(1600, 1000,
               title="Testing and CI Without a GPU",
               subtitle="A runtime seam with a deterministic mock, wire-level contracts between "
                        "the two services and a throwaway Compose stack make the platform "
                        "reviewable on any machine.",
               kicker="Later revision · what is tested, and what deliberately is not")
    c.header()

    # -- costura de runtime ------------------------------------------------
    c.add(band(100, 200, 700, 560, "The runtime seam", API))
    c.add(box(116, 244, 668, 64, API, "Feature code", centered=True, title_size=16, lines=[
        "inference · sliced inference · validation · training · metrology",
    ], line_size=12.5))
    c.add(arrow([(450, 310), (450, 334)], API))
    c.add(box(116, 336, 668, 64, API, "Runtime protocol", centered=True, title_size=16, lines=[
        "`load(model_ref) · predict(image, params) · train(config) · device()`",
    ], line_size=12.5))
    c.add(arrow([(450, 402), (450, 416), (277, 416), (277, 428)], DATA))
    c.add(arrow([(450, 402), (450, 416), (623, 416), (623, 428)], GPU))
    c.add(box(116, 430, 322, 136, DATA, "Mock runtime", tag="tests · ci", lines=[
        "Deterministic boxes from image size",
        "and parameters; no weights, no device",
        "Health endpoint and every manifest",
        "record which runtime produced a result",
    ], title_size=16, line_size=12.5))
    c.add(box(462, 430, 322, 136, GPU, "Real runtime", tag="deployment", lines=[
        "The deep-learning library",
        "Device injected from configuration,",
        "never probed by the code",
        "CPU fallback when none is configured",
    ], title_size=16, line_size=12.5))

    c.add(text(116, 592, "SUITES", 11, API, family=BODY, weight=700, spacing=1.4))
    c.add(text(784, 592, "CPU only · on the order of two thousand tests · minutes",
               11.5, FAINT, family=BODY, anchor="end"))
    suites = [
        ("Unit", "coordinate reconstruction, naming, manifests, registry transactions, "
                 "metrology stages"),
        ("Contract, wire level", "client and routes agree on every payload and error envelope, "
                                 "over real HTTP with the mock"),
        ("Purity and fences", "no framework in the service client, no database driver in the "
                              "AI service, no cross-imports"),
        ("Document guards", "Compose chain consistent, README claims true, every error code "
                            "in the catalogue"),
        ("Console", "every view renders, every string is translated, permissions hold per group"),
        ("Mutation-checked subsets", "coordinate and registry code: the tests fail when the "
                                     "logic is broken"),
    ]
    for i, (name, what) in enumerate(suites):
        y = 618 + i * 23
        c.add(text(116, y, name, 12.5, TEXT, family=BODY, weight=700))
        c.add(text(300, y, what, 12, DIM, family=BODY))

    # -- integracion continua ----------------------------------------------
    c.add(band(830, 200, 714, 560, "Continuous integration", GPU,
               note="advisory, not yet blocking"))
    steps = [
        (WEB, "push", "any branch, every commit"),
        (WEB, "lint", "style and static checks"),
        (WEB, "compose-chain guard", "the Compose file chain is consistent"),
        (GPU, "build both images", "web and AI, from the checkout"),
        (GPU, "throwaway Compose project", "own name, own volumes, mock runtime"),
        (GPU, "both suites in containers", "the image that would ship, not a dev tree"),
        (STORE, "tear down", "delete the volumes; nothing shared with a local stack"),
    ]
    for i, (col, title_, note) in enumerate(steps):
        y = 244 + i * 72
        c.add(box(846, y, 380, 61, col, title_, lines=[note], title_size=14.5, line_size=11.5))
        if i < 6:
            c.add(arrow([(1036, y + 62), (1036, y + 71)], steps[i + 1][0]))

    notes = [
        (GPU, "Same definitions as a deployment",
         "The CI job uses the same Compose files as a deployment, so what is tested is "
         "the image that would ship."),
        (STORE, "Nothing survives the run",
         "The project is named per run and its volumes are removed afterwards; no state "
         "leaks between runs or into a local stack."),
        (FAINT, "Advisory by decision",
         "It reports, it does not block merges. Branch protection is deferred until more "
         "than one person commits. The runner is self-managed and not described."),
    ]
    for i, (col, title_, body) in enumerate(notes):
        y = 244 + i * 172
        c.add(box(1250, y, 278, 152, col, title_, lines=_wrap(body, 36),
                  title_size=14.5, line_size=12, dashed=(col is FAINT)))

    # -- lo que deliberadamente no se prueba ------------------------------
    c.add(band(100, 800, 1444, 100, "Deliberately not tested", WARN,
               note="the boundary of the confidence is stated, not hidden"))
    nots = [
        "The real runtime on a device · no GPU in CI",
        "Model accuracy on real images · no images or weights",
        "SAHI border behaviour with real boxes · synthetic cases only",
        "The browser · views render, interactions are not scripted",
        "Metrology against ground truth · arithmetic only (doc 04)",
    ]
    for i, txt_ in enumerate(nots):
        col_, row_ = divmod(i, 2)
        x = 132 + col_ * 470
        y = 850 + row_ * 32
        c.add(text(x, y, "✕", 13, WARN, family=BODY))
        c.add(text(x + 22, y, txt_, 13, DIM, family=BODY))

    c.add(legend(100, 938, [
        (API, "Feature code and protocol"), (DATA, "Mock runtime"), (GPU, "Real runtime · CI build"),
        (WEB, "CI checks"), (STORE, "Tear down"), (WARN, "Not covered"),
    ]))
    c.footer()
    return c.render()


# --------------------------------------------------------------------------
# Poster · lo que vino despues (revision posterior)
# --------------------------------------------------------------------------


def poster_what_came_next() -> str:
    c = Canvas(1240, 1754, title="", pad=88)
    X, W = 88, 1064

    # -- cabecera ----------------------------------------------------------
    c.add(rect(0, 0, 1240, 400, "url(#glow)"))
    c.add(text(X, 104, "LATER REVISION · PUBLIC-SAFE DOCUMENTATION", 13, API,
               family=BODY, weight=700, spacing=2.2))
    c.add(text(X, 182, "What Came Next", 58, TEXT, family=DISPLAY, weight=800))
    c.add(text(X, 246, "Same Architecture, Triggers Fired", 58, TEXT, family=DISPLAY,
               weight=800))
    c.add(text(X, 292, "The initial iteration named its limitations and their triggers. "
                       "This is what a later revision did when they fired:", 16, DIM,
               family=BODY))
    c.add(text(X, 316, "no queue, no Kubernetes — records, a registry, contracts and tests.",
               16, DIM, family=BODY))
    chip_row(c, X, 342, W, [
        (WEB, "Django"), (API, "FastAPI"), (GPU, "PyTorch"), (GPU, "Ultralytics YOLO"),
        (GPU, "SAHI"), (STORE, "PostgreSQL"), (DATA, "Docker Compose"),
        (TRACK, "Run manifests"), (STORE, "Model registry"), (DATA, "GeoJSON"),
        (DATA, "Metrology"), (GPU, "CI without GPU"),
    ], gap=6)

    # -- seccion A · lo que se mantuvo ------------------------------------
    section(c, 452, "What stayed", WEB, note="every structural decision still holds")
    kept = [
        (WEB, "Separate services", ["Web layer and AI service,", "HTTP + JSON between them",
                                    "ADR-001"]),
        (STORE, "Shared storage", ["Artifacts as the integration", "mechanism; same path",
                                   "ADR-002 · ADR-011"]),
        (API, "FastAPI boundary", ["In front of the runtime;", "execution mode amended",
                                   "ADR-003 · ADR-009"]),
        (GPU, "SAHI", ["Small objects in large", "images: tiles, merge, NMS", "ADR-005"]),
        (FAINT, "No broker, no Kubernetes", ["Compose on one node; the", "web layer owns the DB",
                                             "doc 16 · doc 03"]),
    ]
    for i, (col, title_, ls) in enumerate(kept):
        x = X + i * 216
        c.add(box(x, 478, 200, 106, col, title_, title_size=13.5, dashed=(col is FAINT)))
        for j, ln in enumerate(ls):
            colour = FAINT if j == len(ls) - 1 else DIM
            c.add(text(x + 18, 534 + j * 16, ln, 11, colour, family=BODY))

    # -- seccion B · limitacion → resolucion ------------------------------
    section(c, 626, "Limitation → resolution", API,
            note="confessed in the initial iteration · answered in the revision")
    rows = [
        (API, "The HTTP request stays open for the whole job", "doc 15 · ADR-003",
         "Submit returns a run identifier; the job runs on an in-process pool; the console polls",
         "evolution 01 · ADR-009"),
        (STORE, "No job status records, no recovery after a restart", "doc 15 · doc 08",
         "Durable job record per run plus a job-history table; startup reconciliation",
         "evolution 01 · ADR-009"),
        (STORE, "File-based model reference with a race condition", "doc 10 · doc 07",
         "Transactional registry with promotion events; promotion is a human act",
         "evolution 02 · ADR-010"),
        (STORE, "Path translation across four coordinate systems", "doc 19 · ADR-008",
         "One mount path in both containers; the invariant is tested",
         "evolution 03 · ADR-011"),
        (WEB, "No service-to-service authentication", "doc 05",
         "Hashed service tokens and a service key; web sessions with groups and lockout",
         "evolution 03"),
        (API, "Error handling as prose that callers parse", "doc 14",
         "One error envelope with stable codes; a catalogue kept with the contract",
         "evolution 03"),
        (TRACK, "Tracking tool chosen for its SaaS convenience", "ADR-004 · ADR-007",
         "Tool withdrawn; a self-hosted, tracking-only alternative decided and not deployed",
         "ADR-012"),
        (GPU, "No automated tests, no continuous integration", "doc 15",
         "Mock/real runtime seam; about two thousand CPU tests; CI on a throwaway Compose stack",
         "evolution 06"),
    ]
    CW, CH, CG = 520, 104, 12
    for i, (col, lim, lim_ref, res, res_ref) in enumerate(rows):
        colidx, rowidx = divmod(i, 4)
        x = X + colidx * (CW + 24)
        y = 652 + rowidx * (CH + CG)
        c.add(rect(x, y, CW, CH, PANEL, STROKE, rx=10))
        c.add(rect(x, y, 4, CH, col, rx=2))
        c.add(text(x + 18, y + 22, "LIMITATION", 9.5, FAINT, family=BODY, weight=700,
                   spacing=1.3))
        for j, ln in enumerate(_wrap(lim, 34)[:3]):
            c.add(text(x + 18, y + 41 + j * 15, ln, 11.5, DIM, family=BODY))
        c.add(text(x + 18, y + 92, lim_ref, 10, FAINT, family=MONO))
        c.add(text(x + 258, y + 64, "→", 20, col, family=BODY, weight=700, anchor="middle"))
        c.add(text(x + 282, y + 22, "RESOLUTION", 9.5, col, family=BODY, weight=700,
                   spacing=1.3))
        for j, ln in enumerate(_wrap(res, 36)[:3]):
            c.add(text(x + 282, y + 41 + j * 15, ln, 11.5, TEXT, family=BODY))
        c.add(text(x + 282, y + 92, res_ref, 10, FAINT, family=MONO))

    # -- seccion C · capacidades nuevas -----------------------------------
    section(c, 1146, "New capabilities", DATA, note="what the initial iteration did not have")
    caps = [
        (DATA, "Detection metrology", [
            "Pixel boxes → physical size, foci,",
            "coverage and density; explicit gates:",
            "measured | estimated | withheld",
        ], "evolution 04 · ADR-013"),
        (WEB, "Operator console", [
            "GeoJSON per batch on an interactive",
            "map; a localisation guard on every",
            "string; permissions per group",
        ], "evolution 05"),
        (STORE, "Batch lifecycle", [
            "Batches own their runs and outputs;",
            "retention is a batch-level cascade,",
            "not a sweep of the volume",
        ], "evolution 01 · evolution 05"),
    ]
    for i, (col, title_, ls, ref) in enumerate(caps):
        x = X + i * 360
        c.add(box(x, 1172, 344, 122, col, title_, lines=ls, title_size=15, line_size=12))
        c.add(text(x + 18, 1282, ref, 10, FAINT, family=MONO))

    # -- seccion D · lo que la revision no hizo ---------------------------
    section(c, 1354, "What the revision did not do", WARN,
            note="a ledger that lists only wins is a brochure")
    c.add(band(X, 1372, W, 172, "Stated plainly", WARN))
    nots = [
        "Training stayed outside the platform; weights enter through an import step that "
        "fingerprints them (ADR-012 addendum)",
        "The GPU path was not validated: every test runs on CPU with a mock runtime, "
        "and the device is injected, never probed",
        "Admission on the device is not controlled — that is the next trigger, "
        "and a single admission lane is the recommendation",
        "No broker, no worker pool, no object storage, no Kubernetes — and that is the point",
        "Metrology is not validated against ground truth; every value is computed with a "
        "documented derivation",
        "CI is advisory and not yet blocking; branch protection waits for a second contributor",
    ]
    for i, txt_ in enumerate(nots):
        colidx, rowidx = divmod(i, 3)
        x = X + 32 + colidx * 528
        y = 1420 + rowidx * 40
        c.add(text(x, y, "✕", 12, WARN, family=BODY))
        for j, ln in enumerate(_wrap(txt_, 74)[:2]):
            c.add(text(x + 20, y + j * 15, ln, 11.5, DIM, family=BODY))

    c.add(box(X, 1580, W, 96, WEB, "The thesis of the roadmap held", tag="doc 16 · evolution 07",
              lines=[
                  "When the triggers fired, the answer was not a broker and not Kubernetes: "
                  "job records, polling, a registry, contracts and tests.",
                  "The one capability given up, in-platform training, is stated so that the "
                  "title of the repository stays honest.",
              ], title_size=16, line_size=12.5))

    # -- pie ---------------------------------------------------------------
    c.add(line(X, 1714, X + W, 1714, STROKE_SOFT, 1))
    c.add(text(X, 1734, "github.com/maaferna/" + REPO, 12, FAINT, family=MONO))
    c.add(text(X + W, 1734, "Public-safe · no code, datasets, weights, credentials or "
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
    ("diagrams", "08-submit-poll-lifecycle", diagram_submit_poll_lifecycle),
    ("poster", "poster-architecture", poster_architecture),
    # Revision posterior. Registrados despues del poster original para que los
    # identificadores de clipPath de los SVG ya publicados no cambien.
    ("diagrams", "09-model-registry-promotion", diagram_model_registry),
    ("diagrams", "10-detection-metrology", diagram_detection_metrology),
    ("diagrams", "11-testing-and-ci", diagram_testing_ci),
    ("poster", "poster-what-came-next", poster_what_came_next),
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
