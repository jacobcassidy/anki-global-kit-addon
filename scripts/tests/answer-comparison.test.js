import assert from 'node:assert/strict';
import test from 'node:test';
import { diffAnswerCharacters } from '../../src/cards/js/display/answer-comparison.js';

function compare(expected, actual) {
  const diffs = diffAnswerCharacters(expected, actual);
  assert.equal(
    diffs
      .filter(([operation]) => operation !== 1)
      .map(([, text]) => text)
      .join(''),
    expected,
  );
  assert.equal(
    diffs
      .filter(([operation]) => operation !== -1)
      .map(([, text]) => text)
      .join(''),
    actual,
  );
  for (const [operation, text] of diffs) {
    assert.ok([-1, 0, 1].includes(operation));
    assert.notEqual(text, '');
    assert.doesNotMatch(text, /[\uD800-\uDFFF]/u, 'valid Unicode must not become isolated surrogate halves');
  }
  return diffs;
}

test('empty answers, insertions, omissions, and short substitutions retain the comparison format', () => {
  assert.deepEqual(compare('', ''), []);
  assert.deepEqual(compare('', 'hello'), [[1, 'hello']]);
  assert.deepEqual(compare('hello', ''), [[-1, 'hello']]);
  assert.deepEqual(compare('hello', 'hallo'), [
    [0, 'h'],
    [-1, 'e'],
    [1, 'a'],
    [0, 'llo'],
  ]);
  assert.deepEqual(compare('a', 'baa'), [
    [1, 'ba'],
    [0, 'a'],
  ]);
});

for (const length of [999, 1000, 3000, 10_000]) {
  test(`identical ${length}-character answers remain entirely correct`, () => {
    const answer = 'a'.repeat(length);
    assert.deepEqual(compare(answer, answer), [[0, answer]]);
  });

  test(`a typo inside ${length}-character answers preserves both matching ends`, () => {
    const prefix = 'a'.repeat(Math.floor(length / 2));
    const suffix = 'b'.repeat(length - prefix.length - 1);
    assert.deepEqual(compare(prefix + 'x' + suffix, prefix + 'y' + suffix), [
      [0, prefix],
      [-1, 'x'],
      [1, 'y'],
      [0, suffix],
    ]);
  });
}

test('10,000-character answers retain a large matching region between two changed ends', () => {
  const prefix = 'a'.repeat(2500);
  const suffix = 'c'.repeat(2500);
  const common = 'b'.repeat(5000);
  const diffs = compare(prefix + common + suffix, 'x'.repeat(2500) + common + 'y'.repeat(2500));
  assert.deepEqual(
    diffs.filter(([operation]) => operation === 0),
    [[0, common]],
  );
});

test('10,000-character answers with no shared characters report only omissions and mistakes', () => {
  const expected = 'a'.repeat(10_000);
  const actual = 'b'.repeat(10_000);
  assert.deepEqual(compare(expected, actual), [
    [-1, expected],
    [1, actual],
  ]);
});

test('large insertions and omissions preserve matching text', () => {
  const prefix = 'a'.repeat(4000);
  const suffix = 'b'.repeat(4000);
  const inserted = 'x'.repeat(2000);
  assert.deepEqual(compare(prefix + suffix, prefix + inserted + suffix), [
    [0, prefix],
    [1, inserted],
    [0, suffix],
  ]);
  assert.deepEqual(compare(prefix + inserted + suffix, prefix + suffix), [
    [0, prefix],
    [-1, inserted],
    [0, suffix],
  ]);
});

test('10,000-character repeated text retains its matching run despite shifted boundaries', () => {
  const diffs = compare('ab'.repeat(5000), 'ba'.repeat(5000));
  assert.equal(
    diffs.filter(([operation]) => operation === 0).reduce((total, [, text]) => total + text.length, 0),
    9999,
  );
});

test('a multiline 10,000-character code answer highlights just the changed character', () => {
  const expected = Array.from({ length: 400 }, (_, index) => `value_${index} = compute(input_${index})\n`)
    .join('')
    .slice(0, 10_000);
  const actual = expected.replace('input_20)', 'input_21)');
  const diffs = compare(expected, actual);
  assert.equal(expected.length, 10_000);
  assert.deepEqual(
    diffs.filter(([operation]) => operation !== 0),
    [
      [-1, '0'],
      [1, '1'],
    ],
  );
  assert.equal(
    diffs.filter(([operation]) => operation === 0).reduce((total, [, text]) => total + text.length, 0),
    9999,
  );
});

test('10,000 emoji are counted as code points and stay intact around a substitution', () => {
  const expected = '😀'.repeat(10_000);
  assert.deepEqual(compare(expected, expected), [[0, expected]]);
  const prefix = '😀'.repeat(5000);
  const suffix = '😀'.repeat(4999);
  assert.deepEqual(compare(expected, prefix + '😃' + suffix), [
    [0, prefix],
    [-1, '😀'],
    [1, '😃'],
    [0, suffix],
  ]);
});

test('10,000 distinct supplementary Unicode characters survive token encoding and shifted matching', () => {
  const characters = Array.from({ length: 10_000 }, (_, index) => String.fromCodePoint(0x10000 + index));
  const expected = characters.join('');
  const shifted = characters.slice(1).join('');
  assert.deepEqual(compare(expected, shifted + characters[0]), [
    [-1, characters[0]],
    [0, shifted],
    [1, characters[0]],
  ]);
});
