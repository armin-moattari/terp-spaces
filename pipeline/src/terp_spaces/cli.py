"""Build data/umd/class_activity.json and rooms.json from umd.io.

    python -m terp_spaces.cli --term 202608 --out ../data/umd
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .activity import building_grids, room_busy
from .umdio import iter_sections


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--term", default="202608", help="YYYYMM term code, e.g. 202608")
    ap.add_argument("--out", type=Path, default=Path("../data/umd"))
    args = ap.parse_args(argv)

    sections = list(iter_sections(args.term))
    meta = {"term": args.term, "built_at": datetime.now(timezone.utc).isoformat(),
            "source": "umd.io mirror of the Testudo Schedule of Classes",
            "sections_read": len(sections)}

    args.out.mkdir(parents=True, exist_ok=True)
    grids = building_grids(sections)
    rooms = room_busy(sections)
    (args.out / "class_activity.json").write_text(json.dumps({**meta, "buildings": grids}))
    (args.out / "rooms.json").write_text(json.dumps({**meta, "rooms": rooms}))
    print(f"{len(sections)} sections -> {len(grids)} buildings, {len(rooms)} rooms")


if __name__ == "__main__":
    main()
