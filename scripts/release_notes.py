"""Extract the latest dated changelog release and validate package versions."""

import argparse
from datetime import date
import json
from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"


def latest_release(changelog: str) -> tuple[str, str]:
    """Ignore Unreleased and fenced examples, retaining the release's Markdown."""
    lines = changelog.splitlines(keepends=True)
    version = None
    start = None
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is not None or not line.startswith("## "):
            continue
        if start is not None:
            notes = "".join(lines[start:index]).strip()
            break
        if line.strip() == "## [Unreleased]":
            continue
        heading = re.fullmatch(
            rf"## \[({VERSION_PATTERN})\] - (\d{{4}}-\d{{2}}-\d{{2}})",
            line.strip(),
        )
        if not heading:
            raise ValueError("The latest release needs a version and date: ## [1.2.3] - YYYY-MM-DD")
        date.fromisoformat(heading[2])
        version = heading[1]
        start = index + 1
    else:
        notes = "".join(lines[start:]).strip() if start is not None else ""
    if version is None:
        raise ValueError("The changelog has no dated release section.")
    if not notes:
        raise ValueError(f"The changelog section for {version} has no release notes.")
    return version, notes + "\n"


def validate_versions(root: Path, version: str) -> None:
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "addon/manifest.json").read_text(encoding="utf-8"))
    versions = {
        "package.json": package["version"],
        "package-lock.json": lock["version"],
        "package-lock.json packages root": lock["packages"][""]["version"],
        "addon/manifest.json": manifest["version"],
    }
    mismatches = [f"{name}: {value}" for name, value in versions.items() if value != version]
    if mismatches:
        raise ValueError(f"Package versions must match changelog {version}: " + ", ".join(mismatches))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Markdown notes destination")
    parser.add_argument("--github-output", type=Path, help="GitHub Actions step output file")
    args = parser.parse_args()
    version, notes = latest_release((REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    validate_versions(REPOSITORY_ROOT, version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(notes, encoding="utf-8")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"version={version}\ntag=v{version}\n")
    print(f"Prepared release notes for v{version}: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error)) from error
