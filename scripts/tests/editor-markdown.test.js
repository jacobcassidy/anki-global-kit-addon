import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { markdownToHtml } from '../../src/cards/js/markdown/render.js';
import { highlightMarkdownCodeBlocks } from '../../src/editor/js/formatting/markdown.js';

function withDocument(callback) {
  const dom = new JSDOM('');
  const originalDocument = globalThis.document;
  globalThis.document = dom.window.document;
  try {
    callback(dom.window.document);
  } finally {
    if (originalDocument === undefined) delete globalThis.document;
    else globalThis.document = originalDocument;
    dom.window.close();
  }
}

function highlight(markdown, topic = '') {
  return highlightMarkdownCodeBlocks(markdownToHtml(markdown), topic);
}

test('paste highlighting uses the explicit fence language and records normalized classes', () => {
  withDocument((document) => {
    const container = document.createElement('div');
    container.innerHTML = highlight('```js\nconst answer = 42;\n```', 'Python');
    const code = container.querySelector('pre > code');
    assert.equal(code.dataset.language, 'js');
    assert.ok(code.classList.contains('shigeSyntax'));
    assert.ok(code.classList.contains('language-javascript'));
    assert.ok(code.querySelector('.k'));
  });
});

test('paste highlighting falls back to the topic for missing or unsupported labels', () => {
  withDocument((document) => {
    for (const markdown of ['```\nprint(42)\n```', '```unknown\nprint(42)\n```']) {
      const container = document.createElement('div');
      container.innerHTML = highlight(markdown, 'Python');
      assert.ok(container.querySelector('code.language-python .nb'));
    }
  });
});

test('unrecognized topic leaves code plain and source text remains escaped', () => {
  withDocument((document) => {
    const plain = document.createElement('div');
    plain.innerHTML = highlight('```unknown\n<not-html>\n```', 'Unknown topic');
    assert.equal(plain.querySelector('code').className, '');
    assert.equal(plain.querySelector('code').textContent, '<not-html>');

    const highlighted = document.createElement('div');
    highlighted.innerHTML = highlight('```python\nvalue = "<tag>"\n```');
    assert.equal(highlighted.querySelector('code').textContent, 'value = "<tag>"');
    assert.equal(highlighted.querySelector('code span.s').innerHTML, '"&lt;tag&gt;"');
  });
});
