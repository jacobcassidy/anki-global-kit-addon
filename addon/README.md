# Anki Global Kit add-on

Requires **Anki Desktop 26.05 or later**.

This add-on installs the generated card JavaScript, CSS, and shared font into the active Anki profile's `collection.media` folder. Anki can then sync those resources to AnkiWeb and the mobile clients.

## Create, replace, and delete note types

Choose **Tools > Anki Global Kit Settings...**, open **Note Types**, and select the topics and card formats you want. Use **+** to add a custom topic. Kit types are named like `CSS (Advance)` and `CSS (Cloze)`.

- **Create** adds a missing note type from the bundled template parts. Existing types are left unchanged.
- **Replace** updates an existing type's kit templates and styling after explicit selection and confirmation. Notes and fields are kept, missing kit fields are added, and custom card templates may be replaced. The existing type must be standard for **Advance** or Cloze for **Cloze**.
- **Delete** removes an empty note type after confirmation, or removes an uncreated custom topic row. Types containing notes cannot be deleted here. After a Delete action, a custom topic row is removed if none of its formats remain.

Choose **Update Selected Note Types** and confirm the listed collection changes. These actions apply separately from **Save**, which applies settings. **Cancel** does not undo confirmed note type changes. Sync the collection and media afterward to make the changes available on your other devices.

## Customizing editor styles

To customize field contents, open **Tools > Anki Global Kit Settings... > Editor**. In **Editor Fields**, use **Enable custom Editor fields stylesheet** to turn your custom field CSS on or off, and click **View Stylesheet** to open `user_files`, where you can edit `editor-fields.css`. Custom field styles are enabled by default and appended after the kit defaults. Restart Anki after editing the stylesheet to reload it.

In **Editor UI**, use **Enable custom Editor UI stylesheet** to turn interface CSS on or off, and click **View Stylesheet** to open the same folder and edit `editor-ui.css`. Custom UI styles are also enabled by default. To find these files through the add-ons dialog, open **Tools > Add-ons**, select **Anki Global Kit**, and click **View Files**, then open `user_files`. The `user_files/README.txt` file is also included with the add-on.

## Build and install for development

From the repository root, install the development dependencies and build the assets:

```sh
npm install
npm run build:addon
```

Copy the `addon` folder into Anki's add-ons folder and restart Anki. On profile open, the add-on installs or refreshes the card JavaScript, CSS, and font in that profile. In **Tools > Anki Global Kit Settings... > Note Types**, select topics and card formats, then choose **Update Selected Note Types** and confirm. Sync your collection and media before reviewing on other devices.

The **Cards** settings tab controls question-input Markdown shortcuts and indentation, answer Markdown rendering and syntax highlighting, and the question formatting toolbar and its buttons. Fenced code uses an explicit language label when supplied after the opening backticks (for example, a `python` label); otherwise, syntax highlighting is inferred from the card topic. The toolbar appears above question inputs; each button tooltip lists its shortcut. The **Editor** tab controls features in Anki Desktop's note editor, including inline-code formatting, indentation, copy behavior, and paste cleanup. Card settings sync with your collection; Desktop editor settings apply in Anki Desktop.

## Package for publishing

After building, run `npm run package:addon` from the repository root. The script checks required files and asset paths before writing `dist/anki-global-kit.ankiaddon`.

The archive contains `__init__.py`, `desktop/`, `shared/`, `web/`, `templates/`, `user_files/`, `config.json`, `manifest.json`, `README.md`, `ABOUT.md`, `HELP.md`, and the canonical repository-root `CHANGELOG.md`. These paths are at the archive root, without an enclosing `addon/` folder.
