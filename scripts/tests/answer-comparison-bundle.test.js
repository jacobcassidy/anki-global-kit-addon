import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../addon/web/assets/js/_anki-global-kit.min.js', import.meta.url), 'utf8');

for (const client of ['Desktop', 'AnkiDroid', 'AnkiWeb', 'AnkiMobile']) {
  test(`bundled comparison renders a 10,000-character answer and bonus answer in simulated ${client}`, async () => {
    const dom = new JSDOM(
      '<div id="qa"><textarea class="question-input"></textarea><textarea class="question-input"></textarea></div>',
      {
        runScripts: 'outside-only',
        url: 'https://example.test/',
      },
    );
    try {
      const { window } = dom;
      const { document } = window;
      // jsdom has no layout/innerText implementation; these fixtures use plain
      // text, so textContent supplies the rendered-text input to comparison.
      Object.defineProperty(window.HTMLElement.prototype, 'innerText', {
        get() {
          return this.textContent;
        },
        set(value) {
          this.textContent = value;
        },
      });
      window.ankiGlobalKitSettings = { card_toolbar_enabled: false, card_review_syntax_highlighting: false };
      if (client === 'Desktop') window.pycmd = () => {};
      if (client === 'AnkiDroid') window.AnkiDroidJS = {};
      if (client === 'AnkiWeb') window.study = { drawAnswer() {} };
      window.eval(bundle);
      const expected = 'a'.repeat(10_000);
      const typed = 'a'.repeat(5000) + 'b' + 'a'.repeat(4999);
      const inputs = [...document.querySelectorAll('textarea')];
      for (const [index, answer] of [typed, '😃b'].entries()) {
        inputs[index].value = answer;
        inputs[index].dispatchEvent(new window.Event('input'));
      }
      const back = `<div class="global-kit-container">
        <div class="answer-container is-primary">
          <div class="reference-answer"><div class="box__content">${expected}</div></div>
          <div class="user-answer"><div class="box__content" data-compare="yes"></div></div>
        </div>
        <div class="answer-container">
          <div class="is-bonus"><div class="question">Bonus</div></div>
          <div class="reference-answer"><div class="box__content">😀b</div></div>
          <div class="user-answer"><div class="box__content" data-compare="yes"></div></div>
        </div>
      </div>`;
      // AnkiDroid observes replacement of body children; other clients observe #qa.
      if (client === 'AnkiDroid') document.body.innerHTML = `<div id="qa">${back}</div>`;
      else document.getElementById('qa').innerHTML = back;
      await new Promise((resolve) => window.setTimeout(resolve, 0));

      const comparisons = [...document.querySelectorAll('.comparison')];
      assert.equal(comparisons.length, 2);
      assert.equal(comparisons[0].querySelectorAll('.typeGood').length, 19_998);
      assert.equal(comparisons[0].querySelector('.typeBad').textContent, 'b');
      assert.equal(comparisons[0].querySelector('.typeMissed').textContent, 'a');
      assert.equal(comparisons[1].querySelector('.typeBad').textContent, '😃');
      assert.equal(comparisons[1].querySelector('.typeMissed').textContent, '😀');
      assert.equal(comparisons[1].querySelectorAll('.typeGood').length, 2);
      assert.equal(window.diff_match_patch, undefined, 'comparison must not depend on a separate global library');
      window.eval(bundle);
      assert.equal(
        document.querySelectorAll('.comparison').length,
        2,
        'reinitialization must preserve the comparisons',
      );
    } finally {
      dom.window.close();
    }
  });
}

test('the card media bundle includes the complete comparison-engine license', () => {
  const notice = readFileSync(
    new URL('../../addon/web/assets/js/licenses/diff-match-patch.txt', import.meta.url),
    'utf8',
  );
  assert.ok(bundle.includes(notice.trimEnd()));
});
