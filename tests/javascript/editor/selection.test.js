import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { getEditorRangeText } from '../../../src/editor/js/helpers/selection.js';
import { tokenHtmlByLine } from '../../../src/shared/js/syntax-highlighting/code-lines.js';
import { decorateCodeBlock } from '../../../src/shared/js/syntax-highlighting/code-block-controls.js';

function withCode(source, callback) {
  const dom = new JSDOM(
    '<anki-editable><pre class="agk-code-block" data-language="python"><code></code></pre></anki-editable>',
  );
  const previous = { document: globalThis.document, Node: globalThis.Node };

  globalThis.document = dom.window.document;
  globalThis.Node = dom.window.Node;

  try {
    const pre = document.querySelector('pre');
    const code = pre.querySelector('code');

    code.innerHTML = tokenHtmlByLine(source, 9);
    decorateCodeBlock(pre, { optionsButton: true });
    callback(pre, code);
  } finally {
    globalThis.document = previous.document;
    globalThis.Node = previous.Node;
    dom.window.close();
  }
}

for (const source of ['first()\nsecond()', '\nfirst()\n\nsecond()\n', '😀first()\nsecond()\n\n']) {
  test(`saved code selections preserve source rows and blank lines: ${JSON.stringify(source)}`, () => {
    withCode(source, (pre, code) => {
      for (const node of [code, pre]) {
        const range = document.createRange();

        range.selectNodeContents(node);
        assert.equal(getEditorRangeText(range), source);
        range.selectNode(node);
        assert.equal(getEditorRangeText(range), source);
      }
    });
  });
}

test('partial code selections preserve intervening rows and a selection ending at the next row start', () => {
  withCode('<b>first()</b>\n\n<i>second()</i>', (_pre, code) => {
    const range = document.createRange();

    range.setStart(code.querySelector('b').firstChild, 2);
    range.setEnd(code.querySelector('i').firstChild, 3);
    assert.equal(getEditorRangeText(range), 'rst()\n\nsec');
    range.setEnd(code.querySelector('i').firstChild, 0);
    assert.equal(getEditorRangeText(range), 'rst()\n\n');
  });
});

test('mixed prose and saved code omit decorations and retain block separators', () => {
  withCode('first()\nsecond()', (pre) => {
    const field = pre.parentElement;
    const range = document.createRange();

    pre.insertAdjacentHTML('beforebegin', '<p>Before</p>');
    pre.insertAdjacentHTML('afterend', '<p>After</p>');
    range.selectNodeContents(field);
    assert.equal(getEditorRangeText(range), 'Before\nfirst()\nsecond()\nAfter');

    field.innerHTML = '<p>plain<br>text</p>';
    range.selectNodeContents(field);
    assert.equal(getEditorRangeText(range), 'plain\ntext');
  });
});
