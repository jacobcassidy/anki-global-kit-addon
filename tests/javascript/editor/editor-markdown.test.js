import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { installMarkdownHighlighting, convertMarkdown } from '../../../src/editor/js/formatting/markdown.js';

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
  range.collapse(true);
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

test('Convert Markdown prefers selected text over the clipboard and replaces only that selection', () => {
  withEditor(({ field, window, document }) => {
    field.innerHTML = '<p>Keep **selected** after</p>';
    const range = document.createRange();

    range.setStart(field.firstChild.firstChild, 5);
    range.setEnd(field.firstChild.firstChild, 17);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);

    assert.equal(convertMarkdown('**clipboard**'), true);
    assert.equal(field.querySelector('b').textContent, 'selected');
    assert.equal(field.textContent, 'Keep selected after');
  });
});

test('Convert Markdown inserts clipboard text at a caret and ignores an empty clipboard', () => {
  withEditor(({ field }) => {
    assert.equal(convertMarkdown(''), false);
    assert.equal(convertMarkdown('**clipboard**'), true);
    assert.equal(field.querySelector('b').textContent, 'clipboard');
    assert.equal(field.textContent, 'clipboardreplace this');
  });
});

test('selected Markdown preserves paragraph and soft line breaks in fenced code and rejects stale results', () => {
  withEditor(({ field, window, document, getRequest }) => {
    field.innerHTML = '<div>```python</div><div>first = 1<br>second = 2</div><div>```</div>';
    const range = document.createRange();

    range.selectNodeContents(field);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);

    assert.equal(convertMarkdown('ignored clipboard'), true);
    assert.equal(getRequest().codeBlocks[0].source, 'first = 1\nsecond = 2');

    field.textContent = 'new edits';
    const request = getRequest();

    assert.equal(globalThis.ankiGlobalKitEditor.applyMarkdownHighlightResult(request.id, request.html, []), false);
    assert.equal(field.textContent, 'new edits');
  });
});

test('Convert Markdown rejects a selection spanning editor fields', () => {
  withEditor(({ field, window, document }) => {
    const other = field.cloneNode(true);

    document.body.append(other);

    const range = document.createRange();

    range.setStart(field.firstChild.firstChild, 0);
    range.setEnd(other.firstChild.firstChild, 3);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);

    assert.equal(convertMarkdown('**clipboard**'), false);
    assert.equal(field.textContent, 'replace this');
    assert.equal(other.textContent, 'replace this');
  });
});

test('Desktop Markdown submits explicit fenced code to the Pygments bridge', () => {
  withEditor(({ field, getRequest }) => {
    assert.equal(convertMarkdown('```js\nconst answer = 42;\n```'), true);
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
    convertMarkdown('```not-a-real-language\n<plain>\n```');
    const block = getRequest().codeBlocks[0];
    assert.equal(block.explicitLanguage, 'not-a-real-language');
    assert.equal(block.language, 'not-a-real-language');
    assert.equal(block.source, '<plain>');
  });
});

test('Pygments response inserts a Kit code block as one native edit', () => {
  withEditor(({ document, field, getRequest }) => {
    convertMarkdown('```python\nprint(42)\n```');
    const request = getRequest();
    const result = globalThis.ankiGlobalKitEditor.applyMarkdownHighlightResult(request.id, request.html, [
      { index: 0, language: 'python', html: '<span class="nb">print</span>(42)' },
    ]);

    assert.equal(result, true);
    assert.equal(field.querySelector('pre.global-kit-code-block').dataset.language, 'python');
    assert.equal(field.querySelectorAll('[data-language]').length, 1);
    assert.equal(field.querySelector('pre > code').attributes.length, 0);
    assert.equal(field.querySelector('code').textContent, 'print(42)');
    assert.ok(field.querySelector('code .nb'));
    assert.equal(field.querySelector('[data-global-kit-token="builtin"]').textContent, 'print');
    assert.equal(document.querySelectorAll('[data-anki-global-kit-edit-boundary]').length, 0);
  });
});
