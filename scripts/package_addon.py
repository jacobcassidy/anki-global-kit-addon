"""Create an AnkiWeb archive with the repository changelog and license."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
ADDON_ROOT = REPOSITORY_ROOT / "addon"
ARCHIVE_PATH = REPOSITORY_ROOT / "dist" / "anki-global-kit.ankiaddon"
PACKAGE_FILES = (
    "__init__.py",
    "config.json",
    "manifest.json",
    "README.md",
    "ABOUT.md",
    "HELP.md",
)
PACKAGE_DIRECTORIES = (
    "desktop",
    "shared",
    "web",
    "templates",
    "user_files",
)
PACKAGE_PATHS = PACKAGE_FILES + PACKAGE_DIRECTORIES
REQUIRED_USER_FILES = (
    "user_files/README.txt",
    "user_files/editor-fields.css",
    "user_files/editor-ui.css",
)


def validate_package_paths() -> None:
    problems = [
        f"Expected file: addon/{item}"
        for item in (*PACKAGE_FILES, *REQUIRED_USER_FILES)
        if not (ADDON_ROOT / item).is_file()
    ]
    problems.extend(
        f"Expected folder: addon/{item}"
        for item in PACKAGE_DIRECTORIES
        if not (ADDON_ROOT / item).is_dir()
    )
    if problems:
        raise FileNotFoundError(
            "Cannot package Anki Global Kit: required components are missing "
            "or have the wrong file/folder type.\n" + "\n".join(problems)
        )


def package_files() -> list[Path]:
    validate_package_paths()
    files = []
    for item in PACKAGE_PATHS:
        path = ADDON_ROOT / item
        if item == "user_files":
            # A development link shares this directory with the live add-on.
            # Ship the supplied templates without collecting local user data.
            files.extend(ADDON_ROOT / name for name in REQUIRED_USER_FILES)
        elif path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                child
                for child in path.rglob("*")
                if child.is_file()
                and "__pycache__" not in child.parts
                and child.suffix != ".pyc"
                and child.name != ".DS_Store"
            )
    return sorted(files)


def main() -> None:
    if __package__:
        from .check_assets import validate_assets
        from .font_notices import write_font_notice
    else:
        from check_assets import validate_assets
        from font_notices import write_font_notice

    changelog = REPOSITORY_ROOT / "CHANGELOG.md"
    if not changelog.is_file():
        raise FileNotFoundError(f"The canonical changelog is missing: {changelog}")
    license_path = REPOSITORY_ROOT / "LICENSE"
    if not license_path.is_file():
        raise FileNotFoundError(
            f"The project license is missing or is not a file: {license_path}"
        )

    validate_package_paths()
    write_font_notice()
    files = package_files()
    print(validate_assets(files))
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(ARCHIVE_PATH, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ADDON_ROOT).as_posix())
        archive.write(changelog, "CHANGELOG.md")
        archive.write(license_path, "LICENSE")

    print(f"Created {ARCHIVE_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, SyntaxError) as error:
        raise SystemExit(str(error)) from error
