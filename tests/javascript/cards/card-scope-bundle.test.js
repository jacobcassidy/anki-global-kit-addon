import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../../addon/assets/cards/js/_anki-global-kit.min.js', import.meta.url), 'utf8');

for (const client of ['Desktop', 'AnkiDroid', 'AnkiWeb', 'AnkiMobile']) {
  test(`code header observers leave unrelated cards untouched in ${client}`, async () => {
    const kit = '<main class="agk-container"><pre><code>kit code</code></pre></main>';
    const ordinary = '<pre id="ordinary"><code>ordinary code</code></pre>';
    const dom = new JSDOM(`<div id="qa">${kit}${ordinary}</div>`, { runScripts: 'outside-only' });
    const { window } = dom;
    const { document } = window;

    window.ankiGlobalKitSettings = { card_review_syntax_highlighting: false };

    if (client === 'Desktop') window.pycmd = () => {};
    if (client === 'AnkiDroid') window.AnkiDroidJS = {};
    if (client === 'AnkiWeb') window.study = { drawAnswer() {} };

    const show = async (html) => {
      if (client === 'AnkiDroid') document.body.innerHTML = `<div id="qa">${html}</div>`;
      else document.getElementById('qa').innerHTML = html;

      await new Promise((resolve) => window.setTimeout(resolve, 0));
    };
    const assertOrdinary = () => {
      assert.equal(document.querySelector('#ordinary').outerHTML, ordinary);
    };

    try {
      window.eval(bundle);
      assert.ok(document.querySelector('.agk-container .code-block__header'));
      assertOrdinary();
      await show(ordinary);
      assertOrdinary();
      window.eval(bundle);
      assertOrdinary();

      const extra = document.createElement('div');

      extra.innerHTML = '<pre><code>inserted ordinary code</code></pre>';
      document.querySelector('#qa').append(extra);
      await new Promise((resolve) => window.setTimeout(resolve, 0));
      assert.equal(document.querySelector('.code-block__header'), null);

      await show(kit + ordinary);
      assert.ok(document.querySelector('.agk-container .code-block__header'));
      assertOrdinary();

      const code = document.querySelector('.agk-container code');

      code.append(document.createElement('span'));
      await new Promise((resolve) => window.setTimeout(resolve, 0));
      assert.equal(document.querySelectorAll('.code-block__header').length, 1);
    } finally {
      window.close();
    }
  });
}

for (const client of ['Desktop', 'AnkiDroid', 'AnkiWeb', 'AnkiMobile']) {
  test(`card features ignore colliding classes outside Kit containers in ${client}`, async () => {
    const unrelated =
      '<input id="other"><div class="topic">Python</div><div class="question-container">ordinary</div><textarea class="question-input"></textarea><div class="answer-container">ordinary</div><div class="notes-container">ordinary</div><div class="user-answer"><div class="box__content"><pre><code>print(1)</code></pre></div></div>';
    const kit =
      '<main class="agk-container"><div class="topic">Python</div><textarea id="kit-input" class="question-input"></textarea></main>';
    const dom = new JSDOM(`<div id="qa">${unrelated}${kit}</div>`, { runScripts: 'outside-only' });
    const { window } = dom;
    const { document } = window;
    const errors = [];

    window.addEventListener('error', (event) => errors.push(event.error));
    if (client === 'Desktop') window.pycmd = () => {};
    if (client === 'AnkiDroid') window.AnkiDroidJS = {};
    if (client === 'AnkiWeb') window.study = { drawAnswer() {} };

    try {
      window.eval(bundle);
      assert.equal(document.activeElement.id, 'kit-input');
      assert.equal(document.querySelectorAll('.card-formatting-toolbar').length, 1);
      assert.equal(document.querySelector('.user-answer code').innerHTML, 'print(1)');
      if (client === 'AnkiDroid') document.body.innerHTML = `<div id="qa">${unrelated}</div>`;
      else document.getElementById('qa').innerHTML = unrelated;

      await new Promise((resolve) => window.setTimeout(resolve, 0));
      assert.equal(document.getElementById('qa').innerHTML, unrelated);
      assert.equal(document.activeElement, document.body);
      window.eval(bundle);
      await new Promise((resolve) => window.setTimeout(resolve, 0));
      assert.equal(document.getElementById('qa').innerHTML, unrelated);
      assert.equal(document.activeElement, document.body);
      assert.deepEqual(errors, []);
    } finally {
      window.close();
    }
  });
}
