import { getEditorSelection, installSelectionTracking } from './helpers/selection.js';
import { installCodeSpaceNormalization } from './formatting/code-spaces.js';
import { toggleInlineCode } from './formatting/inline-code.js';
import { installCopySource } from './clipboard/copy-source.js';
import { installClozeShortcuts } from './cloze/shortcuts.js';
import { beginPasteLayout, finishPasteLayout } from './paste/layout.js';
import { installEditorStyles } from './styles.js';
import { installBlockFormatting, toggleEditorBlock } from './formatting/blocks.js';

if (!globalThis.ankiGlobalKitEditor) {
  installSelectionTracking();
  installCodeSpaceNormalization();
  installCopySource();
  installClozeShortcuts();
  installBlockFormatting();

  globalThis.ankiGlobalKitEditor = {
    toggleBlock: toggleEditorBlock,
    toggleInlineCode() {
      return toggleInlineCode.call({ node: getEditorSelection()?.focusNode }, '<code>', '</code>');
    },
    beginPasteLayout,
    finishPasteLayout,
  };
}

installEditorStyles();
