"""Ensure release packaging excludes local data in the live user_files folder."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "kit_packager",
    Path(__file__).resolve().parents[3] / "scripts/package_addon.py",
)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def test_user_files_include_only_supplied_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in packager.PACKAGE_DIRECTORIES:
                (root / name).mkdir()
            for name in (
                *packager.PACKAGE_FILES,
                *packager.REQUIRED_SETTINGS_FILES,
                *packager.REQUIRED_USER_FILES,
            ):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("package default", encoding="utf-8")
            (root / "user_files/private-note.txt").write_text(
                "private data", encoding="utf-8"
            )
            (root / "user_files/backups").mkdir()
            (root / "user_files/backups/editor-fields.css").write_text(
                "local backup", encoding="utf-8"
            )
            with patch.object(packager, "ADDON_ROOT", root):
                files = packager.package_files()
                for name in packager.REQUIRED_SETTINGS_FILES:
                    self.assertIn(root / name, files)
                    path = root / name
                    path.unlink()
                    with self.assertRaises(FileNotFoundError):
                        packager.package_files()
                    path.mkdir()
                    with self.assertRaises(FileNotFoundError):
                        packager.package_files()
                    path.rmdir()
                    path.write_text("package default", encoding="utf-8")
                user_files = {
                    path.relative_to(root).as_posix()
                    for path in files
                    if path.parent == root / "user_files"
                }
                self.assertEqual(user_files, set(packager.REQUIRED_USER_FILES))
                self.assertFalse(any("backups" in path.parts for path in files))
                self.assertNotIn(root / "user_files/private-note.txt", files)
                (root / packager.REQUIRED_USER_FILES[0]).unlink()
                with self.assertRaises(FileNotFoundError):
                    packager.package_files()


if __name__ == "__main__":
    unittest.main()
