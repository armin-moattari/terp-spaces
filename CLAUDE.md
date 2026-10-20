# Terp Spaces

A live map of how busy University of Maryland buildings are, plus which classrooms are free right now. Estimates come from the Testudo class schedule (via umd.io), published building hours, and later, student check-ins. Inspired by campusquiet.com/umd, which Armin reverse-engineered; this is his own build with its own angle (room-level "free now" finder, course info from PlanetTerp).

## Language rules (read first)
- **pipeline/** is Python 3.10+ only: scrapers and JSON builders. Tests use pytest.
- **web/** is TypeScript + Vite + MapLibre GL. No framework unless we agree to add one.
- Do not mix: no Python in web/, no JS in pipeline/. CI YAML is the only other code.

## Goals
- Resume project for SWE roles: data pipeline + scheduled jobs + map frontend + deployed site.
- Honest numbers: every estimate carries a `source` (estimated / typical / reported / closed / unknown) and the UI says where it came from, so a guess never reads like a measurement.
- Be a polite scraper: nightly at most, one request at a time, cache results, identify with a User-Agent.

## How we work together
- **Claude writes the code, including tests.** Explain the key design choices in each change so Armin can learn from and review it.
- Comment and document well: module docstrings, docstrings on public functions, inline comments for non-obvious logic.
- Keep modules small and modular. Suggest a refactor when a file or function grows unwieldy.
- Run `cd pipeline && pytest` (and `npm test` in web/ once it exists) before every commit. Never commit failing tests.
- Network calls stay at the edges (`umdio.py`, `cli.py`); everything else is pure functions tested with fixtures. Tests never hit the network.
- Keep the README current as pieces land.
- Show the proposed commit message and wait for approval before committing. Small, focused, conventional-style commits (e.g. `feat(pipeline): build hourly seat grids`).
- Explain *why* when recommending a change, briefly.

## Data sources (verified 2026-10-20)
- **umd.io** `https://api.umd.io/v1/courses/sections?semester=202608&per_page=100&page=N` — JSON, no key. Each section: `seats`, `open_seats`, `waitlist`, `instructors`, `meetings[]` with `days` ("MWF", "TuTh"), `start_time` ("11:00am"), `end_time`, `building` ("IRB"), `room` ("1207" or "ONLINE"). Lags Testudo slightly on seat counts.
- **Testudo** `https://app.testudo.umd.edu/soc/202608/<DEPT>` and `/soc/202608/sections?courseIds=CMSC434` — HTML. Selectors: `.section`, `.section-id`, `.total-seats-count`, `.open-seats-count`, `.section-days`, `.class-start-time`, `.class-end-time`, `.building-code`, `.class-room`. Use for fresher seat counts if umd.io drifts.
- **PlanetTerp** `https://planetterp.com/api/v1/course?name=CMSC434`, `/grades?course=...` — course info, professors, grade distributions. No rooms or times; use for tooltips.
- **Building hours**: Libraries (lib.umd.edu/visit/hours), Stamp (stamp.umd.edu), RecWell. Start with a hand-written `data/umd/building_hours.json`.
- **Footprints**: OpenStreetMap buildings, or MD iMAP's UMD buildings layer (has building numbers to match Testudo codes).
- Term codes: YYYY + 01 spring, 05 summer, 08 fall, 12 winter.

## Occupancy model (v1)
1. Closed per building hours → 0, source `closed`.
2. Class estimate = enrolled seats in session this hour ÷ that building's weekly peak, × a per-building `peakFullness` cap.
3. Libraries / Stamp / gyms: 24-hour typical curves by type; take max(curve, classes).
4. Breaks and finals scale class activity to 0 (academic calendar).
5. Later: blend student check-ins (Quiet/Okay/Packed), trust growing with report count and decaying with age.
6. Colors: < 0.3 quiet, < 0.55 moderate, else busy.

## Layout
```
pipeline/src/terp_spaces/
  schedule.py   # parse "TuTh", "11:00am"; hour overlap math (pure)
  activity.py   # sections -> building hour grids, room busy intervals (pure)
  umdio.py      # umd.io client (network)
  cli.py        # `python -m terp_spaces.cli` -> writes data/umd/*.json
pipeline/tests/ # pytest, fixtures only
data/umd/       # generated JSON the site serves (committed by the nightly job)
web/            # Vite + TS + MapLibre site
.github/workflows/
```

## Milestones
1. Setup: `git init`, GitHub repo (github.com/armin-moattari/terp-spaces), CI running pytest. Scaffold and first tests already exist.
2. Pipeline: run `cli.py` against umd.io for real; sanity-check output (IRB, ESJ, McKeldin); add Testudo fallback scraper with HTML fixtures.
3. Building hours JSON + academic calendar; occupancy model as a pure, tested module.
4. Web: Vite + TS + MapLibre, 3D extruded buildings colored by occupancy, tooltip with source + note.
5. "Free rooms now" panel: per building, rooms with no class for the next N minutes.
6. Nightly GitHub Action rebuilds data/ and deploys (Vercel or GitHub Pages).
7. PlanetTerp: "in this building now" list with course title, instructor, average GPA.
8. Stretch: Quiet/Okay/Packed check-ins (Supabase), PWA for iPhone home screen, Android client (CMSC436 tie-in).

## Commands
- Install: `cd pipeline && python3 -m pip install -e '.[dev]'`
- Test: `cd pipeline && pytest`
- Build data: `cd pipeline && python3 -m terp_spaces.cli --term 202608 --out ../data/umd`
