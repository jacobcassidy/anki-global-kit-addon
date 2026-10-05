import assert from 'node:assert/strict';
import test from 'node:test';
import { markdownToHtml } from '../../src/cards/js/markdown/render.js';

// Set the Desktop runtime flag before importing the keyboard handler.
globalThis.pycmd = () => {};
const { handleTabIndentation } = await import('../../src/cards/js/inputs/tab-navigation.js');

function setup(value, start = value.length, end = start, topic = 'JavaScript', platform = 'MacIntel') {
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { platform } });
  const input = {
    value,
    selectionStart: start,
    selectionEnd: end,
    inputEvents: 0,
    setRangeText(text, from, to) {
      this.value = this.value.slice(0, from) + text + this.value.slice(to);
      this.selectionStart = this.selectionEnd = from + text.length;
    },
    setSelectionRange(from, to) {
      this.selectionStart = from;
      this.selectionEnd = to;
    },
    dispatchEvent(event) {
      assert.equal(event.type, 'input');
      assert.equal(event.bubbles, true);
      this.inputEvents++;
    },
    tabIndex: 0,
    getClientRects: () => [1],
  };
  const next = {
    ...input,
    focusCalls: 0,
    focus() {
      this.focusCalls++;
    },
  };
  globalThis.document = {
    querySelector: () => ({ textContent: topic }),
    querySelectorAll: () => [input, next],
  };
  globalThis.window = { getComputedStyle: () => ({ visibility: 'visible', display: 'block' }) };
  return { input, next };
}

function key(options = {}) {
  return {
    key: 'Tab',
    shiftKey: false,
    ctrlKey: false,
    metaKey: false,
    altKey: false,
    isComposing: false,
    prevented: false,
    stopped: false,
    preventDefault() {
      this.prevented = true;
    },
    stopPropagation() {
      this.stopped = true;
    },
    ...options,
  };
}

for (const marker of ['-', '*', '+', '1.', '12.']) {
  test(`Tab and Shift+Tab change the ${marker} list level at the line start`, () => {
    const text = `${marker} item`;
    const { input, next } = setup(text, text.length - 2);
    const caret = input.selectionStart;
    handleTabIndentation(input, key());
    assert.equal(input.value, `  ${text}`);
    assert.equal(input.selectionStart, caret + 2);
    assert.equal(input.selectionEnd, caret + 2);
    handleTabIndentation(input, key({ shiftKey: true }));
    assert.equal(input.value, text);
    assert.equal(input.selectionStart, caret);
    assert.equal(input.inputEvents, 2);
    assert.equal(next.focusCalls, 0);
  });
}

test('a nested list item renders as a child after Tab and a sibling after Shift+Tab', () => {
  const { input } = setup('- parent\n- child');
  handleTabIndentation(input, key());
  assert.equal((markdownToHtml(input.value).match(/<ul>/g) || []).length, 2);
  handleTabIndentation(input, key({ shiftKey: true }));
  assert.equal((markdownToHtml(input.value).match(/<ul>/g) || []).length, 1);
});

test('Python list levels use four spaces', () => {
  const { input } = setup('- item', 6, 6, 'Python');
  handleTabIndentation(input, key());
  assert.equal(input.value, '    - item');
  handleTabIndentation(input, key({ shiftKey: true }));
  assert.equal(input.value, '- item');
});

test('selected list items indent together without including the following line', () => {
  const value = '- one\n- two\n- three';
  const { input } = setup(value, 0, 12);
  handleTabIndentation(input, key());
  assert.equal(input.value, '  - one\n  - two\n- three');
  assert.equal(input.selectionStart, 2);
  assert.equal(input.selectionEnd, 16);
  handleTabIndentation(input, key({ shiftKey: true }));
  assert.equal(input.value, value);
  assert.equal(input.selectionStart, 0);
  assert.equal(input.selectionEnd, 12);
});

test('Shift+Tab at the root list level consumes the key without moving focus', () => {
  const { input, next } = setup('- item');
  const event = key({ shiftKey: true });
  handleTabIndentation(input, event);
  assert.equal(input.value, '- item');
  assert.equal(input.inputEvents, 0);
  assert.equal(event.prevented, true);
  assert.equal(next.focusCalls, 0);
});

for (const indentation of [' ', '\t']) {
  test(`Shift+Tab removes a partial level or a tab: ${JSON.stringify(indentation)}`, () => {
    const { input } = setup(`${indentation}- item`);
    handleTabIndentation(input, key({ shiftKey: true }));
    assert.equal(input.value, '- item');
  });
}

test('Tab in plain text still replaces the selection with spaces', () => {
  const { input } = setup('some text', 5, 9);
  handleTabIndentation(input, key());
  assert.equal(input.value, 'some   ');
  assert.equal(input.selectionStart, 7);
});

test('list-like text in a fenced code block uses ordinary Tab insertion', () => {
  const { input } = setup('```\n- item\n```', 8);
  handleTabIndentation(input, key());
  assert.equal(input.value, '```\n- it  em\n```');
});

test('Shift+Tab outside a list keeps native backward navigation', () => {
  const { input, next } = setup('plain');
  const event = key({ shiftKey: true });
  handleTabIndentation(input, event);
  assert.equal(event.prevented, false);
  assert.equal(next.focusCalls, 0);
});

for (const [platform, modifier] of [
  ['MacIntel', 'metaKey'],
  ['Linux', 'ctrlKey'],
]) {
  test(`physical Control+Tab advances focus on ${platform}`, () => {
    const { input, next } = setup('- item', 6, 6, 'JavaScript', platform);
    const event = key({ [modifier]: true });
    handleTabIndentation(input, event);
    assert.equal(next.focusCalls, 1);
    assert.equal(input.value, '- item');
    assert.equal(event.prevented, true);
    assert.equal(event.stopped, true);
  });
}

test('Control+Tab skips hidden and disabled elements', () => {
  const { input, next } = setup('plain');
  const hidden = { ...next, hidden: true };
  const disabled = { ...next, disabled: true };
  document.querySelectorAll = () => [input, hidden, disabled, next];
  window.getComputedStyle = (element) => ({ visibility: element.hidden ? 'hidden' : 'visible', display: 'block' });
  handleTabIndentation(input, key({ metaKey: true }));
  assert.equal(next.focusCalls, 1);
  assert.equal(hidden.focusCalls, 0);
  assert.equal(disabled.focusCalls, 0);
});

for (const options of [{ ctrlKey: true }, { altKey: true }, { isComposing: true }, { key: 'Enter' }]) {
  test(`unrelated shortcuts and composition leave text unchanged: ${JSON.stringify(options)}`, () => {
    const { input } = setup('- item');
    const event = key(options);
    handleTabIndentation(input, event);
    assert.equal(input.value, '- item');
    assert.equal(event.prevented, false);
  });
}
