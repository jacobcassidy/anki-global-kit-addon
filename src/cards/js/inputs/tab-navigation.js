import { matchesMarkdownShortcut } from './markdown-shortcuts.js';

/** Handle configured indentation shortcuts; leave plain Tab to native navigation. */
export function handleTabIndentation(textarea, event, shortcuts) {
  if (event.isComposing) return false;
  const isMac = navigator.platform.startsWith('Mac');
  const configured = shortcuts ?? { increase: 'Alt+Tab', decrease: 'Control+Tab' };
  for (const [action, shortcut] of Object.entries(configured)) {
    if (!shortcut || !matchesMarkdownShortcut(event, shortcut, isMac)) continue;
    event.preventDefault();
    event.stopPropagation();
    changeTextareaIndentation(textarea, action === 'decrease');
    return true;
  }
  return false;
}

/** Shared row indentation action for toolbar buttons and keyboard shortcuts. */
export function changeTextareaIndentation(textarea, outdent = false) {
  const topic = document.querySelector('.topic');
  const indentation = topic && /python/i.test(topic.textContent) ? '    ' : '  ';
  indentLines(textarea, indentation, outdent);
}

/** Change leading indentation on every current or selected text row. */
function indentLines(textarea, indentation, outdent) {
  const value = textarea.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const blockStart = start === 0 ? 0 : value.lastIndexOf('\n', start - 1) + 1;
  const lastPosition = end > start && value[end - 1] === '\n' ? end - 1 : end;
  const nextNewline = value.indexOf('\n', lastPosition);
  const blockEnd = nextNewline < 0 ? value.length : nextNewline;
  const edits = [];
  let lineStart = blockStart;
  const lines = value.slice(blockStart, blockEnd).split('\n');
  const replacement = lines
    .map((line) => {
      const originalStart = lineStart;
      lineStart += line.length + 1;
      const whitespace = line.match(/^([ \t]*)/)[1];
      const removeLength = outdent
        ? whitespace.startsWith('\t')
          ? 1
          : Math.min(whitespace.match(/^ */)[0].length, indentation.length)
        : 0;
      const prefix = outdent ? '' : indentation;
      if (removeLength || prefix) edits.push({ start: originalStart, removeLength, prefix });
      return prefix + line.slice(removeLength);
    })
    .join('\n');

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
