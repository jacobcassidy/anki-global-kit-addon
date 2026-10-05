# Settings

Save applies the settings in the dialog. Cancel closes it without saving. Settings are stored in the active Anki profile; sync the collection to carry changes to other devices.

## Cards

The Cards tab controls behavior in card question fields and during reviews.

### Card Fields

- **Enable Markdown shortcuts** turns the configured formatting shortcuts on or off as a group.
- Each **Enable … shortcut** checkbox controls its individual shortcut. Click the shortcut field to record a key combination. Use its reset link to restore the default. Shortcuts require a modifier such as Ctrl, Alt, or Command; warnings identify conflicts and reserved keys.
- **Enable tab indentation** makes Tab insert indentation in question fields: four spaces for Python topics and two spaces for other topics. Shift+Tab moves to the next field.

### Card Toolbar

- **Show formatting toolbar** displays a toolbar below each question field.
- The individual button options show or hide the bold, italic, strikethrough, code block, inline code, unordered list, ordered list, and blockquote buttons.

### Card Reviews

- **Enable Markdown rendering** converts submitted Markdown answers into formatted content, including headings, lists, links, and code blocks.
- **Enable code block syntax highlighting** colors code blocks by language. A language named after the opening backticks takes precedence; otherwise, the card topic is used when possible.

## Editor

The Editor tab controls formatting tools and text handling in Anki Desktop editor fields.

### Editor Fields

- **Enable inline code shortcut** turns the inline-code keyboard shortcut on or off. Click the shortcut field to record a key combination, or use the reset link to restore its default.
- **Enable tab indentation** makes Tab insert four spaces instead of moving focus.
- **Enable custom Editor fields stylesheet** applies `user_files/editor-fields.css` after the kit defaults. **View Stylesheet** opens the folder containing the file.

### Editor Formatting

- **Clean up formatting when pasting** removes unwanted formatting while keeping useful content and structure.
- **Copy selected source HTML** includes HTML formatting on the clipboard alongside plain text when copying a selection from an editor field.
- **Normalize spaces around inline code** replaces non-breaking spaces next to inline code with regular spaces.

### Editor UI

- **Show inline code button in editor toolbar** adds an inline-code button to the Desktop editor toolbar. It formats selected text or starts an inline-code span.
- **Enable custom Editor UI stylesheet** applies `user_files/editor-ui.css` after the kit defaults. **View Stylesheet** opens the folder containing the file.

Both custom stylesheets are enabled by default. Restart Anki after editing the files to reload them.

## Note Types

The Note Types tab creates kit note types in the active profile and lets you replace or delete eligible kit note types. It does not modify existing note types unless you select **Replace**.

- **Advance** creates a standard question-and-answer note type with typed-answer comparison.
- **Cloze** creates a cloze-deletion note type.
- **Create** selects a note type to create when it does not already exist. Existing note types are left unchanged.
- **Replace** updates an existing note type with the kit templates and styling. Its notes and fields are kept, missing kit fields are added, and custom card templates may be replaced.
- **Delete** removes an empty note type. Move or delete its cards first. The help icon in a disabled Delete cell explains this requirement.
- **Topic** selects which topic-specific note type to create, replace, or delete. Use **+** to add a custom topic. Deleting a custom topic row from settings does not delete its note types or cards.
- **Update Selected Note Types** applies the checked actions after confirmation. The action reports types that were created, replaced, deleted, or left unchanged.

Deleting a note type changes the collection structure. Anki cannot merge that change with AnkiWeb, so syncing may show a conflict asking which collection to keep. On the device where you deleted the note type, choose **Upload to AnkiWeb** to keep the deletion. Then sync your other devices and choose **Download from AnkiWeb** there. This replaces their local collections with the uploaded version. Syncing before quitting may show the prompt sooner, but does not remove the required choice.

## Changelog

The Changelog tab displays release notes for the add-on.

## About

The About tab shows the add-on name, version, a short description, where settings are stored, and a link to the project repository.

## Help

The Help tab displays this guide. Use it to look up what each settings tab and option does.
