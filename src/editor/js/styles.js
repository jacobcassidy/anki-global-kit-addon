import {
  decorateCodeBlock,
  installCodeBlockControls,
} from '../../shared/js/syntax-highlighting/code-block-controls.js';
import { getEditorFields, readStoreValue } from './helpers/fields.js';

const UI_STYLE_ID = 'anki-global-kit-editor-ui-styles';
const FIELD_STYLE_ID = 'anki-global-kit-editor-field-styles';

function setStyle(root, id, css) {
  if (!root) return;

  let style = root.querySelector(`#${id}`);

  if (!css) {
    style?.remove();

    return;
  }

  if (!style) {
    style = document.createElement('style');
    style.id = id;
    root.append(style);
  }

  if (style.textContent !== css) style.textContent = css;
}

async function installFieldStyles() {
  const fields = getEditorFields();

  if (!fields?.length) return;

  await Promise.all(
    fields.map(async (field) => {
      const richText = readStoreValue(field.editingArea?.editingInputs)?.[0];
      const editable = await richText?.element;
      const css = globalThis.ankiGlobalKitEditorStyles?.fields || '';

      setStyle(editable?.getRootNode(), FIELD_STYLE_ID, css);

      editable
        ?.querySelectorAll('pre.agk-code-block')
        .forEach((pre) => decorateCodeBlock(pre, { optionsButton: true }));
    }),
  );
}

export function installEditorStyles() {
  installCodeBlockControls();
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
