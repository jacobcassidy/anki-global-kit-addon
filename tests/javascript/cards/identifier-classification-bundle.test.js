import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../../addon/assets/cards/js/_anki-global-kit.min.js', import.meta.url), 'utf8');

for (const client of ['Desktop', 'AnkiDroid', 'AnkiWeb', 'AnkiMobile']) {
  test(`the bundled classifier annotates JavaScript and Python answers in simulated ${client}`, () => {
    const dom = new JSDOM(
      `<div id="qa"><div class="topic">JavaScript</div>
      <div class="user-answer"><div class="box__content"><pre><code data-language="javascript">function example(value) { return value.title.replace(value); }</code></pre>
      <pre><code data-language="python">def example(value):
    return str(value.title), True</code></pre></div></div></div>`,
      { runScripts: 'outside-only' },
    );

    try {
      const { window } = dom;

      // Deadline behavior is tested separately with an injected clock.
      window.performance.now = () => 0;
      window.ankiGlobalKitSettings = { card_toolbar_enabled: false };

      if (client === 'Desktop') window.pycmd = () => {};
      if (client === 'AnkiDroid') window.AnkiDroidJS = {};
      if (client === 'AnkiWeb') window.study = { drawAnswer() {} };
      window.eval(bundle);

      const blocks = [...window.document.querySelectorAll('code')];
      const annotated = (block, role) =>
        [...block.querySelectorAll(`[data-global-kit-token="${role}"]`)].map((item) => item.textContent);

      assert.deepEqual(annotated(blocks[0], 'function'), ['example']);
      assert.deepEqual(annotated(blocks[0], 'parameter'), ['value', 'value', 'value']);
      assert.deepEqual(annotated(blocks[0], 'method'), ['replace']);
      assert.deepEqual(annotated(blocks[0], 'attribute'), ['title']);
      assert.deepEqual(annotated(blocks[1], 'declaration'), ['def']);
      assert.deepEqual(annotated(blocks[1], 'builtin'), ['str']);
      assert.deepEqual(annotated(blocks[1], 'builtin-constant'), ['True']);
    } finally {
      dom.window.close();
    }
  });
}

test('both distributed scripts contain every bundled Lezer dependency notice', () => {
  const notice = readFileSync(
    new URL('../../../addon/assets/cards/js/licenses/lezer.txt', import.meta.url),
    'utf8',
  ).trimEnd();
  const editor = readFileSync(new URL('../../../addon/assets/editor/js/editor.min.js', import.meta.url), 'utf8');

  assert.ok(bundle.includes(notice));
  assert.ok(editor.includes(notice));

  for (const name of ['javascript', 'python', 'common', 'lr', 'highlight'])
    assert.ok(notice.includes(`@lezer/${name}\n`));
});
