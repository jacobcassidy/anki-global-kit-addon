import assert from 'node:assert/strict';
import test from 'node:test';
import { reportQuestionShortcutFocus } from '../../src/cards/js/inputs/shortcut-focus.js';

function report(active, enabled = true, shortcuts = { unorderedList: 'Ctrl+,' }) {
  const messages = [];
  globalThis.document = { activeElement: active ? { matches: () => true } : null };
  globalThis.pycmd = (message) => messages.push(message);
  reportQuestionShortcutFocus(enabled, shortcuts);
  return messages;
}

test('refreshing ownership claims Command+Comma for an already-focused question input', () => {
  assert.deepEqual(report(true), ['anki-global-kit:question-input-focus:handled']);
  assert.deepEqual(report(true), ['anki-global-kit:question-input-focus:handled']);
});

test('disabled shortcuts and other configured keys do not claim Preferences', () => {
  assert.deepEqual(report(true, false), ['anki-global-kit:question-input-focus:unhandled']);
  assert.deepEqual(report(true, true, { unorderedList: 'Ctrl+.' }), ['anki-global-kit:question-input-focus:unhandled']);
});

test('refreshing after leaving question inputs releases Command+Comma', () => {
  assert.deepEqual(report(false), ['anki-global-kit:question-input-blur']);
});
