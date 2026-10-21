# Pasted list layout repair

> **Removed:** This repair is no longer part of the add-on. External rich-text
> paste cleanup remains available under **Editor → Formatting**.

Chromium can omit the final newline after a pasted list. That can leave the
caret at the end of the last list item, so subsequent typing may continue
inside that item instead of starting after the list.

The repair tracked the editor field and its existing lists immediately before
an external rich-text paste. After insertion, it inspected only newly added
lists. When a new list had the expected opening newline and ended with a list
item, it appended a newline after that item and dispatched an `input` event so
the editor recognized the change. It skipped existing lists, compact lists,
nested wrapper lists, and lists inside code or preformatted content.

For example, a pasted list ending like this:

```html
<ul>
  \n
  <li>One</li>
  \n
  <li>Two</li>
</ul>
```

was repaired to include a final newline after the last item:

```html
<ul>
  \n
  <li>One</li>
  \n
  <li>Two</li>
  \n
</ul>
```

The repair affected only the inserted list ending. It did not rewrite the
existing field contents or intentionally reposition the caret.
