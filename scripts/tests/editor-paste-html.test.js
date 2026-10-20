import assert from 'node:assert/strict';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { buildSync } from 'esbuild';
import { JSDOM } from 'jsdom';

const bundle = buildSync({
  entryPoints: [fileURLToPath(new URL('../../src/editor/js/index.js', import.meta.url))],
  bundle: true,
  format: 'iife',
  write: false,
}).outputFiles[0].text;

function editor(t, { html = '<br>', mac = false } = {}) {
  const dom = new JSDOM('<div id="host"></div><button data-command="anki_global_kit_paste_html">Paste</button>', {
    runScripts: 'outside-only',
    pretendToBeVisual: true,
  });
  t.after(() => dom.window.close());
  const { window } = dom;
  const { document } = window;
  Object.defineProperty(window.navigator, 'platform', { value: mac ? 'MacIntel' : 'Linux' });
  const host = document.querySelector('#host');
  const root = host.attachShadow({ mode: 'open' });
  root.innerHTML = `<anki-editable contenteditable="true" tabindex="0">${html}</anki-editable>`;
  const field = root.firstChild;
  let range = document.createRange();
  range.selectNodeContents(field);
  range.collapse(false);
  const selection = {
    rangeCount: 1,
    get focusNode() {
      return range.endContainer;
    },
    getRangeAt: () => range,
    removeAllRanges() {},
    addRange(value) {
      range = value;
    },
  };
  root.getSelection = () => selection;
  const edits = [];
  document.execCommand = (command, _, value) => {
    assert.equal(command, 'insertHTML');
    assert.equal(root.activeElement, field);
    edits.push({ before: field.innerHTML, value });
    field.innerHTML = value;
    field.dispatchEvent(new window.InputEvent('input', { bubbles: true, composed: true }));
    return true;
  };
  window.eval(bundle);
  field.focus();
  return { window, document, host, field, selection, edits, button: document.querySelector('button') };
}

test('HTML paste survives bundle reinjection and toolbar focus in an Anki shadow field', (t) => {
  const { window, field, button, selection, edits } = editor(t);
  window.eval(bundle);
  window.eval(bundle);
  button.focus();
  let inputs = 0;
  field.addEventListener('input', () => {
    inputs += 1;
  });
  assert.equal(
    window.ankiGlobalKitEditor.pasteHtml(
      '<!doctype html><html><head><title>ignored</title></head><body>\n<h1>Hello</h1>\n<p><b>world</b></p>\n</body></html>',
    ),
    true,
  );
  assert.equal(field.innerHTML, '<h1>Hello</h1><p><b>world</b></p>');
  assert.equal(edits.length, 1);
  assert.equal(inputs, 1);
  assert.equal(selection.getRangeAt(0).collapsed, true);
  assert.equal(selection.getRangeAt(0).startContainer, field);
  assert.equal(selection.getRangeAt(0).startOffset, field.childNodes.length);
});

test('HTML paste replaces only the selection and preserves inline spaces', (t) => {
  const { window, field, selection, edits } = editor(t, { html: 'before replace after' });
  const range = selection.getRangeAt(0);
  range.setStart(field.firstChild, 7);
  range.setEnd(field.firstChild, 14);
  assert.equal(window.ankiGlobalKitEditor.pasteHtml('<b>one</b> <i>two</i>'), true);
  assert.equal(field.innerHTML, 'before <b>one</b> <i>two</i> after');
  assert.equal(edits.length, 1);
});

test('empty clipboard and removed fields do not change content', (t) => {
  const { window, field, host, button, edits } = editor(t, { html: 'keep me' });
  field.getRootNode().getSelection().getRangeAt(0).selectNodeContents(field);
  assert.equal(window.ankiGlobalKitEditor.pasteHtml(''), false);
  assert.equal(field.textContent, 'keep me');
  host.remove();
  button.focus();
  assert.equal(window.ankiGlobalKitEditor.pasteHtml('<b>ignore</b>'), false);
  assert.equal(edits.length, 0);
});

for (const mac of [false, true]) {
  test(`HTML paste shortcut blocks ordinary paste and invokes the button once (${mac ? 'macOS' : 'Windows/Linux'})`, (t) => {
    const { window, field, button, edits } = editor(t, { mac });
    window.eval(bundle);
    let clicks = 0;
    button.addEventListener('click', () => {
      clicks += 1;
      window.ankiGlobalKitEditor.pasteHtml('<strong>formatted</strong>');
    });
    let ordinaryPaste = 0;
    field.addEventListener('keydown', () => {
      ordinaryPaste += 1;
    });
    const key = new window.KeyboardEvent('keydown', {
      key: mac ? '√' : 'v',
      code: 'KeyV',
      metaKey: mac,
      ctrlKey: !mac,
      altKey: true,
      bubbles: true,
      composed: true,
      cancelable: true,
    });
    field.dispatchEvent(key);
    assert.equal(key.defaultPrevented, true);
    assert.equal(ordinaryPaste, 0);
    assert.equal(clicks, 1);
    assert.equal(edits.length, 1);
    assert.equal(field.innerHTML, '<strong>formatted</strong>');
  });
}

test('ordinary paste, composition, and shortcuts outside a formatted field stay available', (t) => {
  const { window, document, field, button } = editor(t, { mac: true });
  let clicks = 0;
  button.addEventListener('click', () => {
    clicks += 1;
  });
  for (const [target, overrides] of [
    [field, { altKey: false }],
    [field, { shiftKey: true }],
    [field, { isComposing: true }],
    [document.body, {}],
  ]) {
    const key = new window.KeyboardEvent('keydown', {
      key: 'v',
      code: 'KeyV',
      metaKey: true,
      altKey: true,
      bubbles: true,
      composed: true,
      cancelable: true,
      ...overrides,
    });
    target.dispatchEvent(key);
    assert.equal(key.defaultPrevented, false);
  }
  assert.equal(clicks, 0);
});
