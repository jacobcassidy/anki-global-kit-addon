import { getSyntaxLanguage } from './languages.js';
import { codeOffset, textFromCode } from './code-lines.js';

const INSTALLED = Symbol.for('ankiGlobalKitCodeLineSelection');

function lineControl(event) {
  return event.composedPath().find((node) => node?.matches?.('.agk-code-block .code-line__number'));
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
  const code = start?.closest('pre.agk-code-block > code');

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

const COPY_INSTALLED = Symbol.for('ankiGlobalKitCodeCopy');
const LANGUAGE_MENU_INSTALLED = Symbol.for('ankiGlobalKitLanguageMenu');
const OPTIONS_INSTALLED = Symbol.for('ankiGlobalKitCodeOptions');
const copying = new WeakSet();
const LANGUAGE_NAMES = {
  bash: 'Bash',
  c: 'C',
  cpp: 'C++',
  csharp: 'C#',
  css: 'CSS',
  go: 'Go',
  html: 'HTML',
  java: 'Java',
  javascript: 'JavaScript',
  json: 'JSON',
  kotlin: 'Kotlin',
  markdown: 'Markdown',
  php: 'PHP',
  powershell: 'PowerShell',
  python: 'Python',
  ruby: 'Ruby',
  rust: 'Rust',
  sql: 'SQL',
  typescript: 'TypeScript',
  text: 'Plain text',
  plaintext: 'Plain text',
};

/** Add presentation outside CODE so the source never contains header text. */
export function decorateCodeBlock(pre, { copyButton, optionsButton = false } = {}) {
  const code = [...pre.children].find((node) => node.localName === 'code');

  if (!code) return;

  code.classList.add('code-block__source');
  pre.classList.add('has-header');

  if (copyButton !== undefined) pre.dataset.copyButton = String(copyButton);

  let header = [...pre.children].find((node) => node.classList.contains('code-block__header'));

  if (!header) {
    header = pre.ownerDocument.createElement('span');
    header.className = 'code-block__header';
    header.setAttribute('contenteditable', 'false');

    const label = pre.ownerDocument.createElement('span');
    const actions = pre.ownerDocument.createElement('span');
    const button = pre.ownerDocument.createElement('button');
    const icon = pre.ownerDocument.createElement('span');

    label.className = 'code-block__language';
    actions.className = 'code-block__actions';
    button.className = 'code-block__copy';
    button.type = 'button';
    button.title = 'Copy Code';
    button.setAttribute('aria-label', 'Copy Code');
    icon.className = 'code-block__copy-icon';
    icon.setAttribute('aria-hidden', 'true');
    button.append(icon);
    actions.append(button);
    header.append(label, actions);
    pre.prepend(header);
  }

  if (!header.querySelector('.code-block__actions')) {
    const actions = pre.ownerDocument.createElement('span');
    actions.className = 'code-block__actions';
    const button = header.querySelector('.code-block__copy');
    button?.after(actions);
    actions.append(button);
  }

  let optionsControl = header.querySelector('.code-block__options');

  if (optionsButton && !optionsControl) {
    optionsControl = pre.ownerDocument.createElement('button');
    const optionsIcon = pre.ownerDocument.createElement('span');

    optionsControl.className = 'code-block__options';
    optionsControl.type = 'button';
    optionsControl.title = 'Code Block Options…';
    optionsControl.setAttribute('aria-label', 'Code Block Options');
    optionsIcon.className = 'code-block__options-icon';
    optionsIcon.setAttribute('aria-hidden', 'true');
    optionsControl.append(optionsIcon);
    header.querySelector('.code-block__actions')?.append(optionsControl);
  }

  if (!optionsButton) optionsControl?.remove();

  const language =
    pre.dataset.language ||
    code.dataset.language ||
    [...code.classList].find((name) => name.startsWith('language-'))?.slice(9) ||
    '';
  const name = LANGUAGE_NAMES[getSyntaxLanguage(language) || language] || language || 'Code';
  const label = header.querySelector('.code-block__language');
  const button = header.querySelector('.code-block__copy');

  if (label.textContent !== name) label.textContent = name;

  button.hidden = pre.dataset.copyButton === 'false';
  button.title = 'Copy Code';
  button.setAttribute('aria-label', 'Copy Code');
  if (optionsControl) {
    optionsControl.title = 'Code Block Options…';
    optionsControl.setAttribute('aria-label', 'Code Block Options');
  }
}

function legacyCopy(text) {
  let active = document.activeElement;
  let selection = window.getSelection();

  while (active?.shadowRoot?.activeElement) {
    const nextSelection = active.shadowRoot.getSelection?.();

    if (nextSelection?.rangeCount) selection = nextSelection;

    active = active.shadowRoot.activeElement;
  }

  const ranges = Array.from({ length: selection?.rangeCount || 0 }, (_, index) =>
    selection.getRangeAt(index).cloneRange(),
  );

  const textarea = document.createElement('textarea');

  textarea.value = text;
  textarea.setAttribute('aria-hidden', 'true');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.append(textarea);

  try {
    textarea.focus({ preventScroll: true });
    textarea.select();

    if (!document.execCommand('copy')) throw new Error('Clipboard copy failed');
  } finally {
    textarea.remove();
    active?.focus({ preventScroll: true });
    selection?.removeAllRanges();

    for (const range of ranges) selection.addRange(range);
  }
}

export async function copyCodeToClipboard(pre) {
  const text = textFromCode([...pre.children].find((node) => node.localName === 'code'));

  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');

    await navigator.clipboard.writeText(text);
  } catch {
    legacyCopy(text);
  }
}

export function installCodeBlockControls() {
  installCodeLineSelection();

  if (!document[LANGUAGE_MENU_INSTALLED]) {
    document[LANGUAGE_MENU_INSTALLED] = true;
    document.addEventListener(
      'mousedown',
      (event) => {
        const label = event.composedPath().find((node) => node?.matches?.('.code-block__language'));

        if (label && event.button === 0) event.preventDefault();
      },
      true,
    );
    document.addEventListener(
      'click',
      (event) => {
        const label = event.composedPath().find((node) => node?.matches?.('.code-block__language'));

        if (!label) return;

        event.preventDefault();
        const pre = label.closest('pre.agk-code-block');
        const code = pre?.querySelector(':scope > code');

        if (!pre || !code) return;

        const selection = pre.getRootNode().getSelection?.() || window.getSelection();
        const range = pre.ownerDocument.createRange();

        range.selectNodeContents(code);
        selection?.removeAllRanges();
        selection?.addRange(range);

        const rect = label.getBoundingClientRect();
        globalThis.pycmd?.(
          `anki-global-kit:language-menu:${JSON.stringify([rect.left, rect.bottom, pre?.dataset.language || ''])}`,
        );
      },
      true,
    );
  }

  if (!document[OPTIONS_INSTALLED]) {
    document[OPTIONS_INSTALLED] = true;
    document.addEventListener(
      'mousedown',
      (event) => {
        if (event.composedPath().some((node) => node?.matches?.('.code-block__options'))) event.preventDefault();
      },
      true,
    );
    document.addEventListener(
      'click',
      (event) => {
        const button = event.composedPath().find((node) => node?.matches?.('.code-block__options'));

        if (!button) return;

        event.preventDefault();
        const pre = button.closest('pre.agk-code-block');
        const code = pre?.querySelector(':scope > code');

        if (!pre || !code) return;

        const selection = pre.getRootNode().getSelection?.() || window.getSelection();
        const range = pre.ownerDocument.createRange();

        range.selectNodeContents(code);
        selection?.removeAllRanges();
        selection?.addRange(range);
        globalThis.ankiGlobalKitEditor?.openCodeBlockOptions();
      },
      true,
    );
  }

  if (document[COPY_INSTALLED]) return;

  document[COPY_INSTALLED] = true;
  document.addEventListener(
    'mousedown',
    (event) => {
      if (event.composedPath().some((node) => node?.matches?.('.code-block__copy'))) event.preventDefault();
    },
    true,
  );
  document.addEventListener(
    'click',
    async (event) => {
      const button = event.composedPath().find((node) => node?.matches?.('.code-block__copy'));

      if (!button) return;

      event.preventDefault();

      if (copying.has(button)) return;

      copying.add(button);

      try {
        await copyCodeToClipboard(button.closest('pre'));
        button.title = 'Copied';
      } catch {
        button.title = 'Copy failed';
      } finally {
        copying.delete(button);
        setTimeout(() => {
          button.title = 'Copy Code';
        }, 1500);
      }
    },
    true,
  );
}
