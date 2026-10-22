const STATE_KEY = Symbol.for('ankiGlobalKitEditorRequests');

/** Keep asynchronous request IDs unique when the editor bundle is reinjected. */
export function nextEditorRequestId() {
  const state = (document[STATE_KEY] ||= { nextId: 0 });

  return String(++state.nextId);
}
