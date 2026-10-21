import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { highlightReviewCode, reviewLanguageAliases } from '../../../src/cards/js/syntax-highlighting/engine.js';
import { getSyntaxLanguage } from '../../../src/shared/js/syntax-highlighting/languages.js';

test('review highlighting uses explicit bundled grammars and escapes source', () => {
  const highlighted = highlightReviewCode("print('<tag>')", 'py');

  assert.match(highlighted, /hljs-built_in/);
  assert.match(highlighted, /&lt;tag&gt;/);
  assert.equal(highlightReviewCode('source', 'unknown-language'), null);
  assert.equal(reviewLanguageAliases.html, 'html');
});

test('topic language matching recognizes planned aliases without autodetection', () => {
  assert.equal(getSyntaxLanguage('C++ notes'), 'cpp');
  assert.equal(getSyntaxLanguage('C#'), 'csharp');
  assert.equal(getSyntaxLanguage('JavaScript'), 'javascript');
  assert.equal(getSyntaxLanguage('a Pythonic example'), null);
  assert.equal(getSyntaxLanguage('unlabeled source'), null);
});

test('review highlighting enforces per-block, per-answer, and block-count budgets', async () => {
  const dom = new JSDOM('<body></body>');
  const previous = {
    document: globalThis.document,
    Element: globalThis.Element,
    MutationObserver: globalThis.MutationObserver,
    ankiGlobalKitSettings: globalThis.ankiGlobalKitSettings,
  };
  globalThis.document = dom.window.document;
  globalThis.Element = dom.window.Element;
  globalThis.MutationObserver = dom.window.MutationObserver;
  globalThis.ankiGlobalKitSettings = { card_review_syntax_highlighting: true };
  const { watchSubmittedCodeBlocks } = await import(
    `../../../src/cards/js/syntax-highlighting/index.js?review-budget=${Date.now()}`
  );

  const answer = (blocks) => {
    document.body.innerHTML = `<div class="user-answer"><div class="box__content">${blocks}</div></div>`;
    watchSubmittedCodeBlocks()?.disconnect();
    return [...document.querySelectorAll('.box__content code')];
  };
  const code = (source) => `<pre><code data-language="python">${source}</code></pre>`;

  try {
    let blocks = answer(code('x'.repeat(10_001)) + code('print(1)'));
    assert.equal(blocks[0].dataset.syntaxHighlighted, undefined);
    assert.equal(blocks[1].dataset.syntaxHighlighted, 'true');

    blocks = answer(code('x'.repeat(10_000)) + code('x'.repeat(10_000)) + code('x'));
    assert.equal(blocks[0].dataset.syntaxHighlighted, 'true');
    assert.equal(blocks[1].dataset.syntaxHighlighted, 'true');
    assert.equal(blocks[2].dataset.syntaxHighlighted, undefined);

    blocks = answer(Array.from({ length: 21 }, () => code('x')).join(''));
    assert.equal(blocks.filter((block) => block.dataset.syntaxHighlighted === 'true').length, 20);
    assert.equal(blocks[20].dataset.syntaxHighlighted, undefined);
  } finally {
    dom.window.close();
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
  }
});
