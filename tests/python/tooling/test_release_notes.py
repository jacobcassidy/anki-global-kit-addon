"""Check release notes boundaries and refuse inconsistent release metadata."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "kit_release_notes",
    Path(__file__).resolve().parents[3] / "scripts/release_notes.py",
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseNotesTests(unittest.TestCase):
    def test_latest_release_excludes_unreleased_and_older_versions(self):
        changelog = """# Changelog

## [Unreleased]

### Added

- Future work.

## [1.1.0] - 2026-10-12

### Added

- New tool.

### Changed

- Updated defaults.

### Fixed

- Fixed a bug.

### Removed

- Removed old code.

## [1.0.0] - 2026-10-07

- Older release.
"""
        version, notes = release.latest_release(changelog)
        self.assertEqual(version, "1.1.0")
        self.assertTrue(notes.startswith("### Added\n"))
        self.assertIn("### Removed\n\n- Removed old code.", notes)
        self.assertNotIn("Future work", notes)
        self.assertNotIn("Older release", notes)

    def test_heading_inside_fenced_example_does_not_end_notes(self):
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                notes = f"### Added\n\n{fence}md\n## [9.0.0] - 2026-10-12\n{fence}\n\n- Final note.\n"
                changelog = "## [1.1.0] - 2026-10-12\n\n" + notes
                self.assertEqual(release.latest_release(changelog), ("1.1.0", notes))

    def test_missing_empty_or_invalid_latest_release_is_rejected(self):
        for changelog in (
            "## [Unreleased]\n\n- Pending.\n",
            "## [1.1.0] - 2026-10-12\n\n## [1.0.0] - 2026-10-07\n\n- Older.\n",
            "## [1.1] - 2026-10-12\n\n- Invalid version.\n",
            "## [01.1.0] - 2026-10-12\n\n- Invalid version.\n",
            "## [1.1.0] - 2026-02-30\n\n- Invalid date.\n",
            "## [1.1.0]\n\n- Missing date.\n",
        ):
            with self.subTest(changelog=changelog), self.assertRaises(ValueError):
                release.latest_release(changelog)

    def test_every_package_version_must_match_changelog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "addon").mkdir()
            metadata = {
                "package.json": {"version": "1.1.0"},
                "package-lock.json": {
                    "version": "1.1.0",
                    "packages": {"": {"version": "1.1.0"}},
                },
                "addon/manifest.json": {"version": "1.1.0"},
            }
            for name, content in metadata.items():
                (root / name).write_text(json.dumps(content), encoding="utf-8")
            release.validate_versions(root, "1.1.0")
            for name, content in metadata.items():
                with self.subTest(name=name):
                    wrong = {**content, "version": "1.0.0"}
                    (root / name).write_text(json.dumps(wrong), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        release.validate_versions(root, "1.1.0")
                    (root / name).write_text(json.dumps(content), encoding="utf-8")
            metadata["package-lock.json"]["packages"][""]["version"] = "1.0.0"
            (root / "package-lock.json").write_text(
                json.dumps(metadata["package-lock.json"]), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                release.validate_versions(root, "1.1.0")


if __name__ == "__main__":
    unittest.main()
