import { installSelectionTracking } from './helpers/selection.js';
import { installCodeSpaceNormalization } from './formatting/code-spaces.js';
import { toggleInlineCode } from './formatting/inline-code.js';
import { installCopySource } from './clipboard/copy-source.js';
import { installClozeShortcuts } from './cloze/shortcuts.js';
import { beginPasteLayout, finishPasteLayout } from './paste/layout.js';
import { installEditorStyles } from './styles.js';
import {
  installBlockFormatting,
  toggleEditorBlock,
  indentEditorField,
  unindentEditorField,
} from './formatting/blocks.js';

if (!globalThis.ankiGlobalKitEditor) {
  installSelectionTracking();
  installCodeSpaceNormalization();
  installCopySource();
  installClozeShortcuts();
  installBlockFormatting();

  globalThis.ankiGlobalKitEditor = {
    toggleBlock: toggleEditorBlock,
    toggleInlineCode,
    beginPasteLayout,
    finishPasteLayout,
  };
}

// Note loads reinject the bundle into existing editor webviews. Refresh the
// native action even if the editor was initialized with an older bundle.
globalThis.ankiGlobalKitEditor.indent = indentEditorField;
globalThis.ankiGlobalKitEditor.unindent = unindentEditorField;

installEditorStyles();
