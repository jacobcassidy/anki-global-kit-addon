"""Check managed media updates, unrelated-file isolation, and write recovery."""

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from anki_stubs import load_settings_services


class Media:
    def __init__(self, directory):
        self.directory = directory
        self.writes = []
        self.trashed = []
        self.failures = 0
        self.rename_next = False

    def dir(self):
        return str(self.directory)

    def trash_files(self, names):
        self.trashed.extend(names)
        for name in names:
            (self.directory / name).unlink()

    def write_data(self, name, data):
        self.writes.append(name)
        if self.failures:
            self.failures -= 1
            raise OSError("injected media write failure")
        if self.rename_next:
            self.rename_next = False
            name = f"renamed-{name}"
        path = self.directory / name
        if path.is_file() and path.read_bytes() != data:
            raise AssertionError("Updated managed media must be trashed before writing")
        path.write_bytes(data)
        return name


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        source = root / "source"
        source.mkdir()
        destination = root / "media"
        destination.mkdir()
        self.config = {}
        self.services = load_settings_services(config=self.config)
        self.assets = self.services.assets
        self.assets.ASSET_PATHS = {}
        for name in self.assets.ASSET_NAMES:
            path = source / name
            path.write_bytes(f"packaged content: {name}".encode())
            self.assets.ASSET_PATHS[name] = path
        self.media = Media(destination)
        self.services.mw.col = SimpleNamespace(media=self.media)
        self.unrelated = destination / "user-picture.png"
        self.unrelated.write_bytes(b"user media")

    def test_fresh_install_is_scoped_to_managed_names_and_unchanged_files_are_skipped(self):
        self.assets.update_assets_for_profile()
        self.assertEqual(set(self.media.writes), set(self.assets.ASSET_NAMES))
        self.assertEqual(self.unrelated.read_bytes(), b"user media")
        self.assertEqual(self.media.trashed, [])
        self.media.writes.clear()
        self.assets.update_assets_for_profile()
        self.assertEqual(self.media.writes, [])
        self.services.warning.assert_not_called()

    def test_changed_card_settings_refresh_only_the_javascript(self):
        self.assets.update_assets_for_profile()
        self.media.writes.clear()
        self.config["card_input_markdown_shortcuts"] = False
        self.assets.update_assets_for_profile()
        self.assertEqual(self.media.writes, [self.assets.JS_ASSET_NAME])
        self.assertEqual(self.media.trashed, [self.assets.JS_ASSET_NAME])
        self.assertEqual(self.unrelated.read_bytes(), b"user media")

    def test_failed_refresh_restores_previous_media_and_can_be_retried(self):
        self.assets.update_assets_for_profile()
        path = self.media.directory / self.assets.JS_ASSET_NAME
        previous = path.read_bytes()
        self.config["card_input_markdown_shortcuts"] = False
        self.media.failures = 1
        self.assets.update_assets_for_profile()
        self.assertEqual(path.read_bytes(), previous)
        self.assertIn("injected media write failure", self.services.warning.call_args.args[0])
        self.assertEqual(self.unrelated.read_bytes(), b"user media")
        self.services.warning.reset_mock()
        self.assets.update_assets_for_profile()
        self.assertNotEqual(path.read_bytes(), previous)
        self.services.warning.assert_not_called()

    def test_unexpected_filename_is_reported_and_original_media_is_restored(self):
        self.assets.update_assets_for_profile()
        path = self.media.directory / self.assets.JS_ASSET_NAME
        previous = path.read_bytes()
        self.config["card_input_markdown_shortcuts"] = False
        self.media.rename_next = True
        self.assets.update_assets_for_profile()
        self.assertEqual(path.read_bytes(), previous)
        self.assertIn("different filename", self.services.warning.call_args.args[0])
        self.assertEqual(self.unrelated.read_bytes(), b"user media")

    def test_missing_source_prevents_partial_installation(self):
        self.assets.ASSET_PATHS[self.assets.ASSET_NAMES[-1]].unlink()
        self.assets.update_assets_for_profile()
        self.assertEqual(self.media.writes, [])
        self.services.warning.assert_called_once()

    def test_no_collection_does_not_write_or_warn(self):
        self.services.mw.col = None
        self.assets.update_assets_for_profile()
        self.assertEqual(self.media.writes, [])
        self.services.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
