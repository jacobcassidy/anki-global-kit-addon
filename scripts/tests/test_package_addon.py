"""Ensure release packaging excludes local data in the live user_files folder."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "kit_packager", Path(__file__).resolve().parents[1] / "package_addon.py",
)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def test_user_files_include_only_supplied_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in packager.PACKAGE_DIRECTORIES:
                (root / name).mkdir()
            for name in (*packager.PACKAGE_FILES, *packager.REQUIRED_USER_FILES):
                (root / name).write_text("package default", encoding="utf-8")
            (root / "user_files/private-note.txt").write_text("private data", encoding="utf-8")
            (root / "user_files/backups").mkdir()
            (root / "user_files/backups/editor-fields.css").write_text("local backup", encoding="utf-8")
            with patch.object(packager, "ADDON_ROOT", root):
                files = packager.package_files()
                user_files = {
                    path.relative_to(root).as_posix()
                    for path in files if path.parent == root / "user_files"
                }
                self.assertEqual(user_files, set(packager.REQUIRED_USER_FILES))
                self.assertFalse(any("backups" in path.parts for path in files))
                self.assertNotIn(root / "user_files/private-note.txt", files)
                (root / packager.REQUIRED_USER_FILES[0]).unlink()
                with self.assertRaises(FileNotFoundError):
                    packager.package_files()


if __name__ == "__main__":
    unittest.main()
