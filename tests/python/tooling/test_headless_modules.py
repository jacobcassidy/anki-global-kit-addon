"""Check the build-tool import path in a process without Anki or Qt."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class HeadlessModuleTests(unittest.TestCase):
    def test_pure_defaults_and_asset_manifest_load_without_anki_or_qt(self):
        script = """
import json
import sys
from pathlib import Path
from scripts.addon_module_loader import load_addon_module

defaults = load_addon_module('desktop.config.defaults').DEFAULT_SETTINGS
manifest = load_addon_module('desktop.media.manifest')
release = json.loads((Path('addon/config.json')).read_text())
assert defaults == {key: value for key, value in release.items() if key != 'note_type_selections'}
assert manifest.ASSET_PATHS[manifest.JS_ASSET_NAME].is_file()
assert 'aqt' not in sys.modules and 'anki' not in sys.modules
"""
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, check=True)

    def test_template_asset_validation_reads_annotated_service_constants(self):
        script = """
import sys
from scripts.package_addon import package_files
from scripts.verify_package_assets import validate_templates

paths = {path.resolve() for path in package_files()}
assert validate_templates(paths) > 0
assert 'aqt' not in sys.modules and 'anki' not in sys.modules
"""
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
