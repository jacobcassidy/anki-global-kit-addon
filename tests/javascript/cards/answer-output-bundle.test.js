import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../../addon/assets/cards/js/_anki-global-kit.min.js', import.meta.url), 'utf8');

for (const client of ['Desktop', 'AnkiDroid', 'AnkiWeb', 'AnkiMobile']) {
  for (const markdown of [true, false]) {
    test(`plain answer output in ${client} preserves text with Markdown ${markdown ? 'enabled' : 'disabled'}`, async () => {
      const dom = new JSDOM('<div id="qa"><textarea class="question-input"></textarea></div>', {
        runScripts: 'outside-only',
        url: 'https://example.test/',
      });
      const { window } = dom;
      const { document } = window;

      Object.defineProperty(window.HTMLElement.prototype, 'innerText', {
        get() {
          return this.textContent;
        },
      });
      window.ankiGlobalKitSettings = {
        card_toolbar_enabled: false,
        card_review_syntax_highlighting: false,
        card_review_markdown_rendering: markdown,
      };

      if (client === 'Desktop') window.pycmd = () => {};
      if (client === 'AnkiDroid') window.AnkiDroidJS = {};
      if (client === 'AnkiWeb') window.study = { drawAnswer() {} };

      try {
        window.eval(bundle);

        const input = document.querySelector('textarea');

        input.value = '**bold**\n<unsafe>';
        input.dispatchEvent(new window.Event('input'));

        const back =
          '<main class="agk-container"><section class="answer-container is-primary">' +
          '<div class="reference-answer"><div class="box__content">Reference</div></div>' +
          '<div class="user-answer"><div class="box__content"></div></div></section></main>';

        if (client === 'AnkiDroid') document.body.innerHTML = `<div id="qa">${back}</div>`;
        else document.getElementById('qa').innerHTML = back;

        await new Promise((resolve) => window.setTimeout(resolve, 0));

        const output = document.querySelector('.user-answer .box__content');

        assert.equal(output.querySelector('unsafe'), null);
        assert.equal(output.querySelector('b')?.textContent, markdown ? 'bold' : undefined);
        assert.equal(output.textContent.includes('<unsafe>'), true);

        if (!markdown) assert.equal(output.innerHTML, '**bold**<br>&lt;unsafe&gt;');

        const rendered = output.innerHTML;

        document.body.append(document.createElement('span'));
        document.getElementById('qa').append(document.createElement('span'));
        await new Promise((resolve) => window.setTimeout(resolve, 0));
        assert.equal(output.innerHTML, rendered, 'observer reruns must preserve the rendered answer');
      } finally {
        window.close();
      }
    });
  }
}
