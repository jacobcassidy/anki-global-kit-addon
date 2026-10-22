# Anki Global Kit Help

## Description

Developed by Jacob Cassidy • v{version}

Anki Global Kit is a collection of global features that supercharges Anki flashcards. It includes advanced input fields, Markdown formatting and rendering, card styles, and more that work across apps. It is especially useful for programming reviews, but works with other topics too.

Anki Desktop saves the kit's settings locally. Card settings are also included in the **{asset_name}** file in the active profile's **collection.media** folder and sync with the card assets. Editor settings apply to editing in Anki Desktop.

## Getting Started

Requires **Anki Desktop 26.05 or later**.

Open **Tools > Anki Global Kit Settings...** on Desktop. Use **Cards** for review tools and **Editor** for editing notes. Hover over help icons for individual setting details.

**Save** applies settings; sync to carry card changes to other devices. Editor settings apply on Desktop. **Cancel** discards unsaved settings but does not undo confirmed note type actions.

## Set Up Kit Note Types

1. Open **Note Types** and choose a topic.
2. Check **Create** under **Advance** for question-and-answer cards, or **Cloze** for cloze-deletion cards. Use **+** to add your own topic.
3. Choose **Apply Selected Changes** and confirm the changes.
4. Add a note using the new type, such as **Python (Advance)**, then sync your collection and media before reviewing on another device.

For Advance notes, fill in **Question** and **Answer**. Enter `yes` in **Compare** to highlight differences from your typed answer; leave it empty to show the answers separately. Hints, bonus questions, and notes are optional. Cloze notes use **Cloze Question** and compare the primary answer automatically.

Existing note types are checked automatically. To update their first card template and styling, select **Replace** and confirm. Existing notes and fields are kept, and missing kit fields are added. For standard note types, additional card templates and their associated cards are removed, including those cards' scheduling. Review the affected note types, additional template names, and template and card removal counts in the confirmation before proceeding. If the active collection, selected note types, affected templates, or card counts change after confirmation, the operation stops so you can review and confirm again.

**Delete** removes empty note types or uncreated custom topics. Move or delete a type's notes first if deletion is unavailable. Note type actions apply through **Apply Selected Changes**, separately from **Save**.

Custom topic headings display braces as literal text. If an existing kit topic name contains `{{…}}`, select **Replace** for its note types and confirm to apply the corrected heading, then sync the collection and media.

After deleting a note type, Anki may require a full sync. Upload from the device where you made the deletion, then download on your other devices to keep the same collection. Sync other devices' pending changes before deleting.

## Type And Format Answers

Type in the card's input field, then reveal the answer to see your response and the reference.

- Select text and use a formatting toolbar button or shortcut. With no selection, word formatting applies to the word at the caret. Apply it again to remove the formatting.
- The toolbar appears above each input. Enable **Cards > Card Toolbar > Show formatting toolbar** if it is hidden. Hover over a button to see its shortcut. Use **Shift+Tab** from the input to reach the toolbar, **Left/Right**, **Home**, or **End** to choose a button, and **Enter** or **Space** to apply it. **Escape** returns to the input.
- With **Enable Indentation shortcuts** on, **⌘+Option+.** increases indent and **⌘+Option+,** decreases indent on macOS; use **Ctrl+Alt+.** and **Ctrl+Alt+,** on Windows and Linux. Customize or disable each shortcut beneath this option. Indentation applies to the current or selected rows, using four spaces for Python topics and two otherwise. **Tab** and **Shift+Tab** move focus. The **Increase Indent** and **Decrease Indent** toolbar buttons use the same row actions. With Markdown shortcuts enabled, **Enter** continues list items; inside fenced code blocks, it inserts a normal newline.

- **Exit Code Block** uses **Alt+Enter** when the caret is at the end of a code block. Customize or disable it under **Editor > Editor Fields**.

Enable **Markdown to HTML rendering** under **Cards > Card Reviews** to format submitted answers: `**bold**`, `*italic*`, and `` `inline code` ``. Surround code blocks with lines of three backticks. Add a language after the opening backticks, such as `python`, to choose highlighting; otherwise, the topic is used when possible.

### Typed answers and comparison

Advance notes can include primary and bonus answer inputs, type hints, and notes. Cloze notes compare the primary answer automatically. For Advance notes, enter `yes` in **Compare** to display character-by-character differences beside the reference answer. **Bonus Compare** enables comparison for the bonus answer. Matching text, mistakes, and omissions are highlighted while Unicode characters remain intact. Comparison is validated with up to 10,000 characters in each answer; difficult comparisons use a one-second processing budget and may show coarser differences.

Typed responses remain available on the card back, including through AnkiDroid's review flow. On Windows/Linux Desktop and AnkiWeb, reveal an answer with **Control+Enter**; on macOS Desktop use **Command+Enter**.

### Markdown formatting details

Submitted answers support headings, paragraphs, line breaks, nested lists, blockquotes, fenced code blocks, inline code, bold, italics, strikethrough, and HTTP(S) links. Inline bold, italic, and strikethrough become `<b>`, `<i>`, and `<s>` tags. Block tags are output on separate lines with two spaces per nesting level. Headings receive a blank line before them, converted HTML has no trailing line break, and numbered lists retain their starting number, including nested lists.

Craft Markdown exports use `+ ## Heading` and `+ ### Heading` toggle lines as headings at those levels. An unmarked `+` question toggle becomes the next heading level after the latest heading (for example, an `h4` after an `h3`); other `+` items remain unordered list items.

The optional formatting toolbar appears above each review input. Each shortcut and toolbar button can be enabled individually. To use the toolbar, press **Shift+Tab** from an input, navigate with **Left/Right**, **Home**, or **End**, then press **Enter** or **Space**. **Escape** returns to the input. Word formatting applies to the selection or the word at the caret, and applying it again removes the markers.

The **Increase Indent** and **Decrease Indent** buttons appear between Numbered List and Blockquote and work independently of the shortcut switches. Markdown shortcuts continue list items with **Enter**; inside fenced code blocks, **Enter** inserts a normal newline. Bullet, numbered, and No List defaults are **Command+Option+8/9/0** on macOS and **Ctrl+Alt+8/9/0** on Windows/Linux. No List removes list markers while retaining indentation and other formatting. List conversion preserves nested indentation and list styles.

With **Enable Indentation shortcuts**, **⌘+Option+.** and **⌘+Option+,** indent and unindent on macOS; use **Ctrl+Alt+.** and **Ctrl+Alt+,** on Windows/Linux. Indentation adds four spaces for Python topics and two otherwise; decrease indent removes leading indentation. **Tab** and **Shift+Tab** retain focus navigation.

Click a shortcut field and press the new combination. **Escape** cancels capture; the reset link restores the default. Enable both the Markdown shortcut group and the individual shortcut, and resolve conflict warnings before saving. On macOS, displayed Command and Control symbols identify the physical keys.

## Edit Notes And Customize Appearance

Enable **Show custom formatting toolbar** and **Show Inline Code button** under **Editor Toolbar** or its shortcut under **Editor Fields** to format a selection or word. On macOS, physical **Control+Shift+C** inserts Cloze; **Command+Shift+C** is the default inline-code shortcut.

New code blocks start at line **1**. To use another starting number, place the caret in the block and open **Code Block Options** in the editor toolbar.

### Syntax highlighting and code blocks

Code fences use the language label after the opening backticks, such as `python`. If no label is supplied, the card topic is used when possible. Unsupported explicit labels remain plain code. Available languages include Python, JavaScript/Node, TypeScript, Java, C, C++, C#, SQL, Bash/shell, JSON, Ruby, Go, Rust, PHP, HTML, CSS, Markdown, PowerShell, and Kotlin. Under **Syntax Highlighting > Languages**, **Auto** identifies languages that also highlight typed answers during review.

Enable **Enable syntax highlighting for submitted answers** under **Cards > Card Reviews** to highlight fenced code in typed responses when revealed. Card scripts and stylesheet assets sync with collection media. Choose a theme under **Syntax Highlighting > Themes**. For existing note types, **Enable Code Styling…** adds only the syntax stylesheet import after confirmation, preserving notes, fields, templates, cards, and other styling.

The Desktop editor's **Highlight Code** action applies highlighting to selected code, with line numbers and optional cloze behavior. Its language menu and default come from **Syntax Highlighting > Languages**. Line numbers update as code changes and cannot be edited directly. Click a line number to select that line's content for copying, cutting, deleting, or replacing. Optional per-deck language memory records a language only after an explicit choice is applied successfully.

Highlighted blocks show a language header in the Desktop editor and can include a **Copy code** button there. The button copies plain text, preserving indentation and blank lines while omitting markup and line numbers. **Syntax Highlighting > Lines > Show Copy code button on new code blocks** controls new highlighted or converted blocks; existing blocks keep their saved choice. Card code blocks show only the code.

Saved highlighted blocks use `pre.global-kit-code-block` with language, line number, and cloze attributes, and `.code-line` wrappers inside the block. Updating add-on assets does not rewrite saved notes. If a block from an earlier development build does not display correctly, recreate it from source with **Highlight Code** or update its markup in Anki's HTML editor.

JavaScript and Python highlighting includes parser-based identifier colors for functions, methods, parameters, properties, classes, namespace imports, variables, and known builtins. Analysis is limited to each block and does not resolve external projects, imported libraries, or runtime types. Incomplete snippets retain basic highlighting where classification is uncertain; other languages use standard syntax highlighting. Re-highlight existing blocks to add identifier annotations.

Cassidy Dark colors declaration keywords blue, ordinary keywords red, functions and classes cyan, parameters orange, properties green, variables pink, methods and builtin functions/classes white, and builtin constants and namespaces purple. To publish changed Cassidy Dark colors, choose **Update Synced Theme**, then **Save** and sync. See the [classification architecture](../../../../../docs/development/syntax-classification.md) for extension points and limits.

### Editor formatting and shortcuts

The Desktop editor provides Inline Code, Blockquote, Highlight Code, and Markdown conversion actions, along with indentation and source HTML copying. Selected inline code can be toggled off for only the selected portion. List buttons and shortcuts change the outermost selected list level, preserving nested styles and indentation; plain indented rows become nested lists. No List removes formatting at every selected level while preserving inline formatting and unselected items. Blockquote toggles a quote at the current indentation level.

List shortcuts are **Command+Option+8/9/0** on macOS and **Ctrl+Alt+8/9/0** on Windows/Linux. Indentation defaults to **⌘+Option+.** and **⌘+Option+,** on macOS or **Ctrl+Alt+.** and **Ctrl+Alt+,** on Windows/Linux. In plain text, increase indent adds four spaces to selected rows and decrease indent removes leading indentation. **Tab** and **Shift+Tab** keep native focus navigation. Physical **Control+Shift+C** inserts Cloze on macOS, leaving **Command+Shift+C** for inline code.

**Convert Markdown to HTML** uses **Option+M** on macOS and **Alt+M** on Windows/Linux by default. It converts selected text, or inserts converted clipboard text at the caret when there is no selection. Code fences use the same rendering as Highlight Code. Configure or disable this shortcut under **Editor > Editor Fields**. Blockquote, Convert Markdown to HTML, and Inline Code share a toolbar group; Blockquote is off by default. List, blockquote, inline-code, and code-block changes support native undo and redo.

**Show custom formatting toolbar** controls the Kit editor buttons while leaving keyboard shortcuts available. **Show Syntax Highlighting button** controls Highlight Code, its language selector, and Code Block Options. Saving settings refreshes shortcuts and toolbar tooltips in open editors.

Under **Editor Styles**, the two **Enable Anki Global Kit's default … styles** options control the kit's field and UI styles. The custom stylesheet switches work independently. Saving applies these switches to open editors.

Under **Editor Styles**, choose **View custom Editor Fields stylesheet** or **View custom Editor UI stylesheet** to open `user_files`. Edit `editor-fields.css` for note fields or `editor-ui.css` for the surrounding interface. Enable the corresponding stylesheet setting and restart Anki to reload edits. These files survive add-on upgrades.

The default Editor Field and Editor UI style switches are independent, as are the custom stylesheet switches. Editor styles affect Desktop editing. Card appearance is controlled separately by note type styling and synced card assets.

Under **Syntax Highlighting > Themes**, choose **Add Syntax Styles…**, check one or more note types, then confirm once to add the syntax stylesheet to all selected types. **Select All** checks every listed type; types that already include the stylesheet are omitted. This preserves notes, fields, templates, cards, and other styling. Sync afterward to apply the styles on other devices.

## If Something Does Not Work

- **Changes are missing on another device:** save the card settings on Desktop and sync both the collection and media, then sync the other device. After updating the add-on, restart Desktop before syncing.
- **A shortcut does nothing:** check its enable switches and conflict warning. Check whether another Anki shortcut uses the same keys.
- **Answers show plain text:** enable Markdown rendering and syntax highlighting in **Cards → Card Reviews**. Check that code fences have matching opening and closing lines.
- **Cards lack the kit tools:** use a kit note type. To update an existing kit type's templates, select **Replace** in **Note Types**.

For an unresolved problem, [report an issue](https://github.com/jacobcassidy/anki-global-kit-addon/issues) with your Anki version, device, steps to reproduce it, and a screenshot if useful.
