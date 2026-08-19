# Assets Directory

Generated visual material for the architecture documentation.

## Contents

```text
assets/
├── src/         SVG sources — build products of scripts/build_visuals.py
├── diagrams/    Diagram PNGs, 3200 × 2000 (2x for high-density screens)
└── poster/      One-page poster PNG, 2480 × 3508 (A2 at 150 dpi)
```

| File | Subject |
|---|---|
| `diagrams/01-system-architecture.png` | Layer separation and service boundaries |
| `diagrams/02-training-flow.png` | Training request from submission to selected model |
| `diagrams/03-ci-training-flow.png` | Conditional model promotion |
| `diagrams/04-sahi-inference.png` | Tiled inference for small-object detection |
| `diagrams/05-deployment-strategy.png` | Local, cloud and hybrid deployment trade-offs |
| `diagrams/06-synthetic-dataset.png` | Synthetic dataset generation pipeline |
| `diagrams/07-evolution-roadmap.png` | Evolution priorities and their triggers |
| `poster/poster-architecture.png` | One-page architecture poster |

## Regenerating

Nothing in `src/`, `diagrams/` or `poster/` should be edited by hand — every file is regenerated
from `scripts/build_visuals.py` and any manual change is lost on the next build.

```bash
./scripts/render-visuals.sh            # everything
./scripts/render-visuals.sh 04         # only what matches "04"
```

Requires `python3` and `rsvg-convert` (`librsvg2-tools` on Fedora, `librsvg2-bin` on Debian/Ubuntu).
The design system — palette, typography, grid, arrow and composition rules — is documented in
`.claude/skills/diagram-studio/references/design-system.md`.

## Public-safety

These diagrams follow the same rules as the documentation: no real paths, credentials, client
names, infrastructure identifiers or measured metrics. Every numeric value shown is illustrative
and each canvas carries that notice in its footer.

See `../docs/architecture/16-public-release-sanitization.md` for the complete policy.
