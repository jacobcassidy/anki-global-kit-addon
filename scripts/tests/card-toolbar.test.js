import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { JSDOM } from 'jsdom';

const bundle = readFileSync(new URL('../../addon/web/assets/js/_anki-global-kit.min.js', import.meta.url), 'utf8');
function card(settings = {}, platform = 'MacIntel') {
  const dom = new JSDOM(
    '<div id="qa"><div class="topic">Python</div><textarea class="question-input">one\ntwo\nthree</textarea></div>',
    { runScripts: 'outside-only' },
  );
  Object.defineProperty(dom.window.navigator, 'platform', { value: platform });
  dom.window.pycmd = () => {};
  dom.window.ankiGlobalKitSettings = settings;
  dom.window.eval(bundle);
  const input = dom.window.document.querySelector('textarea');
  input.setSelectionRange(5, 5);
  return { dom, input, document: dom.window.document };
}

test('indent toolbar buttons appear between ordered list and blockquote and preserve the selected row', () => {
  const { dom, input, document } = card();
  try {
    const buttons = [...document.querySelectorAll('.toolbar-group[aria-label="Lists and quotes"] button')];
    assert.deepEqual(
      buttons.map((button) => button.className.split(' ')[1]),
      [
        'is-unordered-list',
        'is-ordered-list',
        'is-indent-increase',
        'is-indent-decrease',
        'is-blockquote',
      ],
    );
    const increase = document.querySelector('.is-indent-increase');
    const decrease = document.querySelector('.is-indent-decrease');
    assert.equal(increase.title, 'Increase indent (⌘⇧.)');
    assert.equal(decrease.title, 'Decrease indent (⌘⇧,)');
    increase.click();
    assert.equal(input.value, 'one\n    two\nthree');
    assert.equal(input.selectionStart, 9);
    decrease.click();
    assert.equal(input.value, 'one\ntwo\nthree');
    assert.equal(input.selectionStart, 5);
    assert.equal(document.activeElement, input);
  } finally {
    dom.window.close();
  }
});

test('toolbar indentation stays available when keyboard indentation is disabled', () => {
  const { dom, input, document } = card({ card_input_tab_indentation: false });
  try {
    const increase = document.querySelector('.is-indent-increase');
    assert.equal(increase.title, 'Increase indent');
    increase.click();
    assert.equal(input.value, 'one\n    two\nthree');
    const event = new dom.window.KeyboardEvent('keydown', { key: 'Tab', ctrlKey: true, cancelable: true });
    input.dispatchEvent(event);
    assert.equal(event.defaultPrevented, false);
    assert.equal(input.value, 'one\n    two\nthree');
  } finally {
    dom.window.close();
  }
});

test('custom indentation shortcuts work independently of Markdown shortcuts and update tooltips', () => {
  const { dom, input, document } = card({
    card_input_markdown_shortcuts: false,
    card_input_tab_indent_increase_shortcut: 'Alt+]',
    card_input_tab_indent_decrease_shortcut: 'Alt+[',
  });
  try {
    assert.equal(document.querySelector('.is-bold').title, 'Bold');
    assert.equal(document.querySelector('.is-indent-increase').title, 'Increase indent (⌥])');
    assert.equal(document.querySelector('.is-indent-decrease').title, 'Decrease indent (⌥[)');
    for (const [key, expected] of [
      [']', 'one\n    two\nthree'],
      ['[', 'one\ntwo\nthree'],
    ]) {
      const event = new dom.window.KeyboardEvent('keydown', { key, altKey: true, cancelable: true });
      input.dispatchEvent(event);
      assert.equal(event.defaultPrevented, true);
      assert.equal(input.value, expected);
    }
    const old = new dom.window.KeyboardEvent('keydown', { key: 'Tab', altKey: true, cancelable: true });
    input.dispatchEvent(old);
    assert.equal(old.defaultPrevented, false);
  } finally {
    dom.window.close();
  }
});

test('individual shortcut and toolbar switches are independent', () => {
  const { dom, input, document } = card({
    card_input_tab_indent_increase_shortcut_enabled: false,
    card_toolbar_indent_decrease: false,
  });
  try {
    assert.equal(document.querySelector('.is-indent-decrease'), null);
    const increase = document.querySelector('.is-indent-increase');
    assert.equal(increase.title, 'Increase indent');
    const event = new dom.window.KeyboardEvent('keydown', { key: 'Tab', altKey: true, cancelable: true });
    input.dispatchEvent(event);
    assert.equal(event.defaultPrevented, false);
    increase.click();
    assert.equal(input.value, 'one\n    two\nthree');
  } finally {
    dom.window.close();
  }
});

test('disabling Markdown shortcuts leaves Enter in list-like text to the textarea', () => {
  const { dom, input } = card({ card_input_markdown_shortcuts: false });
  try {
    input.value = '1. literal text';
    input.setSelectionRange(input.value.length, input.value.length);
    const event = new dom.window.KeyboardEvent('keydown', { key: 'Enter', cancelable: true });
    input.dispatchEvent(event);
    assert.equal(event.defaultPrevented, false);
    assert.equal(input.value, '1. literal text');
  } finally {
    dom.window.close();
  }
});

function toolbarKey(dom, target, key, modifiers = {}) {
  const event = new dom.window.KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...modifiers });
  target.dispatchEvent(event);
  return event;
}

test('the toolbar has one tab stop and supports wrapping arrows, Home, End, and Escape', () => {
  const { dom, input, document } = card();
  try {
    const buttons = [...document.querySelectorAll('[role="toolbar"] button')];
    assert.deepEqual(
      buttons.map((button) => button.tabIndex),
      [0, ...buttons.slice(1).map(() => -1)],
    );
    buttons[0].focus();
    assert.equal(toolbarKey(dom, buttons[0], 'ArrowLeft').defaultPrevented, true);
    assert.equal(document.activeElement, buttons.at(-1));
    toolbarKey(dom, buttons.at(-1), 'ArrowRight');
    assert.equal(document.activeElement, buttons[0]);
    toolbarKey(dom, buttons[0], 'End');
    assert.equal(document.activeElement, buttons.at(-1));
    toolbarKey(dom, buttons.at(-1), 'Home');
    assert.equal(document.activeElement, buttons[0]);
    assert.equal(buttons.filter((button) => button.tabIndex === 0).length, 1);
    assert.equal(toolbarKey(dom, buttons[0], 'Tab').defaultPrevented, false);
    assert.equal(toolbarKey(dom, buttons[0], 'ArrowRight', { altKey: true }).defaultPrevented, false);
    toolbarKey(dom, buttons[0], 'Escape');
    assert.equal(document.activeElement, input);
    assert.equal(input.selectionStart, 5);
  } finally {
    dom.window.close();
  }
});

test('Enter and Space activate toolbar indentation with shortcuts disabled and preserve the input selection', () => {
  const { dom, input, document } = card({ card_input_tab_indentation: false });
  try {
    const increase = document.querySelector('.is-indent-increase');
    increase.focus();
    assert.equal(increase.tabIndex, 0);
    assert.equal(toolbarKey(dom, increase, 'Enter').defaultPrevented, true);
    assert.equal(input.value, 'one\n    two\nthree');
    assert.equal(input.selectionStart, 9);
    assert.equal(document.activeElement, input);
    const decrease = document.querySelector('.is-indent-decrease');
    decrease.focus();
    toolbarKey(dom, decrease, ' ');
    assert.equal(input.value, 'one\ntwo\nthree');
    assert.equal(input.selectionStart, 5);
    assert.equal(document.activeElement, input);
  } finally {
    dom.window.close();
  }
});

test('toolbar arrow navigation follows right-to-left layout direction', () => {
  const { dom, document } = card();
  try {
    const toolbar = document.querySelector('[role="toolbar"]');
    toolbar.style.direction = 'rtl';
    const buttons = [...toolbar.querySelectorAll('button')];
    buttons[0].focus();
    toolbarKey(dom, buttons[0], 'ArrowRight');
    assert.equal(document.activeElement, buttons.at(-1));
    toolbarKey(dom, buttons.at(-1), 'ArrowLeft');
    assert.equal(document.activeElement, buttons[0]);
  } finally {
    dom.window.close();
  }
});
