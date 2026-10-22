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

for (const mode of ['code', 'markdown']) {
  test(`${mode} results from an earlier bundle cannot replace a newer selection`, () => {
    const dom = new JSDOM('<body><anki-editable contenteditable="true"><p>first()</p></anki-editable></body>', {
      runScripts: 'outside-only',
    });
    const { window } = dom;
    const { document } = window;
    const messages = [];
    const field = document.querySelector('anki-editable');

    window.requestAnimationFrame = () => 0;
    window.ankiGlobalKitEditorSettings = { anki_editor_syntax_highlighting_languages: ['python'] };
    window.pycmd = (message) => messages.push(message);
    document.execCommand = (_command, _ui, html) => {
      const range = window.getSelection().getRangeAt(0);

      range.deleteContents();
      range.insertNode(range.createContextualFragment(html));

      return true;
    };

    const request = (source) => {
      field.querySelector('p').textContent =
        mode === 'markdown' ? `\u0060\u0060\u0060python\n${source}\n\u0060\u0060\u0060` : source;

      const range = document.createRange();

      range.selectNodeContents(field.querySelector('p'));
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);

      const api = window.ankiGlobalKitEditor;

      assert.equal(mode === 'code' ? api.highlightCode('', 'python') : api.convertMarkdown(''), true);

      return JSON.parse(messages.at(-1).slice(messages.at(-1).indexOf('{')));
    };
    const apply = (response) => {
      const api = window.ankiGlobalKitEditor;

      return mode === 'code'
        ? api.applyHighlightResult(response.id, response.source, 'python', response.source, false, 1)
        : api.applyMarkdownHighlightResult(response.id, response.html, []);
    };

    try {
      window.eval(bundle);

      const first = request('first()');

      window.eval(bundle);
      assert.equal(apply(first), false, 'reinjection invalidates earlier requests');

      const second = request('second()');
      const snapshot = field.innerHTML;

      assert.notEqual(first.id, second.id);
      assert.equal(apply(first), false, 'a stale response must not consume a newer request');
      assert.equal(field.innerHTML, snapshot);
      assert.equal(apply(second), true);
      assert.equal(field.querySelector('code').textContent, 'second()');
    } finally {
      window.close();
    }
  });
}

test('editor bundle reinjection retains one transaction listener on an existing field', () => {
  const dom = new JSDOM('<anki-editable contenteditable="true"><p>source</p></anki-editable>', {
    runScripts: 'outside-only',
  });
  const { window } = dom;
  const { document } = window;
  const field = document.querySelector('anki-editable');
  const addEventListener = field.addEventListener.bind(field);
  let listeners = 0;
  let inputs = 0;

  window.requestAnimationFrame = () => 0;
  field.addEventListener = (type, ...args) => {
    if (type === 'input') listeners++;
    addEventListener(type, ...args);
  };
  addEventListener('input', () => inputs++);
  document.execCommand = (_command, _ui, html) => {
    const range = window.getSelection().getRangeAt(0);

    range.deleteContents();
    range.insertNode(range.createContextualFragment(html));
    return true;
  };

  try {
    for (let version = 0; version < 3; version++) {
      window.eval(bundle);
      const range = document.createRange();

      range.selectNodeContents(field);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
      assert.equal(window.ankiGlobalKitEditor.toggleBlock('blockquote'), true);
    }

    assert.equal(listeners, 1);
    assert.equal(inputs, 3);
    assert.equal(field.querySelector('[data-anki-global-kit-edit-position]'), null);
  } finally {
    window.close();
  }
});
