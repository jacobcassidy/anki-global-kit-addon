import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import {
  decorateCodeBlock,
  copyCodeToClipboard,
  installCodeBlockControls,
} from '../../../src/shared/js/syntax-highlighting/code-block-controls.js';
import { tokenHtmlByLine } from '../../../src/shared/js/syntax-highlighting/code-lines.js';
import { watchCodeBlockHeaders } from '../../../src/cards/js/syntax-highlighting/code-block-headers.js';

async function withDocument(html, callback) {
  const dom = new JSDOM(`<body>${html}</body>`);
  const keys = ['document', 'window', 'Node', 'navigator', 'MutationObserver'];
  const descriptors = Object.fromEntries(keys.map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));

  for (const key of keys) Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });

  try {
    await callback(dom.window.document, dom.window);
  } finally {
    for (const key of keys) {
      if (descriptors[key]) Object.defineProperty(globalThis, key, descriptors[key]);
      else delete globalThis[key];
    }

    dom.window.close();
  }
}

test('header labels languages, stays outside source, and respects the saved copy preference', async () => {
  await withDocument('<pre data-language="javascript"><code></code></pre>', async (document) => {
    const pre = document.querySelector('pre');
    const code = pre.querySelector('code');

    code.innerHTML = tokenHtmlByLine('<span class="k">const</span> a = "&lt;tag&gt;";\n\nlast\n', 50);
    decorateCodeBlock(pre);
    decorateCodeBlock(pre);
    assert.equal(pre.querySelectorAll('.code-block__header').length, 1);
    assert.equal(pre.querySelector('.code-block__language').textContent, 'JavaScript');
    assert.equal(pre.querySelector('.code-block__header').getAttribute('contenteditable'), 'false');
    assert.equal(code.querySelector('.k').textContent, 'const');
    assert.equal(code.querySelector('.code-block__header'), null);

    const copied = [];

    navigator.clipboard = { writeText: async (text) => copied.push(text) };
    await copyCodeToClipboard(pre);
    assert.deepEqual(copied, ['const a = "<tag>";\n\nlast\n']);
    decorateCodeBlock(pre, { copyButton: false });
    assert.equal(pre.querySelector('button').hidden, true);
    decorateCodeBlock(pre);
    assert.equal(pre.querySelector('button').hidden, true);
  });
});

test('copy falls back when clipboard permission is denied and restores focus and selection', async () => {
  await withDocument(
    '<div contenteditable="true"><pre><code>one\ntwo &lt;three&gt;</code></pre></div>',
    async (document, window) => {
      const pre = document.querySelector('pre');
      const field = document.querySelector('div');
      const range = document.createRange();

      decorateCodeBlock(pre);
      field.focus();
      range.setStart(pre.querySelector('code').firstChild, 1);
      range.setEnd(pre.querySelector('code').firstChild, 3);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
      navigator.clipboard = {
        writeText: async () => {
          throw new Error('Denied');
        },
      };
      document.execCommand = (command) => {
        assert.equal(command, 'copy');
        assert.equal(document.activeElement.value, 'one\ntwo <three>');

        return true;
      };
      await copyCodeToClipboard(pre);
      assert.equal(document.activeElement, field);
      assert.equal(window.getSelection().toString(), 'ne');
      assert.equal(document.querySelector('textarea'), null);
    },
  );
});

test('delegated copy buttons work inside shadow fields and install only once', async () => {
  await withDocument('<div id="host"></div>', async (document, window) => {
    const root = document.querySelector('#host').attachShadow({ mode: 'open' });

    root.innerHTML = '<pre data-language="python"><code></code></pre>';
    root.querySelector('code').innerHTML = tokenHtmlByLine('print(1)\n', 9);
    decorateCodeBlock(root.querySelector('pre'));
    installCodeBlockControls();
    installCodeBlockControls();

    const copied = [];

    navigator.clipboard = { writeText: async (text) => copied.push(text) };
    root.querySelector('button').dispatchEvent(new window.MouseEvent('click', { bubbles: true, composed: true }));
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.deepEqual(copied, ['print(1)\n']);
    assert.equal(root.querySelector('button').title, 'Copied');
  });
});

test('copy button refreshes its check icon and copies again while feedback is visible', async () => {
  await withDocument('<pre><code>copy me</code></pre>', async (document, window) => {
    const scheduledTimeouts = [];
    const originalSetTimeout = globalThis.setTimeout;

    globalThis.setTimeout = (callback) => {
      scheduledTimeouts.push(callback);

      return scheduledTimeouts.length;
    };

    try {
      const pre = document.querySelector('pre');

      decorateCodeBlock(pre);
      installCodeBlockControls();
      const button = pre.querySelector('.code-block__copy');
      const icon = button.querySelector('.code-block__copy-icon');
      const copied = [];

      navigator.clipboard = { writeText: async (text) => copied.push(text) };

      const clickCopy = async () => {
        button.dispatchEvent(new window.MouseEvent('click', { bubbles: true, composed: true }));
        await Promise.resolve();
        await Promise.resolve();
      };

      assert.equal(icon.querySelector('svg'), null);
      assert.equal(icon.classList.contains('code-block__copy-icon--copied'), false);
      await clickCopy();
      assert.deepEqual(copied, ['copy me']);
      assert.equal(icon.querySelector('svg') !== null, true);
      assert.equal(icon.classList.contains('code-block__copy-icon--copied'), true);

      await clickCopy();
      assert.deepEqual(copied, ['copy me', 'copy me']);
      assert.equal(scheduledTimeouts.length, 2);

      scheduledTimeouts[0]();
      assert.equal(icon.querySelector('svg') !== null, true);
      assert.equal(button.title, 'Copied');

      scheduledTimeouts[1]();
      assert.equal(icon.querySelector('svg'), null);
      assert.equal(icon.classList.contains('code-block__copy-icon--copied'), false);
      assert.equal(button.title, 'Copy Code');
    } finally {
      globalThis.setTimeout = originalSetTimeout;
    }
  });
});

test('card headers cover existing and subsequently rendered blocks without observer loops', async () => {
  await withDocument(
    '<main class="agk-container"><pre class="agk-code-block" data-language="python"><code>old</code></pre></main>',
    async (document) => {
      const observer = watchCodeBlockHeaders();

      try {
        assert.equal(document.querySelector('.code-block__language').textContent, 'Python');

        const answer = document.createElement('div');

        answer.className = 'agk-container';
        answer.innerHTML = '<pre><code class="language-js">new\nanswer</code></pre><pre><code>plain</code></pre>';
        document.body.append(answer);
        await new Promise((resolve) => setTimeout(resolve, 0));
        assert.deepEqual(
          [...document.querySelectorAll('.code-block__language')].map((node) => node.textContent),
          ['Python', 'JavaScript', 'Code'],
        );
        assert.equal(document.querySelectorAll('.code-block__header').length, 3);
        assert.equal(answer.querySelector('code').textContent, 'new\nanswer');
      } finally {
        observer.disconnect();
      }
    },
  );
});

test('empty highlighted token rows retain a caret placeholder', async () => {
  await withDocument('<pre><code></code></pre>', async (document) => {
    const code = document.querySelector('code');

    code.innerHTML = tokenHtmlByLine('<span class="s">first\n\nlast\n</span>', 1);
    assert.equal(code.querySelectorAll('[data-code-placeholder]').length, 2);
    assert.deepEqual(
      [...code.querySelectorAll('.code-line__content')].map((node) => node.textContent),
      ['first', '', 'last', ''],
    );
  });
});
