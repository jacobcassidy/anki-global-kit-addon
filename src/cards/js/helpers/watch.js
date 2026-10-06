import { isAnkiDroid } from '../runtime/platform.js';
import { observers } from '../runtime/state.js';

/** Run an initializer and rerun it when Anki replaces the current card. */
export function watchCardChanges(callback) {
  observers.cardChanges?.disconnect();
  observers.cardChanges = null;
  callback();

  const targetNode = isAnkiDroid ? document.querySelector('body') : document.getElementById('qa');
  if (!targetNode) return null;
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') callback();
      break;
    }
  });
  observer.observe(targetNode, { childList: true });
  observers.cardChanges = observer;
  return observer;
}
