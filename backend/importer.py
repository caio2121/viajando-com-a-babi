from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .providers import import_sync
from .storage import Database, ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Persiste o snapshot normalizado do provider no SQLite local")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--sync", type=Path, default=None)
    args = parser.parse_args()
    logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")
    db = Database()
    result = import_sync(db, args.root.resolve(), args.sync.resolve() if args.sync else None)
    print(result)


if __name__ == "__main__":
    main()
