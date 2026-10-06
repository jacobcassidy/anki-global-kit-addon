![Anki Global Kit logo](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/branding/anki-global-kit-logo.png)

<!-- markdownlint-disable-file MD041 -->

# Anki Global Kit

Build cards that let you type, format, and compare your answers. Anki Global Kit brings reusable card templates, Markdown formatting, code highlighting, and editor tools together in one add-on. Use it for programming, vocabulary, or your own study topics.

**Requires Anki Desktop 26.05 or later.** Set up the kit on Desktop, then sync your collection and media to use its card features in AnkiWeb, AnkiMobile, and AnkiDroid. The settings panel and editor tools run on Desktop.

## Practice with typed answers

- Write multiline answers, including code and formatted text.
- Compare your answer with the reference using character-by-character highlighting, or show the two answers side by side.
- Add hints, bonus questions, bonus answers, and notes when you need more context.
- Study with responsive layouts, topic accent colors, and light and dark themes.

These examples show a Python question with a typed answer, a bonus exercise, and notes.

### Light theme

#### Card front: question, answer inputs, and formatting toolbar

![Light theme card front with a Python question, typed answer fields, and formatting toolbar](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/card-front-light.png)

#### Card back: answers, bonus comparison, and notes

![Light theme card back showing the typed and reference answers, bonus comparison, and notes](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/card-back-light.png)

### Dark theme

#### Card front

![Dark theme card front with a Python question and typed answer fields](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/card-front-dark.png)

#### Card back

![Dark theme card back showing answers, bonus comparison, and notes](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/card-back-dark.png)

## Format Markdown and code

Use headings, lists, blockquotes, bold, italics, links, inline code, and fenced code blocks in your typed answers. Code highlighting uses the language label on a fenced block or the card's topic.

An optional toolbar and configurable keyboard shortcuts make formatting quicker. Choose the buttons and shortcuts you want, including indentation controls, in the **Cards** settings tab.

![Cards settings tab with Markdown shortcuts, indentation controls, and formatting toolbar options](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/settings-cards-tab.png)

## Create cards for your topics

Choose **Advance** for question-and-answer cards or **Cloze** for cloze-deletion cards. Built-in topics include Command Line, CSS, Git, JavaScript, PHP, Python, React, Regex, Ruby, TypeScript, Vocabulary, and WordPress. Add your own topics with **+**.

The **Note Types** tab lets you create missing kit types without assembling templates or copying files manually. Existing note types stay unchanged unless you select **Replace** and confirm. Replacement keeps notes and fields, adds missing kit fields, and may replace custom card templates. **Delete** is available only for empty note types or uncreated custom topics.

![Note Types settings tab showing topic rows and Create, Replace, and Delete options for Advance and Cloze formats](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/settings-note-types-tab.png)

## Make Desktop editing easier

- Format inline code, lists, and blockquotes with toolbar buttons or configurable shortcuts.
- Adjust indentation and clean up rich-text pastes.
- Copy source HTML and normalize spaces in inline code.
- Customize editor field and interface styles with your own stylesheets.

Choose the tools that fit your workflow in the **Editor** settings tab.

![Editor settings tab showing formatting shortcuts, paste cleanup, and custom stylesheet options](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/settings-editor-tab.png)

## Get started

1. Install the add-on through **Tools > Add-ons > Get Add-ons** using the download code on this page, then restart Anki Desktop.
2. Open **Tools > Anki Global Kit Settings... > Note Types**.
3. Select **Create** for the topics and formats you want, choose **Update Selected Note Types**, and confirm.
4. Add a note using one of the new types, such as **Python (Advance)**. Fill in **Question** and **Answer**. For Advance cards, enter `yes` in **Compare** to highlight differences, or leave it empty to display the answers separately.
5. Choose your review and editor options in **Cards** and **Editor**, then select **Save**.
6. Sync your collection and media from Desktop, then sync your other devices before reviewing there.

The add-on installs its card scripts, styles, and font automatically. After an update, restart Desktop and sync again. To apply new kit templates to existing note types, select **Replace** for those types and confirm.

## Help and feedback

Open the **Help** tab in Anki Global Kit Settings for setup guidance, or read the [user guide](https://github.com/jacobcassidy/anki-global-kit-addon/blob/main/addon/HELP.md).

![Help tab in Anki Global Kit Settings with setup guidance and troubleshooting information](https://raw.githubusercontent.com/jacobcassidy/anki-global-kit-addon/main/docs/reference/screenshots/setting-help-tab.png)

For a problem or suggestion, [open an issue](https://github.com/jacobcassidy/anki-global-kit-addon/issues) with your Anki version, device, and steps to reproduce it. You can also browse the [source code and setup guide](https://github.com/jacobcassidy/anki-global-kit-addon) or the [changelog](https://github.com/jacobcassidy/anki-global-kit-addon/blob/main/CHANGELOG.md).
