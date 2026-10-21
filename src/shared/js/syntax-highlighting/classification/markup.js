import { classifyCode, createClassificationBudget, supportsClassification } from './index.js';
import { themeRole } from './roles.js';

/** Add identifier roles to detached engine HTML, preserving all source text. */
export function enhanceHighlightHtml(html, language, options = {}) {
  const owner = options.document || globalThis.document;

  if (!supportsClassification(language) || !owner || typeof html !== 'string') return html;

  const budget = options.budget || createClassificationBudget();

  try {
    budget.check(true);

    const container = owner.createElement('div');

    container.innerHTML = html;

    const source = container.textContent;
    const spans = classifyCode(source, language, { budget });

    if (!spans.length) return html;

    const walker = owner.createTreeWalker(container, 4); // NodeFilter.SHOW_TEXT
    const leaves = [];
    let position = 0;
    let leaf;

    while ((leaf = walker.nextNode())) {
      budget.check();
      leaves.push({ node: leaf, from: position, to: position + leaf.length });
      position += leaf.length;
    }

    let spanIndex = 0;

    for (const item of leaves) {
      budget.check(true);

      while (spans[spanIndex]?.to <= item.from) spanIndex += 1;

      if (!spans[spanIndex] || spans[spanIndex].from >= item.to) continue;

      const fragment = owner.createDocumentFragment();
      let cursor = item.from;
      let index = spanIndex;

      while (spans[index] && spans[index].from < item.to) {
        budget.check(true);

        const span = spans[index];
        const from = Math.max(span.from, item.from);
        const to = Math.min(span.to, item.to);

        if (cursor < from) fragment.append(owner.createTextNode(source.slice(cursor, from)));

        const marked = owner.createElement('span');

        marked.dataset.globalKitToken = themeRole(span);
        marked.textContent = source.slice(from, to);
        fragment.append(marked);
        cursor = to;
        index += 1;
      }

      if (cursor < item.to) fragment.append(owner.createTextNode(source.slice(cursor, item.to)));

      item.node.replaceWith(fragment);
    }

    budget.check(true);

    return container.textContent === source ? container.innerHTML : html;
  } catch {
    // The live field is never touched until the complete enriched result is ready.
    return html;
  }
}
