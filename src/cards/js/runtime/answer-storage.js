/** Session storage for answers that survive AnkiDroid card reloads. */
const ANSWER_KEY_PREFIX = 'anki-global-kit:answer:';

export function readStoredAnswer(inputIndex) {
  try {
    return globalThis.sessionStorage?.getItem(`${ANSWER_KEY_PREFIX}${inputIndex}`) ?? undefined;
  } catch (error) {
    console.log(`${error.name}: ${error.message}`);
    return undefined;
  }
}

export function writeStoredAnswer(inputIndex, value) {
  try {
    globalThis.sessionStorage?.setItem(`${ANSWER_KEY_PREFIX}${inputIndex}`, value);
  } catch (error) {
    console.log(`${error.name}: ${error.message}`);
  }
}

/** Remove only the kit's stored answers when starting or completing a card. */
export function clearStoredAnswers() {
  try {
    const storage = globalThis.sessionStorage;
    if (!storage) return;
    for (let index = storage.length - 1; index >= 0; index--) {
      const key = storage.key(index);
      if (key?.startsWith(ANSWER_KEY_PREFIX)) storage.removeItem(key);
    }
  } catch (error) {
    console.log(`${error.name}: ${error.message}`);
  }
}
