"""Check platform-independent settings installed into synced card media."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CardSettingsTests(unittest.TestCase):
    def installed_settings(self, *, mac, config=None):
        aqt = ModuleType("aqt")
        aqt.mw = SimpleNamespace(addonManager=SimpleNamespace(getConfig=lambda _name: config or {}))
        utils = ModuleType("aqt.utils")
        utils.is_mac = mac
        utils.showWarning = Mock()
        prefix = "kit.desktop.settings"
        manifest = load_module(f"{prefix}.configs.asset_manifest", "addon/desktop/settings/configs/asset_manifest.py")
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {
            "aqt": aqt, "aqt.utils": utils, f"{prefix}.configs.asset_manifest": manifest,
        }):
            constants = load_module(f"{prefix}.configs.constants", "addon/desktop/settings/configs/constants.py")
            with patch.dict(sys.modules, {f"{prefix}.configs.constants": constants}):
                settings = load_module(f"{prefix}.services.config", "addon/desktop/settings/services/config.py")
            with patch.dict(sys.modules, {f"{prefix}.services.config": settings}):
                assets = load_module(f"{prefix}.services.assets", "addon/desktop/settings/services/assets.py")
            # Install the real bundle through a media-manager stand-in.
            def write_data(name, data):
                (Path(directory) / name).write_bytes(data)
                return name
            aqt.mw.col = SimpleNamespace(media=SimpleNamespace(dir=lambda: directory, write_data=write_data))
            assets.ASSET_NAMES = (manifest.JS_ASSET_NAME,)
            assets.update_assets_for_profile()
            utils.showWarning.assert_not_called()
            source = (Path(directory) / manifest.JS_ASSET_NAME).read_text()
            installed = json.loads(source.splitlines()[0].split("=", 1)[1][:-1])
            return installed, settings.get_settings()

    def test_default_primary_modifier_stays_portable_from_both_platforms(self):
        for mac in (False, True):
            with self.subTest(mac=mac):
                installed, _ = self.installed_settings(mac=mac)
                self.assertEqual(installed["card_input_tab_indent_increase_shortcut"], "Ctrl+Shift+.")
                self.assertEqual(installed["card_input_tab_indent_decrease_shortcut"], "Ctrl+Shift+,")

    def test_legacy_physical_control_remains_physical_without_changing_qt_settings(self):
        key = "card_input_tab_indent_decrease_shortcut"
        for mac in (False, True):
            with self.subTest(mac=mac):
                installed, desktop = self.installed_settings(mac=mac, config={key: "Control+Tab"})
                self.assertEqual(installed[key], "Control+Tab")
                self.assertEqual(desktop[key], "Meta+Tab" if mac else "Ctrl+Tab")

    def test_mac_custom_physical_control_is_preserved_in_synced_media(self):
        key = "card_input_tab_indent_increase_shortcut"
        installed, desktop = self.installed_settings(mac=True, config={key: "Meta+]"})
        self.assertEqual(installed[key], "Control+]")
        self.assertEqual(desktop[key], "Meta+]")


if __name__ == "__main__":
    unittest.main()
