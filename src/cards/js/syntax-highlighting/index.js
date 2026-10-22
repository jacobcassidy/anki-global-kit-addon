import { highlightReviewCode } from './engine.js';
import { getSyntaxLanguage } from '../../../shared/js/syntax-highlighting/languages.js';
import { settings } from '../runtime/settings.js';
import { observers } from '../runtime/state.js';
import { createClassificationBudget } from '../../../shared/js/syntax-highlighting/classification/index.js';

const MAX_BLOCK_CHARACTERS = 10_000;
const MAX_ANSWER_CHARACTERS = 20_000;
const MAX_ANSWER_BLOCKS = 20;

/** Highlight current and subsequently rendered answer code blocks. */
export function watchSubmittedCodeBlocks() {
  observers.submittedCode?.disconnect();
  observers.submittedCode = null;
  if (!settings.cardReviewSyntaxHighlighting || !document.body) return null;

  const submittedCodeSelector = ':scope pre > code';
  const processAnswer = (answer) => {
    const budget = createClassificationBudget(25);
    let totalCharacters = 0;
    let processedBlocks = 0;
    const blocks = [...answer.querySelectorAll(submittedCodeSelector)].filter(
      (code) => !code.closest('.agk-code-block') && code.dataset.syntaxHighlighted !== 'true',
    );

    for (const code of blocks) {
      if (processedBlocks >= MAX_ANSWER_BLOCKS || totalCharacters >= MAX_ANSWER_CHARACTERS) break;
      processedBlocks += 1;

      const source = code.textContent || '';
      const sourceLength = Array.from(source).length;
      const explicitLanguage =
        code.dataset.language ||
        [...code.classList].find((name) => name.startsWith('language-'))?.slice('language-'.length);
      const language = explicitLanguage
        ? getSyntaxLanguage(explicitLanguage)
        : getSyntaxLanguage(document.querySelector('.topic')?.textContent || '');

      if (sourceLength > MAX_BLOCK_CHARACTERS) continue;

      if (!language) continue;
      if (totalCharacters + sourceLength > MAX_ANSWER_CHARACTERS) break;

      totalCharacters += sourceLength;
      const highlighted = highlightReviewCode(source, language, { budget });
      if (highlighted === null) continue;

      code.innerHTML = highlighted;
      code.classList.add('syntax-highlights', `language-${language}`);
      code.dataset.syntaxHighlighted = 'true';
    }
  };

  const processNode = (node) => {
    if (!(node instanceof Element)) return;
    const answers = [];
    if (node.matches('.user-answer .box__content')) answers.push(node);
    answers.push(...node.querySelectorAll('.user-answer .box__content'));
    answers.forEach(processAnswer);
  };

  document.querySelectorAll('.user-answer .box__content').forEach(processAnswer);
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => mutation.addedNodes.forEach(processNode));
  });
  observer.observe(document.body, { childList: true, subtree: true });
  observers.submittedCode = observer;
  return observer;
}
