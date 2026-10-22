import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { installEditorStyles } from '../../../src/editor/js/styles.js';

test('saving empty editor styles removes previous styles from the document and field shadow roots', async () => {
  const dom = new JSDOM('<body><div id="field"></div></body>');
  const previous = {
    document: globalThis.document,
    require: globalThis.require,
    requestAnimationFrame: globalThis.requestAnimationFrame,
    ankiGlobalKitEditorStyles: globalThis.ankiGlobalKitEditorStyles,
    ankiGlobalKitStyleGeneration: globalThis.ankiGlobalKitStyleGeneration,
  };
  const shadow = dom.window.document.querySelector('#field').attachShadow({ mode: 'open' });
  const editable = dom.window.document.createElement('anki-editable');
  const richText = { element: Promise.resolve(editable) };
  let frames = [];

  shadow.append(editable);
  globalThis.document = dom.window.document;
  globalThis.requestAnimationFrame = (callback) => frames.push(callback);
  globalThis.require = () => ({
    instances: [
      { fields: [{ editingArea: { editingInputs: { subscribe: (callback) => (callback([richText]), () => {}) } } }] },
    ],
  });

  async function refresh(styles) {
    globalThis.ankiGlobalKitEditorStyles = styles;
    installEditorStyles();
    const frame = frames.pop();

    frames = [];
    await frame();
    frames = [];
  }

  try {
    await refresh({ ui: '/* packaged UI */', fields: '/* packaged fields */' });
    assert.equal(document.head.querySelector('style').textContent, '/* packaged UI */');
    assert.equal(shadow.querySelector('style').textContent, '/* packaged fields */');

    await refresh({ ui: '', fields: '' });
    assert.equal(document.head.querySelector('style'), null);
    assert.equal(shadow.querySelector('style'), null);

    await refresh({ ui: '/* custom UI */', fields: '/* custom fields */' });
    assert.equal(document.head.querySelector('style').textContent, '/* custom UI */');
    assert.equal(shadow.querySelector('style').textContent, '/* custom fields */');
    assert.equal(shadow.querySelectorAll('style').length, 1);

    let releaseField;

    richText.element = new Promise((resolve) => {
      releaseField = resolve;
    });
    globalThis.ankiGlobalKitEditorStyles = { ui: '/* old UI */', fields: '/* old fields */' };
    installEditorStyles();
    const delayedRefresh = frames.pop()();

    frames = [];
    richText.element = Promise.resolve(editable);
    await refresh({ ui: '', fields: '' });
    releaseField(editable);
    await delayedRefresh;
    assert.equal(document.head.querySelector('style'), null);
    assert.equal(shadow.querySelector('style'), null);
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }

    dom.window.close();
  }
});
