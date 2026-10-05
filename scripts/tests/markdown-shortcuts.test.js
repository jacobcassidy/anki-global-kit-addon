import assert from 'node:assert/strict';
import test from 'node:test';
import { toggleMarkdownFormatting } from '../../src/cards/js/inputs/markdown-shortcuts.js';

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
