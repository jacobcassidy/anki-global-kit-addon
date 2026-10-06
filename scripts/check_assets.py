"""Check card/editor assets, shared icons, templates, and their package paths."""

import ast
import importlib.util
import re
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


def read_source(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require_packaged(path: Path, packaged_paths: set[Path]) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required asset: {path.relative_to(ROOT)}")
    if path.resolve() not in packaged_paths:
        raise ValueError(f"Asset is not included in the add-on package: {path.relative_to(ROOT)}")


def css_asset_url(filename: str) -> str:
    name = re.escape(filename)
    return rf"url\(\s*(?:['\"]{name}['\"]|{name})\s*\)"


def validate_build_target(config: str, name: str, entry: str, output: str) -> None:
    block = re.search(rf"export const {name} = \{{(.*?)\n\}};", config, re.S)
    if block is None:
        raise ValueError(f"Missing build target: {name}")
    if f"entryPoints: [`${{root}}{entry}`]" not in block[1]:
        raise ValueError(f"{name} must build from {entry}")
    if f"outfile: `{output}`" not in block[1]:
        raise ValueError(f"Incorrect build output for {name}: expected {output}")
    read_source(ROOT / entry)


def validate_icons(packaged_paths: set[Path]) -> int:
    icons = set()
    for source in (ROOT / "src").rglob("*.js"):
        for reference in re.findall(r"(?:from|import)\s*['\"]([^'\"]+\.svg)['\"]", read_source(source)):
            icons.add((source.parent / reference).resolve())

    # Desktop controls refer to shared icons by filename. Read literals rather
    # than importing Qt modules, so this command runs outside Anki.
    for source in (ROOT / "addon/desktop").rglob("*.py"):
        for node in ast.walk(ast.parse(read_source(source), filename=str(source))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.endswith(".svg") and Path(node.value).name == node.value:
                    icons.add(ROOT / "addon/shared/assets/icons" / node.value)
    for icon in sorted(icons):
        require_packaged(icon, packaged_paths)
    return len(icons)


def validate_templates(packaged_paths: set[Path]) -> int:
    service = ROOT / "addon/desktop/settings/services/note_types.py"
    definitions = {}
    for node in ast.parse(read_source(service), filename=str(service)).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"TOPICS", "FORMATS"}:
                    definitions[target.id] = ast.literal_eval(node.value)
    if set(definitions) != {"TOPICS", "FORMATS"}:
        raise ValueError("Cannot read TOPICS and FORMATS from the note type service")

    parts = ROOT / "addon/templates/note-types/parts"
    paths = {
        parts / "script/card-script.js",
        parts / "styling/imports.css",
        parts / "styling/style-default.css",
    }
    for spec in definitions["FORMATS"].values():
        paths.update(parts / "html" / spec[side] for side in ("front", "back"))
    for topic in definitions["TOPICS"]:
        style = "shell" if topic == "Command Line" else topic.lower()
        paths.add(parts / "styling" / f"style-{style}.css")
    for path in sorted(paths):
        require_packaged(path, packaged_paths)
    return len(paths)


def validate_assets(package_files: list[Path]) -> str:
    """Validate existing build artifacts without importing Anki or creating an archive."""
    manifest = load_script_module(
        ROOT / "addon/desktop/settings/configs/asset_manifest.py",
        "anki_global_kit_asset_manifest",
    )
    packaged_paths = {path.resolve() for path in package_files}
    categories = {".js": "js", ".css": "css"}
    for media_name, source_path in manifest.ASSET_PATHS.items():
        if source_path.suffix in {".woff", ".woff2"} or (
            media_name == manifest.FONT_LICENSE_ASSET_NAME and source_path.suffix == ".txt"
        ):
            expected_parent = ROOT / "addon/shared/assets/fonts"
        elif source_path.suffix in categories:
            expected_parent = ROOT / "addon/web/assets" / categories[source_path.suffix]
        else:
            raise ValueError(f"Unsupported card asset type: {media_name}")
        if source_path.parent != expected_parent:
            raise ValueError(f"{media_name} must be sourced from {expected_parent.relative_to(ROOT)}/")
        if Path(media_name).name != media_name:
            raise ValueError(f"{media_name} must install at the collection.media root")
        if media_name != media_name.lower():
            raise ValueError(f"{media_name} must be lowercase to match Anki's media writer")
        require_packaged(source_path, packaged_paths)

    font_notices = load_script_module(ROOT / "scripts/font_notices.py", "anki_global_kit_font_notices")
    for path in font_notices.font_notice_sources():
        require_packaged(path, packaged_paths)
    notice = manifest.ASSET_PATHS[manifest.FONT_LICENSE_ASSET_NAME]
    if notice.read_bytes() != font_notices.render_font_notice():
        raise ValueError("The combined font notice is out of date. Run `npm run build:addon`.")

    build_config = read_source(ROOT / "scripts/build.config.js")
    for target, entry, category, asset_name in (
        ("cardsJsBuildOptions", "src/cards/js/index.js", "js", manifest.JS_ASSET_NAME),
        ("cardsCssBuildOptions", "src/cards/css/index.css", "css", manifest.CSS_ASSET_NAME),
    ):
        validate_build_target(build_config, target, entry, f"${{addonWebAssets}}/{category}/{asset_name}")

    integration = read_source(ROOT / "addon/desktop/editor/integration.py")
    editor_assets = (
        ("editorJsBuildOptions", "src/editor/js/index.js", "js/editor.min.js"),
        ("editorFieldsCssBuildOptions", "src/editor/css/editor-fields.css", "css/editor-fields.min.css"),
        ("editorUiCssBuildOptions", "src/editor/css/editor-ui.css", "css/editor-ui.min.css"),
    )
    for target, entry, relative_output in editor_assets:
        output = f"addon/desktop/editor/assets/{relative_output}"
        require_packaged(ROOT / output, packaged_paths)
        validate_build_target(build_config, target, entry, f"${{root}}{output}")
        if f'"{Path(relative_output).name}"' not in integration:
            raise ValueError(f"Desktop editor does not reference {relative_output}")

    icon_count = validate_icons(packaged_paths)
    template_count = validate_templates(packaged_paths)
    parts = ROOT / "addon/templates/note-types/parts"
    script_reference = rf"injectScript\(\s*(['\"]){re.escape(manifest.JS_ASSET_NAME)}\1\s*\)"
    if not re.search(script_reference, read_source(parts / "script/card-script.js")):
        raise ValueError(f"Card templates do not reference {manifest.JS_ASSET_NAME}")
    if not re.search(r"@import\s+" + css_asset_url(manifest.CSS_ASSET_NAME), read_source(parts / "styling/imports.css")):
        raise ValueError(f"Card templates do not reference {manifest.CSS_ASSET_NAME}")
    for stylesheet in (
        ROOT / "src/shared/css/fonts.css",
        manifest.ASSET_PATHS[manifest.CSS_ASSET_NAME],
        ROOT / "addon/desktop/editor/assets/css/editor-fields.min.css",
    ):
        if not re.search(css_asset_url(manifest.FONT_ASSET_NAME), read_source(stylesheet)):
            raise ValueError(f"{stylesheet.relative_to(ROOT)} does not reference {manifest.FONT_ASSET_NAME}")

    installer = read_source(ROOT / "addon/desktop/settings/services/assets.py")
    required_installer_paths = (
        "ASSET_PATHS[name].read_bytes()",
        "Path(mw.col.media.dir()) / name",
        "mw.col.media.write_data(name, data)",
    )
    if any(path not in installer for path in required_installer_paths):
        raise ValueError("The card asset installer must map packaged sources to media root filenames")

    return (
        f"Validated {len(manifest.ASSET_PATHS)} card assets, {len(editor_assets)} editor assets, "
        f"{icon_count} shared icons, and {template_count} template parts across source, "
        "build, package, and media paths."
    )


def main() -> None:
    packager = load_script_module(ROOT / "scripts/package_addon.py", "anki_global_kit_packager")
    print(validate_assets(packager.package_files()))


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, SyntaxError) as error:
        raise SystemExit(str(error)) from error
