import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

test('saved Pygments markup, current blocks, and submitted answers share maintained token rules', () => {
  const fallback = readFileSync(new URL('../../../src/shared/css/generated/cassidy-dark.css', import.meta.url), 'utf8');
  const tokens =
    '<span class="mi">42</span><span class="se">\\n</span><span class="sd">docstring</span><span class="nv">variable</span><span class="n">name<span data-global-kit-token="parameter">parameter</span></span><span class="ges">strong emphasis</span>';
  const dom = new JSDOM(
    `<style>${fallback}</style><pre id="saved">${tokens}</pre><pre id="current" class="agk-code-block">${tokens}</pre><pre><code id="answer" class="syntax-highlights">${tokens}</code></pre><span id="outside" class="mi">42</span>`,
  );

  try {
    for (const id of ['saved', 'current', 'answer']) {
      const container = dom.window.document.getElementById(id);
      const check = (selector, role) =>
        assert.equal(dom.window.getComputedStyle(container.querySelector(selector)).color, `var(--agk-syntax-${role})`);

      check('.mi', 'constant');
      check('.se', 'string');
      check('.sd', 'comment');
      check('.nv', 'variable');
      check('.n', 'foreground');
      check('[data-global-kit-token]', 'parameter');
      assert.equal(dom.window.getComputedStyle(container.querySelector('.ges')).fontWeight, '700');
      assert.equal(dom.window.getComputedStyle(container.querySelector('.ges')).fontStyle, 'italic');
    }

    assert.notEqual(
      dom.window.getComputedStyle(dom.window.document.getElementById('outside')).color,
      'var(--agk-syntax-constant)',
    );
  } finally {
    dom.window.close();
  }
});

test('light and dark modes reset inherited font styles from the fallback and the other mode', () => {
  const overrides = execFileSync(
    'python3',
    [
      '-c',
      `
from copy import deepcopy
from scripts.addon_module_loader import load_addon_module
themes = load_addon_module('desktop.syntax_highlighting.themes')
light = themes.resolve_preset('cassidy-dark')
dark = deepcopy(light)
light['styles'] = {'bold': ['keyword'], 'italic': ['string']}
dark['styles'] = {'bold': ['comment'], 'italic': ['keyword']}
print(themes.generate_theme_pair_css(light, dark))
`,
    ],
    { cwd: new URL('../../../', import.meta.url), encoding: 'utf8' },
  );
  const fallback = readFileSync(new URL('../../../src/shared/css/generated/cassidy-dark.css', import.meta.url), 'utf8');
  const dom = new JSDOM(`<style>${fallback}\n${overrides}</style>`);
  const { document } = dom.window;
  const root = document.documentElement;
  const check = (role, weight, style) => {
    const computed = dom.window.getComputedStyle(root);

    assert.equal(computed.getPropertyValue(`--agk-syntax-${role}-weight`).trim(), weight);
    assert.equal(computed.getPropertyValue(`--agk-syntax-${role}-style`).trim(), style);
  };

  try {
    for (const dark of [false, true, false]) {
      root.classList.toggle('nightMode', dark);
      check('keyword', dark ? '400' : '700', dark ? 'italic' : 'normal');
      check('comment', dark ? '700' : '400', 'normal');
      check('string', '400', dark ? 'normal' : 'italic');
    }
  } finally {
    dom.window.close();
  }
});
