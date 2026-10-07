import DiffMatchPatch from 'diff-match-patch';

/**
 * Render answer text without losing it.
 */
export function getRenderedAnswerText(answerElement) {
  // innerText preserves HTML line breaks, but only when the element has layout.
  // Comparison mode hides the original answer, so measure an invisible copy.
  const copy = answerElement.cloneNode(true);

  copy.style.setProperty('display', 'block', 'important');
  copy.style.setProperty('position', 'absolute', 'important');
  copy.style.setProperty('visibility', 'visible', 'important');
  copy.style.setProperty('opacity', '0', 'important');
  copy.style.setProperty('pointer-events', 'none', 'important');

  // Keep the temporary measurement copy inside the card's kit container.
  answerElement.closest('.global-kit-container').appendChild(copy);
  try {
    return copy.innerText;
  } finally {
    copy.remove();
  }
}

/**
 * Compare Unicode code points without allocating a quadratic comparison table.
 */
export function diffAnswerCharacters(cardAnswer, typedAnswer) {
  if (cardAnswer === typedAnswer) return cardAnswer ? [[0, cardAnswer]] : [];

  const expected = Array.from(cardAnswer);
  const actual = Array.from(typedAnswer);
  let start = 0;
  while (start < expected.length && start < actual.length && expected[start] === actual[start]) start++;

  let expectedEnd = expected.length;
  let actualEnd = actual.length;
  while (expectedEnd > start && actualEnd > start && expected[expectedEnd - 1] === actual[actualEnd - 1]) {
    expectedEnd--;
    actualEnd--;
  }

  const before = expected.slice(start, expectedEnd);
  const after = actual.slice(start, actualEnd);
  const middle = diffCodePoints(before, after);
  const diffs = [];
  if (start) diffs.push([0, expected.slice(0, start).join('')]);
  for (const diff of middle) diffs.push(diff);
  if (expectedEnd < expected.length) diffs.push([0, expected.slice(expectedEnd).join('')]);
  return diffs;
}

function diffCodePoints(before, after) {
  if (!before.length) return after.length ? [[1, after.join('')]] : [];
  if (!after.length) return [[-1, before.join('')]];

  // The engine works on UTF-16 units. Encode each code point as one BMP token,
  // excluding surrogates, so emoji cannot be split into separate comparisons.
  const characters = Array.from(new Set([...before, ...after]));
  const surrogateStart = 0xd800;
  const surrogateCount = 0x800;
  if (characters.length > 0x10000 - surrogateCount) {
    // This alphabet limit needs over 63,488 distinct characters in the changed
    // region, well beyond two 10,000-character answers. Shared ends are retained.
    return [
      [-1, before.join('')],
      [1, after.join('')],
    ];
  }
  const tokens = new Map(
    characters.map((character, index) => [
      character,
      String.fromCharCode(index < surrogateStart ? index : index + surrogateCount),
    ]),
  );
  const encode = (text) => text.map((character) => tokens.get(character)).join('');
  const engine = new DiffMatchPatch();
  engine.Diff_Timeout = 1;

  // Tokens do not represent actual lines or words, so disable line-mode cleanup.
  // The engine's linear-space bisect and timeout preserve matches without a
  // length cutoff; difficult changed regions may receive a coarser diff.
  return engine.diff_main(encode(before), encode(after), false).map(([operation, text]) => [
    operation,
    Array.from(text, (token) => {
      const index = token.charCodeAt(0);
      return characters[index < surrogateStart ? index : index - surrogateCount];
    }).join(''),
  ]);
}
