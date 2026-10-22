import { installSelectionTracking } from './helpers/selection.js';
import { installCodeSpaceNormalization } from './formatting/code-spaces.js';
import { toggleInlineCode } from './formatting/inline-code.js';
import { installCopySource } from './clipboard/copy-source.js';
import { installMarkdownHighlighting, convertMarkdown } from './formatting/markdown.js';
import { installCodeBlockHighlighting } from './formatting/code-block.js';
import { exitCodeBlock } from './formatting/code-block-editing.js';
import { installClozeShortcuts } from './cloze/shortcuts.js';
import { installEditorStyles } from './styles.js';
import { refreshEditorToolbar } from './toolbar.js';
import { installLanguageMenu } from './language-menu.js';
import {
  installBlockFormatting,
  toggleEditorBlock,
  indentEditorField,
  unindentEditorField,
} from './formatting/blocks.js';

installSelectionTracking();
installCodeBlockHighlighting();
installLanguageMenu();

if (!globalThis.ankiGlobalKitEditor) {
  installCodeSpaceNormalization();
  installCopySource();
  installClozeShortcuts();
  installBlockFormatting();

  globalThis.ankiGlobalKitEditor = {
    toggleBlock: toggleEditorBlock,
    toggleInlineCode,
    convertMarkdown,
  };
}

// Note loads reinject the bundle into existing editor webviews. Refresh the
// native action even if the editor was initialized with an older bundle.
globalThis.ankiGlobalKitEditor.indent = indentEditorField;
globalThis.ankiGlobalKitEditor.unindent = unindentEditorField;
globalThis.ankiGlobalKitEditor.exitCodeBlock = exitCodeBlock;
globalThis.ankiGlobalKitEditor.convertMarkdown = convertMarkdown;
installMarkdownHighlighting();

installEditorStyles();
refreshEditorToolbar();
