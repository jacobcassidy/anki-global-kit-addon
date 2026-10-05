import { isAnkiPC } from '../runtime/platform.js';

/** Indent with Alt+Tab and unindent with physical Control+Tab; leave Tab to native focus navigation. */
export function handleTabIndentation(textarea, event) {
  if (event.key !== 'Tab' || event.isComposing || event.shiftKey) return;

  const controlPressed = isAnkiPC && navigator.platform.startsWith('Mac') ? event.metaKey : event.ctrlKey;
  const otherModifierPressed = isAnkiPC && navigator.platform.startsWith('Mac') ? event.ctrlKey : event.metaKey;
  if (otherModifierPressed || event.altKey === controlPressed) return;
  const outdent = controlPressed;

  const topic = document.querySelector('.topic');
  const indentation = topic && /python/i.test(topic.textContent) ? '    ' : '  ';
  if (indentLines(textarea, event, indentation, outdent)) return;

  event.preventDefault();
  event.stopPropagation();
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  textarea.setRangeText(indentation, start, end, 'end');
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
}

/** Change list levels, or remove leading whitespace from selected text lines. */
function indentLines(textarea, event, indentation, outdent) {
  const value = textarea.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const blockStart = start === 0 ? 0 : value.lastIndexOf('\n', start - 1) + 1;
  const lastPosition = end > start && value[end - 1] === '\n' ? end - 1 : end;
  const nextNewline = value.indexOf('\n', lastPosition);
  const blockEnd = nextNewline < 0 ? value.length : nextNewline;
  const edits = [];
  let lineStart = blockStart;
  // List-like text in a fenced code block should retain ordinary space insertion.
  let inCodeBlock =
    value
      .slice(0, blockStart)
      .split('\n')
      .filter((line) => /^\s*```/.test(line)).length %
      2 ===
    1;
  let hasMatchingLine = false;
  const lines = value.slice(blockStart, blockEnd).split('\n');
  const replacement = lines
    .map((line) => {
      const originalStart = lineStart;
      lineStart += line.length + 1;
      if (!outdent && /^\s*```/.test(line)) {
        inCodeBlock = !inCodeBlock;
        return line;
      }
      const list = outdent ? line.match(/^([ \t]*)/) : !inCodeBlock && line.match(/^([ \t]*)(?:[-+*]|\d+\.)[ \t]+/);
      if (!list) return line;
      hasMatchingLine = true;
      const removeLength = outdent
        ? list[1].startsWith('\t')
          ? 1
          : Math.min(list[1].match(/^ */)[0].length, indentation.length)
        : 0;
      const prefix = outdent ? '' : indentation;
      if (removeLength || prefix) edits.push({ start: originalStart, removeLength, prefix });
      return prefix + line.slice(removeLength);
    })
    .join('\n');
  if (!hasMatchingLine) return false;

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
