const UI_STYLE_ID = 'anki-global-kit-editor-ui-styles';
const FIELD_STYLE_ID = 'anki-global-kit-editor-field-styles';

function setStyle(root, id, css) {
  if (!root || !css) return;
  let style = root.querySelector(`#${id}`);
  if (!style) {
    style = document.createElement('style');
    style.id = id;
    root.append(style);
  }
  if (style.textContent !== css) style.textContent = css;
}

function getStoreValue(store) {
  let value;
  const unsubscribe = store?.subscribe?.((nextValue) => {
    value = nextValue;
  });
  unsubscribe?.();
  return value;
}

async function installFieldStyles() {
  const noteEditor = globalThis.require?.('anki/NoteEditor');
  const fields = noteEditor?.instances?.[0]?.fields;
  if (!fields?.length) return;

  const css = globalThis.ankiGlobalKitEditorStyles?.fields;
  if (!css) return;

  await Promise.all(
    fields.map(async (field) => {
      const richText = getStoreValue(field.editingArea?.editingInputs)?.[0];
      const editable = await richText?.element;
      setStyle(editable?.getRootNode(), FIELD_STYLE_ID, css);
    }),
  );
}

export function installEditorStyles() {
  const styles = globalThis.ankiGlobalKitEditorStyles;
  setStyle(document.head, UI_STYLE_ID, styles?.ui);

  // The note-load hook runs before Anki has finished rebuilding the fields.
  // Retry briefly so styles reach the new fields after each note is loaded.
  const generation = (globalThis.ankiGlobalKitStyleGeneration || 0) + 1;
  globalThis.ankiGlobalKitStyleGeneration = generation;
  let attempts = 0;
  const retry = async () => {
    if (generation !== globalThis.ankiGlobalKitStyleGeneration) return;
    attempts += 1;
    await installFieldStyles();
    if (attempts >= 60) return;
    requestAnimationFrame(retry);
  };
  requestAnimationFrame(retry);
}
