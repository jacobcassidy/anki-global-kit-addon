import { isAnkiPC } from '../runtime/platform.js';

/** Indent list items or text with Tab; advance focus with physical Control+Tab. */
export function handleTabIndentation(textarea, event) {
  if (event.key !== 'Tab' || event.isComposing || event.altKey) return;

  const controlPressed = isAnkiPC && navigator.platform.startsWith('Mac') ? event.metaKey : event.ctrlKey;
  const otherModifierPressed = isAnkiPC && navigator.platform.startsWith('Mac') ? event.ctrlKey : event.metaKey;
  if (otherModifierPressed) return;

  if (controlPressed) {
    if (event.shiftKey) return;
    event.preventDefault();
    event.stopPropagation();
    const focusableElements = Array.from(
      document.querySelectorAll('a[href], button, input, select, textarea, [tabindex], [contenteditable="true"]'),
    ).filter((element) => {
      const style = window.getComputedStyle(element);
      return (
        !element.disabled &&
        element.tabIndex >= 0 &&
        style.visibility !== 'hidden' &&
        style.display !== 'none' &&
        element.getClientRects().length > 0
      );
    });
    const currentIndex = focusableElements.indexOf(textarea);
    const nextElement = focusableElements[currentIndex + 1];

    if (currentIndex >= 0 && nextElement) nextElement.focus();
    return;
  }

  const topic = document.querySelector('.topic');
  const indentation = topic && /python/i.test(topic.textContent) ? '    ' : '  ';
  if (indentMarkdownList(textarea, event, indentation)) return;
  if (event.shiftKey) return;

  event.preventDefault();
  event.stopPropagation();
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  textarea.setRangeText(indentation, start, end, 'end');
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
}

/** Change the leading indentation on each selected Markdown list item. */
function indentMarkdownList(textarea, event, indentation) {
  const value = textarea.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const blockStart = start === 0 ? 0 : value.lastIndexOf('\n', start - 1) + 1;
  const lastPosition = end > start && value[end - 1] === '\n' ? end - 1 : end;
  const nextNewline = value.indexOf('\n', lastPosition);
  const blockEnd = nextNewline < 0 ? value.length : nextNewline;
  const edits = [];
  let lineStart = blockStart;
  // List-like text in a fenced code block should retain ordinary Tab behavior.
  let inCodeBlock =
    value
      .slice(0, blockStart)
      .split('\n')
      .filter((line) => /^\s*```/.test(line)).length %
      2 ===
    1;
  let hasListItem = false;
  const lines = value.slice(blockStart, blockEnd).split('\n');
  const replacement = lines
    .map((line) => {
      const originalStart = lineStart;
      lineStart += line.length + 1;
      if (/^\s*```/.test(line)) {
        inCodeBlock = !inCodeBlock;
        return line;
      }
      const list = !inCodeBlock && line.match(/^([ \t]*)(?:[-+*]|\d+\.)[ \t]+/);
      if (!list) return line;
      hasListItem = true;
      const removeLength = event.shiftKey
        ? list[1].startsWith('\t')
          ? 1
          : Math.min(list[1].match(/^ */)[0].length, indentation.length)
        : 0;
      const prefix = event.shiftKey ? '' : indentation;
      if (removeLength || prefix) edits.push({ start: originalStart, removeLength, prefix });
      return prefix + line.slice(removeLength);
    })
    .join('\n');
  if (!hasListItem) return false;

  event.preventDefault();
  event.stopPropagation();
  if (!edits.length) return true;

  const mapPosition = (position) =>
    position +
    edits.reduce((offset, edit) => {
      if (position < edit.start) return offset;
      return offset + edit.prefix.length - Math.min(position - edit.start, edit.removeLength);
    }, 0);
  textarea.setRangeText(replacement, blockStart, blockEnd, 'end');
  textarea.setSelectionRange(mapPosition(start), mapPosition(end));
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  return true;
}
