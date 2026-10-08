import assert from 'node:assert/strict';
import test from 'node:test';
import {
  handleMarkdownListEnter,
  toggleMarkdownBlock,
  toggleMarkdownFormatting,
} from '../../src/cards/js/inputs/markdown-shortcuts.js';

function textarea(value, start, end = start) {
  return {
    value,
    selectionStart: start,
    selectionEnd: end,
    inputEvents: 0,
    setRangeText(replacement, rangeStart, rangeEnd) {
      this.value = this.value.slice(0, rangeStart) + replacement + this.value.slice(rangeEnd);
      this.selectionStart = this.selectionEnd = rangeStart + replacement.length;
    },
    dispatchEvent(event) {
      assert.equal(event.type, 'input');
      assert.equal(event.bubbles, true);
      this.inputEvents++;
    },
  };
}

const formats = [
  ['bold', '**', '**'],
  ['italic', '*', '*'],
  ['strikethrough', '~~', '~~'],
  ['inline code', '`', '`'],
  ['code block', '```\n', '\n```'],
];

for (const [name, prefix, suffix] of formats) {
  test(`${name} toggles repeatedly from the cursor left after formatting a word`, () => {
    const input = textarea('before word after', 9);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, `before ${prefix}word${suffix} after`);
    assert.equal(input.selectionStart, 7 + prefix.length + 4 + suffix.length);
    assert.equal(input.selectionEnd, input.selectionStart);

    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, 'before word after');
    assert.equal(input.selectionStart, 7);
    assert.equal(input.selectionEnd, 11);

    toggleMarkdownFormatting(input, prefix, suffix);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, 'before word after');
    assert.equal(input.inputEvents, 4);
  });

  test(`${name} removes a multiword selection from its ending cursor`, () => {
    const input = textarea('before two words after', 7, 16);
    toggleMarkdownFormatting(input, prefix, suffix);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, 'before two words after');
    assert.equal(input.selectionStart, 7);
    assert.equal(input.selectionEnd, 16);
  });

  test(`${name} still removes formatting from inside the contents`, () => {
    const input = textarea(`${prefix}word${suffix}`, prefix.length + 2);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, 'word');
  });

  test(`${name} does not remove a previous word's formatting after moving the cursor`, () => {
    const value = `${prefix}first${suffix} second`;
    const input = textarea(value, value.length);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, `${prefix}first${suffix} ${prefix}second${suffix}`);
  });

  test(`${name} removes an empty pair from its ending cursor`, () => {
    const input = textarea(`${prefix}${suffix}`, prefix.length + suffix.length);
    toggleMarkdownFormatting(input, prefix, suffix);
    assert.equal(input.value, '');
    assert.equal(input.selectionStart, 0);
    assert.equal(input.selectionEnd, 0);
  });
}

test('bold and italic remove only their own layer at the end of combined formatting', () => {
  const bold = textarea('***word***', 10);
  toggleMarkdownFormatting(bold, '**', '**');
  assert.equal(bold.value, '*word*');

  const italic = textarea('***word***', 10);
  toggleMarkdownFormatting(italic, '*', '*');
  assert.equal(italic.value, '**word**');
});

test('italic at the end of bold text adds italic without removing the bold markers', () => {
  const input = textarea('**word**', 8);
  toggleMarkdownFormatting(input, '*', '*');
  assert.equal(input.value, '***word***');
});

const listConversions = [
  {
    name: 'unordered parents to ordered parents',
    input: '- parent\n  - child\n    1. grandchild\n- sibling\n  + child',
    format: 'ordered-list',
    expected: '1. parent\n  - child\n    1. grandchild\n2. sibling\n  + child',
  },
  {
    name: 'ordered parents to unordered parents',
    input: '1. parent\n  1. child\n    - grandchild\n2. sibling\n  2. child',
    format: 'unordered-list',
    expected: '- parent\n  1. child\n    - grandchild\n- sibling\n  2. child',
  },
  {
    name: 'toggle off only unordered parents',
    input: '- parent\n  1. child\n- sibling\n  - child',
    format: 'unordered-list',
    expected: 'parent\n  1. child\nsibling\n  - child',
  },
  {
    name: 'toggle off only ordered parents',
    input: '1. parent\n  - child\n2. sibling\n  1. child',
    format: 'ordered-list',
    expected: 'parent\n  - child\nsibling\n  1. child',
  },
  {
    name: 'plain indentation becomes an unordered hierarchy',
    input: 'parent\n  child\n    grandchild\nsibling\n  other child',
    format: 'unordered-list',
    expected: '- parent\n  - child\n    - grandchild\n- sibling\n  - other child',
  },
  {
    name: 'plain indentation becomes ordered lists numbered at each level',
    input: 'parent\n  child\n  child two\n    grandchild\nsibling\n  other child',
    format: 'ordered-list',
    expected: '1. parent\n  1. child\n  2. child two\n    1. grandchild\n2. sibling\n  1. other child',
  },
  {
    name: 'tabs and spaces keep their original indentation',
    input: '- parent\n\t- child\n    - other child\n- sibling',
    format: 'ordered-list',
    expected: '1. parent\n\t- child\n    - other child\n2. sibling',
  },
  {
    name: 'mixed parent styles become one consistently numbered list',
    input: '- parent\n  - child\n8. sibling',
    format: 'ordered-list',
    expected: '1. parent\n  - child\n2. sibling',
  },
  {
    name: 'blank lines remain blank when formatting plain text',
    input: 'parent\n\n  child\n   ',
    format: 'unordered-list',
    expected: '- parent\n\n  - child\n   ',
  },
];

for (const { name, input: value, format, expected } of listConversions) {
  test(name, () => {
    const input = textarea(value, 0, value.length);
    toggleMarkdownBlock(input, format);
    assert.equal(input.value, expected);
    assert.equal(input.inputEvents, 1);
  });
}

test('selecting children as the outermost level converts them and preserves grandchildren', () => {
  const value = '- parent\n  - child\n    - grandchild\n  - sibling\n- other parent';
  const input = textarea(value, value.indexOf('child'), value.indexOf('\n- other parent'));
  toggleMarkdownBlock(input, 'ordered-list');
  assert.equal(input.value, '- parent\n  1. child\n    - grandchild\n  2. sibling\n- other parent');
});

test('a caret in a child item converts just that item at its original level', () => {
  const value = '1. parent\n  1. child\n    - grandchild\n  2. sibling';
  const input = textarea(value, value.indexOf('child') + 2);
  toggleMarkdownBlock(input, 'unordered-list');
  assert.equal(input.value, '1. parent\n  - child\n    - grandchild\n  2. sibling');
});

test('a selection ending at the next line excludes that line', () => {
  const input = textarea('- one\n- two\n- three', 0, 12);
  toggleMarkdownBlock(input, 'ordered-list');
  assert.equal(input.value, '1. one\n2. two\n- three');
});

test('a leading empty line does not hide the first selected parent', () => {
  const value = '\n- parent\n  - child';
  const input = textarea(value, 0, value.length);
  toggleMarkdownBlock(input, 'ordered-list');
  assert.equal(input.value, '\n1. parent\n  - child');
});

test('list buttons still create a marker at an empty caret', () => {
  const input = textarea('  ', 2);
  toggleMarkdownBlock(input, 'unordered-list');
  assert.equal(input.value, '  - ');
});

test('blockquote toggling continues to apply to all selected lines', () => {
  const value = '- parent\n  - child';
  const input = textarea(value, 0, value.length);
  toggleMarkdownBlock(input, 'blockquote');
  assert.equal(input.value, '> - parent\n  > - child');
  input.selectionStart = 0;
  input.selectionEnd = input.value.length;
  toggleMarkdownBlock(input, 'blockquote');
  assert.equal(input.value, value);
});

test('blockquotes are added and removed at each existing indentation level', () => {
  const value = 'parent\n  child\n    grandchild\n\ttab-indented child';
  const input = textarea(value, 0, value.length);
  toggleMarkdownBlock(input, 'blockquote');
  assert.equal(input.value, '> parent\n  > child\n    > grandchild\n\t> tab-indented child');
  input.selectionStart = 0;
  input.selectionEnd = input.value.length;
  toggleMarkdownBlock(input, 'blockquote');
  assert.equal(input.value, value);
});

test('adding blockquotes preserves existing indented quotes', () => {
  const value = '  > quoted\n    plain';
  const input = textarea(value, 0, value.length);
  toggleMarkdownBlock(input, 'blockquote');
  assert.equal(input.value, '  > quoted\n    > plain');
});

for (const value of ['```markdown\n1. literal code', '```\n- literal code', 'text\n  ```markdown\n1. literal code']) {
  test(`Enter retains literal behavior inside fenced code: ${JSON.stringify(value)}`, () => {
    const input = textarea(value, value.length);
    const event = { key: 'Enter', preventDefault: () => assert.fail('Code Enter must remain native') };
    assert.equal(handleMarkdownListEnter(input, event), false);
    assert.equal(input.value, value);
    assert.equal(input.inputEvents, 0);
  });
}

test('list continuation resumes after a closed code fence and exits an empty item', () => {
  const value = '```markdown\n1. literal code\n```\n5. real item';
  const input = textarea(value, value.length);
  let prevented = 0;
  const event = { key: 'Enter', preventDefault: () => prevented++ };
  assert.equal(handleMarkdownListEnter(input, event), true);
  assert.equal(input.value, `${value}\n6. `);
  assert.equal(handleMarkdownListEnter(input, event), true);
  assert.equal(input.value, `${value}\n\n`);
  assert.equal(prevented, 2);
});
