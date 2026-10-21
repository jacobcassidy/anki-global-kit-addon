import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { installMarkdownHighlighting, pasteMarkdownAsHtml } from '../../../src/editor/js/formatting/markdown.js';

function withEditor(callback) {
  const dom = new JSDOM('<body><anki-editable contenteditable="true"><p>replace this</p></anki-editable></body>');
  const previous = Object.fromEntries(
    ['document', 'window', 'Node', 'InputEvent', 'pycmd', 'require', 'ankiGlobalKitEditor'].map((key) => [
      key,
      globalThis[key],
    ]),
  );
  const { document, window } = dom.window;
  globalThis.document = document;
  globalThis.window = window;
  globalThis.Node = window.Node;
  globalThis.InputEvent = window.InputEvent;
  globalThis.ankiGlobalKitEditor = {};
  let request;
  globalThis.pycmd = (message) => {
    request = JSON.parse(message.slice(message.indexOf('{')));
  };
  installMarkdownHighlighting();

  const field = document.querySelector('anki-editable');
  const range = document.createRange();
  range.selectNodeContents(field.querySelector('p'));
  window.getSelection().addRange(range);
  document.execCommand = (_command, _ui, html) => {
    const insertion = window.getSelection().getRangeAt(0);
    insertion.deleteContents();
    insertion.insertNode(insertion.createContextualFragment(html));
    return true;
  };

  try {
    callback({ document, window, field, getRequest: () => request });
  } finally {
    dom.window.close();
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
  }
}

test('Desktop Markdown submits explicit fenced code to the Pygments bridge', () => {
  withEditor(({ field, getRequest }) => {
    assert.equal(pasteMarkdownAsHtml('```js\nconst answer = 42;\n```'), true);
    assert.equal(field.textContent, 'replace this');
    const request = getRequest();
    assert.equal(request.codeBlocks[0].source, 'const answer = 42;');
    assert.equal(request.codeBlocks[0].explicitLanguage, 'js');
    assert.equal(request.codeBlocks[0].language, 'js');
  });
});

test('explicit unsupported Markdown labels are preserved without topic fallback', () => {
  withEditor(({ getRequest }) => {
    globalThis.require = () => ({
      instances: [{ fields: [{ name: 'Topic', editingArea: { content: { subscribe: (fn) => fn('Python') } } }] }],
    });
    pasteMarkdownAsHtml('```not-a-real-language\n<plain>\n```');
    const block = getRequest().codeBlocks[0];
    assert.equal(block.explicitLanguage, 'not-a-real-language');
    assert.equal(block.language, 'not-a-real-language');
    assert.equal(block.source, '<plain>');
  });
});

test('Pygments response inserts a Kit code block as one native edit', () => {
  withEditor(({ document, field, getRequest }) => {
    pasteMarkdownAsHtml('```python\nprint(42)\n```');
    const request = getRequest();
    const result = globalThis.ankiGlobalKitEditor.applyMarkdownHighlightResult(request.id, request.html, [
      { index: 0, language: 'python', html: '<span class="nb">print</span>(42)' },
    ]);

    assert.equal(result, true);
    assert.equal(field.querySelector('pre.agk-code-block').dataset.language, 'python');
    assert.equal(field.querySelector('code').textContent, 'print(42)');
    assert.ok(field.querySelector('code .nb'));
    assert.equal(document.querySelectorAll('[data-anki-global-kit-edit-boundary]').length, 0);
  });
});
