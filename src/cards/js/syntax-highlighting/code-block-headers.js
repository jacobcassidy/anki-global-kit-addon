import {
  decorateCodeBlock,
  installCodeBlockControls,
} from '../../../shared/js/syntax-highlighting/code-block-controls.js';
import { observers } from '../runtime/state.js';

/** Include saved blocks and newly rendered Markdown without re-highlighting code. */
export function watchCodeBlockHeaders() {
  observers.codeBlockHeaders?.disconnect();
  installCodeBlockControls();

  const process = (node) => {
    if (node.nodeType !== 1) return;

    const pre = node.closest('pre');

    if (pre) decorateCodeBlock(pre);

    node.querySelectorAll('pre').forEach((block) => decorateCodeBlock(block));
  };

  process(document.body);

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach(process);
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
  observers.codeBlockHeaders = observer;

  return observer;
}
