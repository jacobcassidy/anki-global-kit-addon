import { codeOffset, textFromCode } from './code-lines.js';

const INSTALLED = Symbol.for('ankiGlobalKitCodeLineSelection');

function lineControl(event) {
  return event.composedPath().find((node) => node?.matches?.('.global-kit-code-block .code-line__number'));
}

function selectLine(number) {
  const content = number.parentElement.querySelector('.code-line__content');

  if (!content) return;

  const field = number.closest('anki-editable,[contenteditable="true"]');

  field?.focus({ preventScroll: true });

  const selection = number.getRootNode().getSelection?.() || window.getSelection();
  const range = number.ownerDocument.createRange();

  range.selectNodeContents(content);
  selection.removeAllRanges();
  selection.addRange(range);
}

export function selectedCodeText(selection) {
  if (!selection?.rangeCount) return null;

  const range = selection.getRangeAt(0);
  const start = range.startContainer.nodeType === 1 ? range.startContainer : range.startContainer.parentElement;
  const code = start?.closest('pre.global-kit-code-block > code');

  if (!code || !code.contains(range.endContainer)) return null;

  return textFromCode(code).slice(
    codeOffset(code, range.startContainer, range.startOffset),
    codeOffset(code, range.endContainer, range.endOffset),
  );
}

export function installCodeLineSelection() {
  if (document[INSTALLED]) return;

  document[INSTALLED] = true;

  for (const type of ['mousedown', 'click', 'keydown']) {
    document.addEventListener(
      type,
      (event) => {
        const number = lineControl(event);

        if (!number || (type === 'mousedown' && event.button !== 0)) return;
        if (type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;

        event.preventDefault();
        selectLine(number);
      },
      true,
    );
  }
}
