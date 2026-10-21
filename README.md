# Terp Spaces

[![CI](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml/badge.svg)](https://github.com/armin-moattari/terp-spaces/actions/workflows/ci.yml)

How busy is each University of Maryland building right now, and which classrooms are free?

Terp Spaces turns the Testudo class schedule (via [umd.io](https://api.umd.io)) and published building hours into an hourly estimate for every building, drawn on a 3D campus map. Every number says where it came from, because it is an estimate, not a sensor reading.

## What's here
| Part | Status | What it does |
|---|---|---|
| `pipeline/` | working | Pulls every section's meetings and enrollment from umd.io, builds hourly seat grids per building and busy intervals per room. A Testudo HTML parser is ready as a fallback if umd.io goes down (not yet wired into the CLI) |
| `data/umd/` | snapshot | JSON the site loads; fall 2026 snapshot (9,143 sections, 72 buildings, 758 rooms). `building_hours.json` and `academic_calendar.json` are hand-written inputs with a source URL and verified date on each entry |
| `web/` | planned | MapLibre 3D map + free-rooms finder |

## How busy is "busy"?
`occupancy.json` holds an hourly estimate for every building for the next 7 days. Each hour says where its number came from:

| Source | Meaning |
|---|---|
| `closed` | Posted hours say the building is shut |
| `estimated` | Scheduled class seats this hour ÷ the building's busiest hour, capped at 85% full, scaled by an assumed attendance that slides from 100% to 75% over the term. No classes on breaks, reading day or finals |
| `typical` | Libraries, Stamp and Eppley follow a hand-made daily curve (quieter on weekends and breaks); the larger of curve and classes wins |
| `unknown` | No posted hours and nothing scheduled, so we don't guess. Most academic buildings at night, until their hours are added |

The curves, the 85% cap and the attendance slide are assumptions, not measurements. Student check-ins will replace them later.

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
