import { getSyntaxLanguage, highlightCodeText } from './tokenizer.js';
import { settings } from '../runtime/settings.js';
import { observers } from '../runtime/state.js';

/** Highlight current and subsequently rendered answer code blocks. */
export function watchSubmittedCodeBlocks() {
  observers.submittedCode?.disconnect();
  observers.submittedCode = null;
  if (!settings.cardReviewSyntaxHighlighting || !document.body) return null;
  const submittedCodeSelector = '.user-answer .box__content pre > code';

  const highlightCode = (code) => {
    if (!(code instanceof Element) || code.dataset.syntaxHighlighted === 'true') return;
    if (!code.matches(submittedCodeSelector)) return;

    const topic = document.querySelector('.topic');
    const language =
      getSyntaxLanguage(code.dataset.language) ||
      (code.dataset.language ? null : getSyntaxLanguage(topic ? topic.textContent : ''));
    if (!language) return;

    code.innerHTML = highlightCodeText(code.textContent, language);
    code.classList.add('shigeSyntax', `language-${language}`);
    code.dataset.syntaxHighlighted = 'true';
  };

  const scan = (node) => {
    if (!(node instanceof Element)) return;
    highlightCode(node);
    node.querySelectorAll(submittedCodeSelector).forEach(highlightCode);
  };

  document.querySelectorAll(submittedCodeSelector).forEach(highlightCode);
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => mutation.addedNodes.forEach(scan));
  });
  observer.observe(document.body, { childList: true, subtree: true });
  observers.submittedCode = observer;
  return observer;
}
