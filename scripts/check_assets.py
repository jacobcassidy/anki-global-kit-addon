"""Check card asset source, build, package, and Anki media paths."""

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_script_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


manifest = load_script_module(
    ROOT / "addon/desktop/settings/shared/asset_manifest.py",
    "anki_global_kit_asset_manifest",
)
packager = load_script_module(
    ROOT / "scripts/package_addon.py",
    "anki_global_kit_packager",
)

expected_categories = {".js": "js", ".css": "css", ".woff": "fonts", ".woff2": "fonts"}
packaged_paths = {path.resolve() for path in packager.package_files()}
for media_name, source_path in manifest.ASSET_PATHS.items():
    category = expected_categories.get(source_path.suffix)
    if category is None or source_path.parent.name != category:
        raise SystemExit(
            f"{media_name} must be sourced from addon/web/assets/{category or 'an expected asset folder'}/"
        )
    if Path(media_name).name != media_name:
        raise SystemExit(f"{media_name} must install at the collection.media root")
    if not source_path.is_file():
        raise SystemExit(f"Missing card asset source: {source_path.relative_to(ROOT)}")
    if source_path.resolve() not in packaged_paths:
        raise SystemExit(f"Card asset is not included in the add-on package: {media_name}")

build_config = (ROOT / "scripts/build.config.js").read_text(encoding="utf-8")
for category, asset_name in (
    ("js", manifest.JS_ASSET_NAME),
    ("css", manifest.CSS_ASSET_NAME),
):
    output = f"outfile: `${{addonWebAssets}}/{category}/{asset_name}`"
    if output not in build_config:
        raise SystemExit(f"Build output must be addon/web/assets/{category}/{asset_name}")

card_script = (
    ROOT / "addon/templates/note-types/parts/script/card-script.js"
).read_text(encoding="utf-8")
card_styles = (
    ROOT / "addon/templates/note-types/parts/styling/imports.css"
).read_text(encoding="utf-8")
if manifest.JS_ASSET_NAME not in card_script:
    raise SystemExit(f"Card templates do not reference {manifest.JS_ASSET_NAME}")
if manifest.CSS_ASSET_NAME not in card_styles:
    raise SystemExit(f"Card templates do not reference {manifest.CSS_ASSET_NAME}")

installer = (ROOT / "addon/desktop/settings/services/assets.py").read_text(
    encoding="utf-8"
)
required_installer_paths = (
    "ASSET_PATHS[name].read_bytes()",
    "Path(mw.col.media.dir()) / name",
    "mw.col.media.write_data(name, data)",
)
if any(path not in installer for path in required_installer_paths):
    raise SystemExit("The card asset installer must map packaged sources to media root filenames")

print(
    f"Validated {len(manifest.ASSET_PATHS)} card assets across source, build, "
    "package, and collection.media paths."
)
