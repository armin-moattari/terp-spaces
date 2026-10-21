"""Build data/umd/class_activity.json, rooms.json and occupancy.json.

Reads the hand-written building_hours.json and academic_calendar.json from --out.

    python -m terp_spaces.cli --term 202608 --out ../data/umd
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .activity import building_grids, room_busy
from .occupancy import forecast
from .umdio import iter_sections

CAMPUS_TZ = ZoneInfo("America/New_York")
FORECAST_HOURS = 7 * 24


def local_hour_now() -> datetime:
    """Current campus time, truncated to the hour, as a naive local datetime."""
    return datetime.now(CAMPUS_TZ).replace(minute=0, second=0, microsecond=0, tzinfo=None)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--term", default="202608", help="YYYYMM term code, e.g. 202608")
    ap.add_argument("--out", type=Path, default=Path("../data/umd"))
    ap.add_argument("--cache", type=Path, default=Path("../.cache/umdio"),
                    help="where raw umd.io pages are kept; delete it to re-download")
    ap.add_argument("--start", type=datetime.fromisoformat, default=None,
                    help="forecast start, local time (default: this hour), e.g. 2026-10-21T00:00")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%H:%M:%S")

    sections = list(iter_sections(args.term, cache_dir=args.cache))
    meta = {"term": args.term, "built_at": datetime.now(timezone.utc).isoformat(),
            "source": "umd.io mirror of the Testudo Schedule of Classes",
            "sections_read": len(sections)}

    args.out.mkdir(parents=True, exist_ok=True)
    grids = building_grids(sections)
    rooms = room_busy(sections)
    (args.out / "class_activity.json").write_text(json.dumps({**meta, "buildings": grids}))
    (args.out / "rooms.json").write_text(json.dumps({**meta, "rooms": rooms}))

    hours = json.loads((args.out / "building_hours.json").read_text())["buildings"]
    cal = json.loads((args.out / "academic_calendar.json").read_text())
    start = args.start or local_hour_now()
    occ = forecast(start, FORECAST_HOURS, grids, hours, cal)
    (args.out / "occupancy.json").write_text(json.dumps({
        **meta, "timezone": "America/New_York", "start": start.isoformat(),
        "hours": FORECAST_HOURS, "buildings": occ}))
    print(f"{len(sections)} sections -> {len(grids)} buildings, {len(rooms)} rooms; "
          f"occupancy for {len(occ)} buildings from {start:%Y-%m-%d %H:00}")


if __name__ == "__main__":
    main()
