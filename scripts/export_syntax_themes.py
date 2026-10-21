"""Generate or verify the committed syntax theme fallback CSS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OUTPUT = ROOT / "src/shared/css/generated/cassidy-dark.css"


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    from addon_module_loader import load_addon_module

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    css = load_addon_module("desktop.syntax_highlighting.themes").generate_theme_css()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != css:
            print(
                "Generated Cassidy Dark CSS is missing or stale; run npm run build:addon."
            )
            return 1
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(css, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
