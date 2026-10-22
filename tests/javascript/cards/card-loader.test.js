import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const loader = readFileSync(
  new URL('../../../addon/templates/note-types/parts/script/card-script.js', import.meta.url),
  'utf8',
);

test('overlapping template loaders share a single script and skip an already loaded bundle', async () => {
  const dom = new JSDOM('', { runScripts: 'outside-only' });
  const { window } = dom;

  try {
    window.eval(loader);
    const loading = window.ankiGlobalKitScriptLoading;

    window.eval(loader);
    assert.equal(window.ankiGlobalKitScriptLoading, loading);
    assert.equal(window.document.scripts.length, 1);
    window.eval('var hasMyCustomScript = true;');
    window.document.scripts[0].dispatchEvent(new window.Event('load'));
    await loading;
    window.eval(loader);
    assert.equal(window.document.scripts.length, 1);
  } finally {
    window.close();
  }
});

test('failed template script loads are removed and can be retried', async () => {
  const dom = new JSDOM('', { runScripts: 'outside-only' });
  const { window } = dom;
  const warnings = [];

  window.console.warn = (error) => warnings.push(error);

  try {
    window.eval(loader);
    const loading = window.ankiGlobalKitScriptLoading;

    window.document.scripts[0].dispatchEvent(new window.Event('error'));
    await loading;
    assert.equal(window.document.scripts.length, 0);
    assert.equal(window.ankiGlobalKitScriptLoading, null);
    assert.equal(warnings.length, 1);
    window.eval(loader);
    assert.equal(window.document.scripts.length, 1);
    window.document.scripts[0].dispatchEvent(new window.Event('load'));
    await window.ankiGlobalKitScriptLoading;
  } finally {
    window.close();
  }
});
