# Anki Global Kit Help

Open **Tools > Anki Global Kit Settings...** on Desktop. Use **Cards** for review tools and **Editor** for editing notes. Hover over help icons for individual setting details.

**Save** applies settings; sync to carry card changes to other devices. Editor settings apply on Desktop. **Cancel** discards unsaved settings but does not undo confirmed note type actions.

## Set up kit note types

1. Open **Note Types** and choose a topic.
2. Check **Create** under **Advance** for question-and-answer cards, or **Cloze** for cloze-deletion cards. Use **+** to add your own topic.
3. Choose **Update Selected Note Types** and confirm the changes.
4. Add a note using the new type, such as **Python (Advance)**, then sync your collection and media before reviewing on another device.

For Advance notes, fill in **Question** and **Answer**. Enter `yes` in **Compare** to highlight differences from your typed answer; leave it empty to show the answers separately. Hints, bonus questions, and notes are optional. Cloze notes use **Cloze Question** and compare the primary answer automatically.

Existing note types are checked automatically. To update their kit templates and styling, select **Replace** and confirm. Existing notes and fields are kept, but custom card templates may be replaced.

**Delete** removes empty note types or uncreated custom topics. Move or delete a type's notes first if deletion is unavailable. Note type actions apply through **Update Selected Note Types**, separately from **Save**.

After deleting a note type, Anki may require a full sync. Upload from the device where you made the deletion, then download on your other devices to keep the same collection. Sync other devices' pending changes before deleting.

## Type and format answers

Type in the card's input field, then reveal the answer to see your response and the reference.

- Select text and use a formatting toolbar button or shortcut. With no selection, word formatting applies to the word at the caret. Apply it again to remove the formatting.
- The toolbar appears above each input. Enable **Cards > Card Toolbar > Show formatting toolbar** if it is hidden. Hover over a button to see its shortcut.
- With **Enable tab indentation** on, **Tab** indents list items and **Shift+Tab** unindents them. In other text, Tab inserts four spaces for Python topics and two otherwise. Physical **Control+Tab** moves focus forward, including on macOS.

Enable **Markdown rendering** under **Card Reviews** to format submitted answers: `**bold**`, `*italic*`, and `` `inline code` ``. Surround code blocks with lines of three backticks. Add a language after the opening backticks, such as `python`, to choose highlighting; otherwise, the topic is used when possible.

Click a shortcut field and press the new combination. **Escape** cancels capture; the reset link restores the default. Enable both the Markdown shortcut group and the individual shortcut, and resolve conflict warnings before saving. On macOS, displayed Command and Control symbols identify the physical keys.

## Edit notes and customize appearance

Enable the inline-code button under **Editor UI** or its shortcut under **Editor Fields** to format a selection or word. On macOS, physical **Control+Shift+C** inserts Cloze; **Command+Shift+C** is the default inline-code shortcut. Turn paste cleanup off under **Editor Formatting** to keep original pasted formatting.

Choose **View Stylesheet** to open `user_files`. Edit `editor-fields.css` for note fields or `editor-ui.css` for the surrounding interface. Enable the corresponding stylesheet setting and restart Anki to reload edits. These files survive add-on upgrades.

## If something does not work

- **Changes are missing on another device:** save the card settings on Desktop and sync both the collection and media, then sync the other device. After updating the add-on, restart Desktop before syncing.
- **A shortcut does nothing:** check its enable switches and conflict warning. Check whether another Anki shortcut uses the same keys.
- **Answers show plain text:** enable Markdown rendering and syntax highlighting in **Card Reviews**. Check that code fences have matching opening and closing lines.
- **Cards lack the kit tools:** use a kit note type. To update an existing kit type's templates, select **Replace** in **Note Types**.

For an unresolved problem, [report an issue](https://github.com/jacobcassidy/anki-global-kit/issues) with your Anki version, device, steps to reproduce it, and a screenshot if useful.
