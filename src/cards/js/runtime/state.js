/** State shared by answer input and output rendering. */
export const state = {
  outputAnswers: undefined,
  boundInputs: new WeakSet(),
  renderedPlainOutputs: new WeakSet(),
};

/** Retain observer handles if the card bundle is loaded again in this webview. */
export const observers = (globalThis.ankiGlobalKitObservers ??= {
  cardChanges: null,
  submittedCode: null,
});
