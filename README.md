# Terp Spaces

[![CI](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml/badge.svg)](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml)

How busy is each University of Maryland building right now, and which classrooms are free?

Terp Spaces turns the Testudo class schedule (via [umd.io](https://api.umd.io)) and published building hours into an hourly estimate for every building, drawn on a 3D campus map. Every number says where it came from, because it is an estimate, not a sensor reading.

## What's here
| Part | Status | What it does |
|---|---|---|
| `pipeline/` | working | Pulls every section's meetings and enrollment from umd.io, builds hourly seat grids per building and busy intervals per room. A Testudo HTML parser is ready as a fallback if umd.io goes down (not yet wired into the CLI) |
| `data/umd/` | snapshot | JSON the site loads; fall 2026 snapshot (9,143 sections, 72 buildings, 758 rooms) |
| `web/` | planned | MapLibre 3D map + free-rooms finder |

## Run it
Needs Python 3.10+.
```bash
python3 -m venv .venv && source .venv/bin/activate
cd pipeline
python3 -m pip install -e '.[dev]'
pytest
python3 -m terp_spaces.cli --term 202608 --out ../data/umd
```

umd.io is slow (about 15 minutes for a full term), so every page is cached in `.cache/umdio/<term>/`. A crashed run resumes where it stopped, and reruns are instant. Delete that folder to download fresh data.

Not affiliated with the University of Maryland.
