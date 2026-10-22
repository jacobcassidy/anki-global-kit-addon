"""Check platform-independent settings installed into synced card media."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.support.anki_stubs import load_module

ROOT = Path(__file__).resolve().parents[3]


class CardSettingsTests(unittest.TestCase):
    def installed_settings(self, *, mac, config=None):
        aqt = ModuleType("aqt")
        aqt.mw = SimpleNamespace(
            addonManager=SimpleNamespace(getConfig=lambda _name: config or {})
        )
        utils = ModuleType("aqt.utils")
        utils.is_mac = mac
        utils.showWarning = Mock()
        prefix = "kit.desktop"
        paths = load_module(f"{prefix}.paths", "addon/desktop/paths.py")
        manifest = load_module(
            f"{prefix}.media.manifest",
            "addon/desktop/media/manifest.py",
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(
                sys.modules,
                {
                    "aqt": aqt,
                    "aqt.utils": utils,
                    f"{prefix}.media.manifest": manifest,
                    f"{prefix}.paths": paths,
                },
            ),
        ):
            constants = load_module(
                f"{prefix}.config.constants",
                "addon/desktop/config/constants.py",
            )
            with patch.dict(sys.modules, {f"{prefix}.config.constants": constants}):
                defaults = load_module(
                    f"{prefix}.config.defaults",
                    "addon/desktop/config/defaults.py",
                )
            with patch.dict(sys.modules, {f"{prefix}.config.defaults": defaults}):
                settings = load_module(
                    f"{prefix}.config.service",
                    "addon/desktop/config/service.py",
                )
            with patch.dict(sys.modules, {f"{prefix}.config.service": settings}):
                assets = load_module(
                    f"{prefix}.media.install",
                    "addon/desktop/media/install.py",
                )

            # Install the real bundle through a media-manager stand-in.
            def write_data(name, data):
                (Path(directory) / name).write_bytes(data)
                return name

            collection_config = {}
            aqt.mw.col = SimpleNamespace(
                media=SimpleNamespace(dir=lambda: directory, write_data=write_data),
                get_config=lambda key, default=None: collection_config.get(
                    key, default
                ),
                set_config=lambda key, value: collection_config.__setitem__(key, value),
            )
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
                self.assertEqual(
                    installed["card_input_tab_indent_increase_shortcut"], "Ctrl+Alt+."
                )
                self.assertEqual(
                    installed["card_input_tab_indent_decrease_shortcut"], "Ctrl+Alt+,"
                )

    def test_legacy_physical_control_remains_physical_without_changing_qt_settings(
        self,
    ):
        key = "card_input_tab_indent_decrease_shortcut"
        for mac in (False, True):
            with self.subTest(mac=mac):
                installed, desktop = self.installed_settings(
                    mac=mac, config={key: "Control+Tab"}
                )
                self.assertEqual(installed[key], "Control+Tab")
                self.assertEqual(desktop[key], "Meta+Tab" if mac else "Ctrl+Tab")

    def test_mac_custom_physical_control_is_preserved_in_synced_media(self):
        key = "card_input_tab_indent_increase_shortcut"
        installed, desktop = self.installed_settings(mac=True, config={key: "Meta+]"})
        self.assertEqual(installed[key], "Control+]")
        self.assertEqual(desktop[key], "Meta+]")


if __name__ == "__main__":
    unittest.main()
