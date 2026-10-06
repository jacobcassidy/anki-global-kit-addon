"""Combine font attribution and license texts into a synced media companion."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "addon/shared/assets/fonts"


def font_notice_sources() -> list[Path]:
    """Include all license texts and require every notice linked by attribution."""
    attribution = FONT_DIR / "FONT-LICENSES.md"
    if not attribution.is_file():
        raise FileNotFoundError(f"Missing font attribution: {attribution}")
    references = re.findall(
        r"\]\((licenses/[^)]+\.txt)\)", attribution.read_text(encoding="utf-8")
    )
    sources = {attribution, *(FONT_DIR / reference for reference in references)}
    licenses = set((FONT_DIR / "licenses").glob("*.txt"))
    if not licenses:
        raise FileNotFoundError(f"Missing font license texts: {FONT_DIR / 'licenses'}")
    sources.update(licenses)
    for path in sorted(sources):
        if not path.is_file():
            raise FileNotFoundError(f"Missing font notice source: {path}")
        if not path.read_text(encoding="utf-8").strip():
            raise ValueError(f"Empty font notice source: {path}")
    return [attribution, *sorted(sources - {attribution})]


def render_font_notice() -> bytes:
    """Return deterministic UTF-8 text, preserving all attribution and licenses."""
    sections = [
        "MESLOLGL NERD FONT — SOURCE, ATTRIBUTION, AND LICENSES\n\n"
        "Generated from the add-on's shared/assets/fonts/FONT-LICENSES.md "
        "and licenses/ folder.\n"
        "Keep this notice with _mesloLGL-NF.woff2 when sharing or syncing the font.\n"
        "Full license texts follow the attribution, labelled by source filename."
    ]
    for path in font_notice_sources():
        text = path.read_text(encoding="utf-8").rstrip("\n")
        if path.suffix == ".md":
            # Relative license links would not resolve in collection.media.
            # Their complete text is included below under each source filename.
            text = re.sub(
                r"\[([^\]]+)\]\((licenses/[^)]+\.txt)\)",
                r"\1 (full text below: \2)",
                text,
            )
        filename = path.relative_to(FONT_DIR).as_posix()
        sections.append(f"{'=' * 72}\n{filename}\n{'=' * 72}\n\n{text}")
    return ("\n\n".join(sections) + "\n").encode("utf-8")


def write_font_notice() -> Path:
    if __package__:
        from .check_assets import load_script_module
    else:
        from check_assets import load_script_module

    manifest = load_script_module(
        ROOT / "addon/desktop/settings/configs/asset_manifest.py",
        "anki_global_kit_font_notice_manifest",
    )
    path = manifest.ASSET_PATHS[manifest.FONT_LICENSE_ASSET_NAME]
    data = render_font_notice()
    if not path.is_file() or path.read_bytes() != data:
        path.write_bytes(data)
    return path


if __name__ == "__main__":
    try:
        print(f"Generated {write_font_notice()}")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from error
