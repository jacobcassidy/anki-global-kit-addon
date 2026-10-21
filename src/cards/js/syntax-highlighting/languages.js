import { reviewLanguageAliases } from './engine.js';

const topicAliases = Object.entries(reviewLanguageAliases)
  .map(([alias, language]) => [new RegExp(`(?:^|[^a-z0-9])${escapeRegExp(alias)}(?=$|[^a-z0-9])`, 'i'), language])
  .sort(([first], [second]) => second.source.length - first.source.length);

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function getSyntaxLanguage(value) {
  if (!value) return null;
  const text = String(value);
  return topicAliases.find(([pattern]) => pattern.test(text))?.[1] || null;
}
