# Terp Spaces

[![CI](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml/badge.svg)](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml)

How busy is each University of Maryland building right now, and which classrooms are free?

Terp Spaces turns the Testudo class schedule (via [umd.io](https://api.umd.io)) and published building hours into an hourly estimate for every building, drawn on a 3D campus map. Every number says where it came from, because it is an estimate, not a sensor reading.

## What's here
| Part | Status | What it does |
|---|---|---|
| `pipeline/` | started | Pulls every section's meetings and enrollment, builds hourly seat grids per building and busy intervals per room |
| `data/umd/` | generated | JSON the site loads |
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

Not affiliated with the University of Maryland.
