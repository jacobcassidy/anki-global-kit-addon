# Anki Global Kit add-on

Requires **Anki Desktop 26.05 or later**.

This add-on installs the generated JavaScript and CSS into the active Anki profile's `collection.media` folder. Anki can then sync those resources to AnkiWeb and the mobile clients.

Choose **Tools > Anki Global Kit Settings...**, open **Note Types**, and select the topics and card formats you want. Choose **Update Selected Note Types** to create new note types from the bundled card template parts, named like `CSS (Advance)` and `CSS (Cloze)`. Existing note types are left unchanged unless you select the enabled **Overwrite** checkbox beside that format. Overwriting updates the kit templates and styling while preserving existing notes and fields; custom card templates may be replaced.

## Customizing editor styles

To customize field contents, open **Tools > Anki Global Kit Settings... > Editor**. In **Editor Fields**, use **Enable custom Editor fields stylesheet** to turn your custom field CSS on or off, and click **View Stylesheet** to open `user_files`, where you can edit `editor-fields.css`. Custom field styles are enabled by default and appended after the kit defaults. Restart Anki after editing the stylesheet to reload it.

In **Editor UI**, use **Enable custom Editor UI stylesheet** to turn interface CSS on or off, and click **View Stylesheet** to open the same folder and edit `editor-ui.css`. Custom UI styles are also enabled by default. To find these files through the add-ons dialog, open **Tools > Add-ons**, select **Anki Global Kit**, and click **View Files**, then open `user_files`. The `user_files/README.txt` file is also included with the add-on.

Use **+** to add a custom topic row. To remove a custom topic row from settings, check its **Delete** box and choose **Update Selected Note Types**. This does not delete an existing Anki note type or its cards.

## Build and install for development

From the repository root, run `npm run build:addon`. Copy the `addon` folder into Anki's add-ons folder and restart Anki. On profile open, the add-on installs or refreshes the card JavaScript and CSS in that profile. In **Tools > Anki Global Kit Settings... > Note Types**, select topics and card formats, then choose **Update Selected Note Types**. Sync your collection to make the resources and note types available on your other devices.

The **Cards** settings tab controls question-input Markdown shortcuts and indentation, answer Markdown rendering and syntax highlighting, and the question formatting toolbar and its buttons. Fenced code uses an explicit language label when supplied after the opening backticks (for example, a `python` label); otherwise, syntax highlighting is inferred from the card topic. The toolbar appears above question inputs; each button tooltip lists its shortcut. The **Editor** tab controls features in Anki Desktop's note editor, including inline-code formatting, indentation, copy behavior, and paste cleanup. Card settings sync with your collection; Desktop editor settings apply in Anki Desktop.

Include the root `__init__.py`, the `desktop/` Python package, the `web/` card assets, and the `templates/` folder in published add-on packages.
