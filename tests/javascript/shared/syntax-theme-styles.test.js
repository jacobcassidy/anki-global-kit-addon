import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

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
