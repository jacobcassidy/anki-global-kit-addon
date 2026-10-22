import javascript from './languages/javascript.js';
import python from './languages/python.js';
import { readTree } from './scopes.js';

const LANGUAGES = new Map([
  ['javascript', javascript],
  ['python', python],
]);

const ALIASES = { js: 'javascript', node: 'javascript', py: 'python', python3: 'python', py3: 'python' };
const MAX_SOURCE_UNITS = 100_000;

/** A cooperative analysis deadline shared by every block in an operation. */
export function createClassificationBudget(milliseconds = 100, now = () => performance.now()) {
  const deadline = now() + milliseconds;
  let steps = 0;

  return {
    expired: () => now() >= deadline,
    check(force = false) {
      steps += 1;

      if ((force || steps % 128 === 0) && now() >= deadline) throw new Error('Classification deadline exceeded');
    },
  };
}

export function supportsClassification(language) {
  return LANGUAGES.has(ALIASES[language] || language);
}

/** Locate complete Anki clozes without interpreting or changing their contents. */
function protectedClozes(source, budget) {
  const ranges = [];
  const start = /\{\{c\d+::/g;
  let match;

  while ((match = start.exec(source))) {
    let depth = 1;
    let cursor = start.lastIndex;

    while (cursor < source.length && depth) {
      budget.check();

      if (source.startsWith('{{', cursor)) {
        depth += 1;
        cursor += 2;
      } else if (source.startsWith('}}', cursor)) {
        depth -= 1;
        cursor += 2;
      } else {
        cursor += 1;
      }
    }

    if (depth) break;

    ranges.push({ from: match.index, to: cursor });
    start.lastIndex = cursor;
  }

  return ranges;
}

/** Return source-offset roles; a failed or exhausted analysis returns no overlays. */
export function classifyCode(source, language, options = {}) {
  const adapter = LANGUAGES.get(ALIASES[language] || language);

  if (!adapter || typeof source !== 'string' || source.length > MAX_SOURCE_UNITS) return [];

  const budget = options.budget || createClassificationBudget();

  try {
    budget.check(true);

    if (source.length > 50_000 && Array.from(source).length > 50_000) return [];

    const protectedRanges = protectedClozes(source, budget);
    const pieces = [];
    let position = 0;

    // Without the Unicode flag, each replaced character is exactly one UTF-16 unit.
    for (const range of protectedRanges) {
      budget.check();
      pieces.push(source.slice(position, range.from), source.slice(range.from, range.to).replace(/[^\r\n]/g, ' '));
      position = range.to;
    }

    pieces.push(source.slice(position));

    const masked = pieces.join('');

    const parsing = adapter.parser.startParse(masked);
    let tree;

    while (!tree) {
      budget.check(true);
      tree = parsing.advance();
    }

    const nodes = readTree(tree, budget);
    const excluded = [...protectedRanges, ...nodes.filter((node) => node.error && node.to > node.from)].sort(
      (a, b) => a.from - b.from,
    );
    const spans = adapter.classify(nodes, source, budget).sort((a, b) => a.from - b.from || a.to - b.to);
    const result = [];
    let end = 0;
    let excludedIndex = 0;

    for (const span of spans) {
      budget.check();

      while (excluded[excludedIndex]?.to <= span.from) excludedIndex += 1;

      if (span.from < end || span.to <= span.from || excluded[excludedIndex]?.from < span.to) continue;
      result.push(span);
      end = span.to;
    }

    budget.check(true);

    return result;
  } catch {
    return [];
  }
}
