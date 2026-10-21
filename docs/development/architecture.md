# Desktop architecture and headless modules

`addon/__init__.py` is the installable add-on entry point. It starts `addon/desktop/bootstrap.py`, which owns Desktop startup and registers profile, editor, reviewer, and Settings behavior once. The Settings package presents controls; shared configuration, managed media, note-type operations, shortcuts, reusable Qt controls, and editor integration live in their Desktop responsibility packages.

The release defaults in `addon/config.json` are authoritative. `desktop/config/defaults.py` reads them directly, excluding `note_type_selections` from ordinary controls because that selection is persisted through the note-type service. The card bundle contains fallback values for cases where no Desktop-injected settings object exists; shortcut strings and enabled defaults match the release configuration. Desktop settings translate Qt modifier names when producing browser settings, while browser key events keep the standard Command/Control mapping.

Pure Desktop definitions and asset paths can be loaded by build tools without executing add-on startup or importing Anki and Qt. Use `scripts/addon_module_loader.py`:

```python
from scripts.addon_module_loader import load_addon_module

defaults = load_addon_module("desktop.config.defaults")
manifest = load_addon_module("desktop.media.manifest")
```

The loader creates an isolated package namespace rooted at `addon/`. It does not run `addon/__init__.py`; package initializers below the required entry point remain lightweight. Use this same loader for pure-module tests and build tooling instead of duplicating definitions or importing individual source files with custom path workarounds.

The test move relocated 10 JavaScript test files and 11 Python test files from `scripts/tests/`; the Anki stubs now live in `tests/support/`. Two Python smoke tests were added for the headless loader and startup registration, bringing the Python total to 13 test files. No existing shared source fixture needed a move.
