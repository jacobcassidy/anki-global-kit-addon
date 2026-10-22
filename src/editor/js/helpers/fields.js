/** Read a synchronous editor store without leaving a subscription active. */
export function readStoreValue(store) {
  let value;
  const unsubscribe = store?.subscribe?.((nextValue) => {
    value = nextValue;
  });

  unsubscribe?.();

  return value;
}

/** Resolve the fields exposed by Anki's current note editor. */
export function getEditorFields() {
  return globalThis.require?.('anki/NoteEditor')?.instances?.[0]?.fields || [];
}

/** Read plain Topic text from the field metadata supported by the editor. */
export function getEditorTopicText() {
  const topic = getEditorFields().find((field) =>
    [field.name, field.fieldName, field.field?.name].some(
      (name) => typeof name === 'string' && name.trim().toLowerCase() === 'topic',
    ),
  );
  const html = readStoreValue(topic?.editingArea?.content);

  if (typeof html !== 'string' || !html) return '';

  const content = document.createElement('template');

  content.innerHTML = html;

  return content.content.textContent || '';
}
