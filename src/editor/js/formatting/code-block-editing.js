import { getEditorSelection } from '../helpers/selection.js';
import { editWithNativeUndo } from '../helpers/edit-transaction.js';
import {
  codeOffset,
  codePointAt,
  codeCaret,
  flattenCodeLines,
  tokenHtmlByLine,
  preserveClozeMode,
} from '../../../shared/js/syntax-highlighting/code-lines.js';

import {
  installCodeBlockControls,
  selectedCodeText,
  decorateCodeBlock,
} from '../../../shared/js/syntax-highlighting/code-block-controls.js';

const INSTALLED = Symbol.for('ankiGlobalKitCodeBlockEditing');
const CODE_SELECTOR = 'pre.global-kit-code-block > code';

function selectedCode() {
  const selection = getEditorSelection();

  if (!selection?.rangeCount) return null;

  const range = selection.getRangeAt(0);
  const element = range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement;
  const code = element?.closest(CODE_SELECTOR);
  const field = code?.closest('anki-editable,[contenteditable="true"]');

  if (!field || !code.contains(range.endContainer)) return null;

  return { selection, range, code, field };
}

function replaceCode(target, start, end, text) {
  const { field, selection, code } = target;

  return editWithNativeUndo(field, selection, (_field, staged, resolve) => {
    const clone = resolve(code);
    const flat = flattenCodeLines(clone);
    const replacement = document.createRange();

    replacement.setStart(...codePointAt(flat, start));
    replacement.setEnd(...codePointAt(flat, end));
    replacement.deleteContents();
    replacement.insertNode(document.createTextNode(text));
    clone.innerHTML = tokenHtmlByLine(flat.innerHTML, Number(clone.parentElement.dataset.lineStart) || 1);

    preserveClozeMode(clone, clone.parentElement.dataset.clozeMode);
    decorateCodeBlock(clone.parentElement);

    const caret = document.createRange();

    caret.setStart(...codeCaret(clone, start + text.length));
    caret.collapse(true);
    staged.addRange(caret);
  });
}

function editCode(event) {
  if (!event.cancelable || event.isComposing || event.defaultPrevented) return;

  const target = selectedCode();

  if (!target) return;

  const { code, range } = target;
  let start = codeOffset(code, range.startContainer, range.startOffset);
  let end = codeOffset(code, range.endContainer, range.endOffset);
  let text = '';

  switch (event.inputType) {
    case 'insertParagraph':
    case 'insertLineBreak':
      text = '\n';
      break;
    case 'insertText':
    case 'insertReplacementText':
      if (event.data === null) return;

      text = event.data;
      break;
    case 'deleteContentBackward':
    case 'deleteContentForward': {
      if (start === end) {
        const source = flattenCodeLines(code).textContent;
        const boundaries = [
          0,
          ...Array.from(
            new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(source),
            ({ index, segment }) => index + segment.length,
          ),
        ];

        if (event.inputType === 'deleteContentBackward') {
          start = boundaries.filter((offset) => offset < start).at(-1) ?? start;
        } else {
          end = boundaries.find((offset) => offset > end) ?? end;
        }
      }

      break;
    }
    default: {
      // Blink supplies word/line deletion boundaries, including platform word
      // rules. Resolve them as source offsets before changing the row wrappers.
      const deletion = event.inputType.startsWith('delete') && event.getTargetRanges?.()[0];

      if (!deletion || !code.contains(deletion.startContainer) || !code.contains(deletion.endContainer)) return;

      start = codeOffset(code, deletion.startContainer, deletion.startOffset);
      end = codeOffset(code, deletion.endContainer, deletion.endOffset);
      break;
    }
  }

  // Keep Enter, joins, and pasted newlines in CODE; never let Blink split PRE
  // or merge the non-editable gutter into the editable source.
  event.preventDefault();
  replaceCode(target, start, end, text);
}

export function installCodeBlockEditing() {
  if (document[INSTALLED]) return;

  document[INSTALLED] = true;
  installCodeBlockControls();
  document.addEventListener('beforeinput', editCode, true);
  document.addEventListener(
    'focusin',
    (event) => {
      const field = event.composedPath().find((node) => node?.matches?.('anki-editable,[contenteditable="true"]'));

      // Upgrade gutters in previously saved blocks when their field is opened.
      for (const code of field?.querySelectorAll(CODE_SELECTOR) || []) {
        decorateCodeBlock(code.parentElement);

        const start = Number(code.parentElement.dataset.lineStart) || 1;

        code.querySelectorAll(':scope > .code-line').forEach((line, index) => {
          const number = line.querySelector(':scope > .code-line__number');

          if (!number) return;

          number.dataset.lineNumber = String(start + index);
          number.setAttribute('contenteditable', 'false');
          number.setAttribute('role', 'button');
          number.setAttribute('tabindex', '0');
          number.setAttribute('aria-label', `Line ${start + index}`);
          number.textContent = '';
        });
      }
    },
    true,
  );
  for (const type of ['copy', 'cut']) {
    document.addEventListener(
      type,
      (event) => {
        const target = selectedCode();
        const text = selectedCodeText(target?.selection);

        if (
          text === null ||
          !event.clipboardData ||
          target.range.collapsed ||
          !event.composedPath().includes(target.field)
        )
          return;

        event.clipboardData.setData('text/plain', text);
        event.preventDefault();

        if (type === 'cut') {
          const { code, range } = target;

          replaceCode(
            target,
            codeOffset(code, range.startContainer, range.startOffset),
            codeOffset(code, range.endContainer, range.endOffset),
            '',
          );
        }
      },
      true,
    );
  }

  document.addEventListener(
    'paste',
    (event) => {
      const target = selectedCode();

      if (!target || !event.clipboardData || event.defaultPrevented) return;

      const { code, range } = target;
      const start = codeOffset(code, range.startContainer, range.startOffset);
      const end = codeOffset(code, range.endContainer, range.endOffset);
      const text = event.clipboardData.getData('text/plain').replace(/\r\n?/g, '\n');

      event.preventDefault();
      replaceCode(target, start, end, text);
    },
    true,
  );
}
