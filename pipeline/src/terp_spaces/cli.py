"""Build data/umd/class_activity.json and rooms.json from umd.io.

    python -m terp_spaces.cli --term 202608 --out ../data/umd
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .activity import building_grids, room_busy
from .umdio import iter_sections


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--term", default="202608", help="YYYYMM term code, e.g. 202608")
    ap.add_argument("--out", type=Path, default=Path("../data/umd"))
    ap.add_argument("--cache", type=Path, default=Path("../.cache/umdio"),
                    help="where raw umd.io pages are kept; delete it to re-download")
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
    print(f"{len(sections)} sections -> {len(grids)} buildings, {len(rooms)} rooms")


if __name__ == "__main__":
    main()
