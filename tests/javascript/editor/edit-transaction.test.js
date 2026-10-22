import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';

test('reloaded edit transactions retain one field listener and only notify the latest callback', async () => {
  const dom = new JSDOM('<anki-editable contenteditable="true"><p>source</p></anki-editable>');
  const { window } = dom;
  const { document } = window;
  const field = document.querySelector('anki-editable');
  const previous = Object.fromEntries(['window', 'document', 'InputEvent'].map((key) => [key, globalThis[key]]));
  const notifications = [];
  let listeners = 0;
  const addEventListener = field.addEventListener.bind(field);

  globalThis.window = window;
  globalThis.document = document;
  globalThis.InputEvent = window.InputEvent;
  field.addEventListener = (type, ...args) => {
    if (type === 'input') listeners++;
    addEventListener(type, ...args);
  };
  document.execCommand = (_command, _ui, html) => {
    const range = window.getSelection().getRangeAt(0);

    range.deleteContents();
    range.insertNode(range.createContextualFragment(html));
    return true;
  };

  try {
    for (let version = 0; version < 3; version++) {
      const { editWithNativeUndo } = await import(
        `../../../src/editor/js/helpers/edit-transaction.js?version=${version}`
      );
      const range = document.createRange();
      const selection = window.getSelection();

      range.selectNodeContents(field.querySelector('p'));
      selection.removeAllRanges();
      selection.addRange(range);
      assert.ok(
        editWithNativeUndo(
          field,
          selection,
          (clone) => {
            clone.querySelector('p').setAttribute('data-version', version);
          },
          () => notifications.push(version),
        ),
      );
      assert.equal(field.querySelector('[data-anki-global-kit-edit-position]'), null);
    }

    assert.equal(listeners, 1);
    assert.deepEqual(notifications, [0, 1, 2]);
    field.dispatchEvent(new window.InputEvent('input', { bubbles: true }));
    assert.deepEqual(notifications, [0, 1, 2, 2]);
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
    window.close();
  }
});
