import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import {
  formatBlockContent,
  installBlockFormatting,
  toggleEditorBlock,
} from '../../src/editor/js/formatting/blocks.js';

function editor(html) {
  const dom = new JSDOM(`<div contenteditable="true">${html}</div>`);
  for (const name of ['window', 'document', 'Node', 'NodeFilter', 'Range', 'navigator']) {
    Object.defineProperty(globalThis, name, { value: dom.window[name], configurable: true });
  }
  const field = document.querySelector('div');
  const range = document.createRange();
  range.selectNodeContents(field);
  return { field, range, dom };
}

function apply(html, format, choose) {
  const { field, range } = editor(html);
  choose?.(field, range);
  assert.equal(formatBlockContent(field, range, format), true);
  return field;
}

for (const [from, to, format] of [
  ['ul', 'ol', 'ordered-list'],
  ['ol', 'ul', 'unordered-list'],
]) {
  test(`${from} to ${to} converts selected parents and preserves mixed children`, () => {
    const field = apply(`<${from}><li>A<ul><li>B<ol><li>C</li></ol></li></ul></li><li>D</li></${from}>`, format);
    assert.equal(field.innerHTML, `<${to}><li>A<ul><li>B<ol><li>C</li></ol></li></ul></li><li>D</li></${to}>`);
  });
  test(`${from} to ${to} converts children selected without their parent`, () => {
    const field = apply(
      `<${from}><li>A<${from}><li>B</li><li>C</li></${from}></li></${from}>`,
      format,
      (field, range) => {
        range.selectNodeContents(field.querySelector(`${from} ${from}`));
      },
    );
    assert.equal(field.innerHTML, `<${from}><li>A<${to}><li>B</li><li>C</li></${to}></li></${from}>`);
  });
}

test('converting one item splits the list and leaves unselected siblings intact', () => {
  const field = apply(
    '<ol start="4"><li>A</li><li>B<ul><li>child</li></ul></li><li>C</li></ol>',
    'unordered-list',
    (field, range) => {
      range.selectNodeContents(field.querySelectorAll('li')[1].firstChild);
    },
  );
  assert.equal(
    field.innerHTML,
    '<ol start="4"><li>A</li></ol><ul><li>B<ul><li>child</li></ul></li></ul><ol start="6"><li>C</li></ol>',
  );
});

test('a selection ending at the next item start does not convert it', () => {
  const field = apply('<ul><li>A</li><li>B</li></ul>', 'ordered-list', (field, range) => {
    const items = field.querySelectorAll('li');
    range.setStart(items[0].firstChild, 0);
    range.setEnd(items[1].firstChild, 0);
  });
  assert.equal(field.innerHTML, '<ol><li>A</li></ol><ul><li>B</li></ul>');
});

test('caret conversion preserves nested child lists', () => {
  const field = apply('<ul><li>A<ul><li>B</li></ul></li></ul>', 'ordered-list', (field, range) => {
    range.setStart(field.querySelector('li').firstChild, 1);
    range.collapse(true);
  });
  assert.equal(field.innerHTML, '<ol><li>A<ul><li>B</li></ul></li></ol>');
});

test('toggling the current style removes the selected parent markers and preserves children', () => {
  const field = apply('<ul><li>A<ol><li>B</li></ol></li><li>C</li></ul>', 'unordered-list');
  assert.equal(field.innerHTML, '<div>A<ol><li>B</li></ol></div><div>C</div>');
});

for (const [format, tag] of [
  ['unordered-list', 'ul'],
  ['ordered-list', 'ol'],
]) {
  test(`${format} converts indented plain rows into the same hierarchy`, () => {
    const field = apply('<div><b>A</b></div><div>    B</div><div>        C</div><div>    D</div><div>E</div>', format);
    assert.equal(
      field.innerHTML,
      `<${tag}><li><b>A</b><${tag}><li>B<${tag}><li>C</li></${tag}></li><li>D</li></${tag}></li><li>E</li></${tag}>`,
    );
  });
  test(`${format} handles loose BR rows and preserves inline HTML`, () => {
    const field = apply('<strong>A</strong><br>    <em>B</em><br>C', format);
    assert.equal(
      field.innerHTML,
      `<${tag}><li><strong>A</strong><${tag}><li><em>B</em></li></${tag}></li><li>C</li></${tag}>`,
    );
  });
}

test('blockquote is inserted inside an indented child item', () => {
  const field = apply(
    '<ul><li>A<ol><li><b>B</b><ul><li>C</li></ul></li></ol></li></ul>',
    'blockquote',
    (field, range) => {
      range.selectNodeContents(field.querySelector('ol > li > b'));
    },
  );
  assert.equal(
    field.innerHTML,
    '<ul><li>A<ol><li><blockquote><b>B</b></blockquote><ul><li>C</li></ul></li></ol></li></ul>',
  );
});

test('blockquote toggles back off within its original list level', () => {
  const field = apply(
    '<ul><li>A<ol><li><blockquote>B</blockquote></li></ol></li></ul>',
    'blockquote',
    (field, range) => {
      range.selectNodeContents(field.querySelector('blockquote'));
    },
  );
  assert.equal(field.innerHTML, '<ul><li>A<ol><li>B</li></ol></li></ul>');
});

test('blockquote preserves existing plain text indentation', () => {
  const field = apply('<div style="margin-left: 4ch">    <b>A</b></div>', 'blockquote');
  assert.equal(field.innerHTML, '<div style="margin-left: 4ch"><blockquote>    <b>A</b></blockquote></div>');
});

function nativeInsertion(field) {
  const commands = [];
  document.execCommand = (command, _, html) => {
    commands.push(command);
    if (command === 'insertHTML') field.innerHTML = html;
    return true;
  };
  field.focus();
  return commands;
}

test('formatting uses one native insertion and keeps the caret on the same content', () => {
  const { field, range } = editor('<div>A</div><div>    B</div>');
  const commands = nativeInsertion(field);
  range.setStart(field.lastChild.firstChild, 5);
  range.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  assert.equal(toggleEditorBlock('ordered-list'), true);
  assert.deepEqual(commands, ['insertHTML']);
  assert.equal(field.textContent, 'AB');
  assert.equal(window.getSelection().focusNode.textContent, 'B');
  assert.equal(window.getSelection().focusOffset, 1);
});

test('Alt+Tab and Control+Tab change list levels while Tab retains native navigation', () => {
  const { field, range, dom } = editor('<ul><li>A</li></ul>');
  const commands = nativeInsertion(field);
  range.setStart(field.querySelector('li').firstChild, 1);
  range.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  installBlockFormatting();
  for (const options of [{}, { shiftKey: true }, { altKey: true }, { ctrlKey: true }]) {
    field.dispatchEvent(
      new dom.window.KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true, ...options }),
    );
  }
  assert.deepEqual(commands, ['indent', 'outdent']);
});

for (const [platform, modifier] of [
  ['MacIntel', 'metaKey'],
  ['Linux', 'ctrlKey'],
]) {
  test(`editor physical Control+Tab unindents on ${platform}`, () => {
    const { field, range, dom } = editor('<ul><li>A</li></ul>');
    Object.defineProperty(globalThis, 'navigator', { configurable: true, value: { platform } });
    const commands = nativeInsertion(field);
    range.setStart(field.querySelector('li').firstChild, 1);
    range.collapse(true);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    installBlockFormatting();
    const dispatch = (options) => {
      const event = new dom.window.KeyboardEvent('keydown', {
        key: 'Tab',
        bubbles: true,
        cancelable: true,
        ...options,
      });
      field.dispatchEvent(event);
      return event.defaultPrevented;
    };
    assert.equal(dispatch({}), false);
    assert.equal(dispatch({ shiftKey: true }), false);
    assert.equal(dispatch({ altKey: true, [modifier]: true }), false);
    assert.equal(dispatch({ [modifier === 'metaKey' ? 'ctrlKey' : 'metaKey']: true }), false);
    assert.equal(dispatch({ altKey: true }), true);
    assert.equal(dispatch({ [modifier]: true }), true);
    assert.deepEqual(commands, ['indent', 'outdent']);
  });
}

test('editor Control+Tab removes plain text indentation and preserves formatting and selection', () => {
  const { field, range, dom } = editor('<div>    <b>one</b></div><div>  two</div><div>three</div>');
  const selection = window.getSelection();
  range.setStart(field.firstChild.querySelector('b').firstChild, 1);
  range.setEnd(field.children[2].firstChild, 0);
  selection.addRange(range);
  const commands = [];
  document.execCommand = (command) => {
    commands.push(command);
    assert.equal(command, 'delete');
    selection.getRangeAt(0).deleteContents();
    return true;
  };
  installBlockFormatting();
  field.dispatchEvent(
    new dom.window.KeyboardEvent('keydown', {
      key: 'Tab',
      ctrlKey: true,
      bubbles: true,
      cancelable: true,
    }),
  );
  assert.equal(field.innerHTML, '<div><b>one</b></div><div>two</div><div>three</div>');
  assert.equal(selection.toString(), 'netwo');
  assert.deepEqual(commands, ['delete', 'delete']);
});

test('the existing list button and shortcut route to the same formatter', () => {
  const { field, range, dom } = editor('<ul><li>A<ul><li>B</li></ul></li></ul>');
  const commands = nativeInsertion(field);
  range.selectNodeContents(field);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  globalThis.ankiGlobalKitEditorListLabels = { 'ordered-list': 'Ctrl+.' };
  const button = document.createElement('button');
  button.title = 'Ordered list (Ctrl+.)';
  document.body.append(button);
  installBlockFormatting();
  button.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, cancelable: true }));
  assert.equal(field.innerHTML, '<ol><li>A<ul><li>B</li></ul></li></ol>');
  field.dispatchEvent(
    new dom.window.KeyboardEvent('keydown', { key: ',', ctrlKey: true, bubbles: true, cancelable: true }),
  );
  assert.equal(field.innerHTML, '<ul><li>A<ul><li>B</li></ul></li></ul>');
  assert.deepEqual(commands, ['insertHTML', 'insertHTML']);
});

test('a caret at the start of a child converts that child and stays there', () => {
  const { field, range } = editor('<ul><li>A<ul><li>B</li></ul></li></ul>');
  nativeInsertion(field);
  range.setStart(field.querySelector('ul ul li').firstChild, 0);
  range.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  assert.equal(toggleEditorBlock('ordered-list'), true);
  assert.equal(field.innerHTML, '<ul><li>A<ol><li>B</li></ol></li></ul>');
  assert.equal(window.getSelection().focusNode.textContent, 'B');
  assert.equal(window.getSelection().focusOffset, 0);
});

test('an empty row can start a list', () => {
  const field = apply('<div><br></div>', 'unordered-list');
  assert.equal(field.innerHTML, '<ul><li><br></li></ul>');
});

test('mixed quoted and unquoted rows do not add a second quote to quoted rows', () => {
  const field = apply('<blockquote><div>A</div></blockquote><div>B</div>', 'blockquote');
  assert.equal(field.innerHTML, '<blockquote><div>A</div></blockquote><div><blockquote>B</blockquote></div>');
});

test('conversion normalizes the sibling nested lists produced by native indentation', () => {
  const field = apply('<ul><li>A</li><ul><li>B</li></ul><li>C</li></ul>', 'ordered-list');
  assert.equal(field.innerHTML, '<ol><li>A<ul><li>B</li></ul></li><li>C</li></ol>');
});

test('an element-boundary caret selects the child list level', () => {
  const { field, range } = editor('<ul><li>A<ul><li>B</li></ul></li></ul>');
  nativeInsertion(field);
  range.setStart(field.querySelector('ul ul li'), 0);
  range.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
  assert.equal(toggleEditorBlock('ordered-list'), true);
  assert.equal(field.innerHTML, '<ul><li>A<ol><li>B</li></ol></li></ul>');
});
