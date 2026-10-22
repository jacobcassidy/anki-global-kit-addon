import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { getEditorFields, getEditorTopicText, readStoreValue } from '../../../src/editor/js/helpers/fields.js';

test('reading a store returns its current value and unsubscribes immediately', () => {
  let subscriptions = 0;
  const store = {
    subscribe(callback) {
      subscriptions++;
      callback('current');

      return () => subscriptions--;
    },
  };

  assert.equal(readStoreValue(store), 'current');
  assert.equal(subscriptions, 0);
  assert.equal(readStoreValue(undefined), undefined);
});

test('Topic lookup supports editor metadata shapes and safely handles missing fields', () => {
  const dom = new JSDOM();
  const previousDocument = globalThis.document;
  const previousRequire = globalThis.require;
  let fields;

  globalThis.document = dom.window.document;
  globalThis.require = (name) => {
    assert.equal(name, 'anki/NoteEditor');

    return { instances: [{ fields }] };
  };

  try {
    assert.deepEqual(getEditorFields(), []);
    assert.equal(getEditorTopicText(), '');

    for (const metadata of [{ name: 'Topic' }, { fieldName: ' TOPIC ' }, { field: { name: 'topic' } }]) {
      fields = [
        { name: 'Other' },
        {
          ...metadata,
          editingArea: { content: { subscribe: (callback) => (callback('<b>Python &amp; JS</b>'), () => {}) } },
        },
      ];

      assert.equal(getEditorFields(), fields);
      assert.equal(getEditorTopicText(), 'Python & JS');
    }

    fields = [{ name: 'Topic', editingArea: { content: { subscribe: (callback) => (callback(null), () => {}) } } }];
    assert.equal(getEditorTopicText(), '');
    globalThis.require = undefined;
    assert.deepEqual(getEditorFields(), []);
  } finally {
    globalThis.document = previousDocument;
    globalThis.require = previousRequire;
    dom.window.close();
  }
});
