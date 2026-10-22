import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../../addon/assets/editor/js/editor.min.js', import.meta.url), 'utf8');

test('the complete editor bundle installs formatting, copy, normalization, and cloze handlers once', () => {
  const dom = new JSDOM(
    '<body><div id="cloze"><button title="Cloze (old)"></button><button title="Cloze (old)"></button></div>' +
      '<anki-editable contenteditable="true"><b>selected</b><p>space\u00a0<code>code</code></p></anki-editable></body>',
    { runScripts: 'outside-only' },
  );
  const { window } = dom;
  const { document } = window;
  const listeners = [];
  const addEventListener = document.addEventListener.bind(document);

  Object.defineProperty(window.navigator, 'platform', { value: 'MacIntel' });
  window.requestAnimationFrame = () => 0;
  document.addEventListener = (type, ...args) => {
    listeners.push(type);
    addEventListener(type, ...args);
  };

  try {
    window.eval(bundle);

    for (const action of ['toggleBlock', 'toggleInlineCode', 'convertMarkdown', 'indent', 'unindent']) {
      assert.equal(typeof window.ankiGlobalKitEditor[action], 'function', action);
    }

    const field = document.querySelector('anki-editable');
    const range = document.createRange();

    range.selectNodeContents(field.querySelector('b'));
    window.getSelection().addRange(range);

    const clipboard = new Map();
    const copy = new window.Event('copy', { bubbles: true, cancelable: true, composed: true });

    Object.defineProperty(copy, 'clipboardData', { value: { setData: (type, value) => clipboard.set(type, value) } });
    field.dispatchEvent(copy);
    assert.equal(copy.defaultPrevented, true);
    assert.equal(clipboard.get('text/html'), '<b>selected</b>');
    assert.equal(clipboard.get('text/plain'), 'selected');

    field.dispatchEvent(new window.Event('input', { bubbles: true, composed: true }));
    assert.equal(field.querySelector('code').previousSibling.data, 'space ');

    let clozes = 0;

    document.querySelector('#cloze button').addEventListener('click', () => clozes++);
    field.dispatchEvent(
      new window.KeyboardEvent('keydown', { code: 'KeyC', ctrlKey: true, shiftKey: true, bubbles: true }),
    );
    assert.equal(clozes, 1);
    assert.equal(document.querySelector('#cloze button').title, 'Cloze (⌃⇧C)');

    const installedListeners = listeners.length;

    window.eval(bundle);
    assert.equal(listeners.length, installedListeners, 'reinjection must not duplicate document handlers');
    assert.equal(typeof window.ankiGlobalKitEditor.toggleInlineCode, 'function');
  } finally {
    window.close();
  }
});
