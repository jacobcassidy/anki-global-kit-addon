import { isAnkiDroid, isAnkiPC, isAnkiWeb } from '../runtime/platform.js';
import { state } from '../runtime/state.js';
import {
  handleMarkdownListEnter,
  handleMarkdownShortcuts,
  toggleMarkdownBlock,
  toggleMarkdownFormatting,
} from './markdown-shortcuts.js';
import { handleTabIndentation, changeTextareaIndentation } from './tab-navigation.js';
import { reportQuestionShortcutFocus } from './shortcut-focus.js';
import { settings } from '../runtime/settings.js';
import boldIcon from '../../../../addon/shared/assets/icons/text-bold.svg';
import italicIcon from '../../../../addon/shared/assets/icons/text-italic.svg';
import strikethroughIcon from '../../../../addon/shared/assets/icons/text-strikethrough.svg';
import codeBlockIcon from '../../../../addon/shared/assets/icons/code-block.svg';
import inlineCodeIcon from '../../../../addon/shared/assets/icons/code-inline.svg';
import unorderedListIcon from '../../../../addon/shared/assets/icons/list-unordered.svg';
import orderedListIcon from '../../../../addon/shared/assets/icons/list-ordered.svg';
import indentIncreaseIcon from '../../../../addon/shared/assets/icons/indent-increase.svg';
import indentDecreaseIcon from '../../../../addon/shared/assets/icons/indent-decrease.svg';
import blockquoteIcon from '../../../../addon/shared/assets/icons/blockquote.svg';

/**
 * Watch question textareas and connect their editing and submission handlers.
 */
export function watchQuestionInputs() {
  const questionInputs = document.querySelectorAll('.question-input');
  if (questionInputs.length < 1) return;

  if (isAnkiPC) {
    globalThis.ankiGlobalKitIndentQuestion = () => {
      const input = document.activeElement;
      if (settings.cardInputTabIndentation && input?.matches('.question-input')) changeTextareaIndentation(input);
    };
    globalThis.ankiGlobalKitUnindentQuestion = () => {
      const input = document.activeElement;
      if (settings.cardInputTabIndentation && input?.matches('.question-input')) {
        changeTextareaIndentation(input, true);
      }
    };
  }

  if (isAnkiPC) {
    globalThis.ankiGlobalKitReportQuestionFocus = () =>
      reportQuestionShortcutFocus(true, {
        ...(settings.cardInputMarkdownShortcuts ? settings.cardInputMarkdownShortcutsMap : {}),
        ...(settings.cardInputTabIndentation ? settings.cardInputTabShortcutsMap : {}),
      });
    globalThis.ankiGlobalKitReportQuestionFocus();
  }

  state.outputAnswers = Array.from(questionInputs, (questionInput) => questionInput.value);

  questionInputs.forEach((questionInput, inputIndex) => {
    if (state.boundInputs.has(questionInput)) return;
    state.boundInputs.add(questionInput);

    resizeQuestionInput(questionInput);
    questionInput.addEventListener('input', () => resizeQuestionInput(questionInput));

    if (isAnkiPC) {
      const reportFocus = () => {
        globalThis.ankiGlobalKitReportQuestionFocus();
      };
      questionInput.addEventListener('focus', reportFocus);
      // Card initialization can focus the textarea before handlers are bound.
      if (document.activeElement === questionInput) reportFocus();
      questionInput.addEventListener('blur', () => {
        queueMicrotask(() => {
          if (!document.activeElement?.matches('.question-input')) {
            globalThis.pycmd('anki-global-kit:question-input-blur');
          }
        });
      });
    }

    questionInput.addEventListener(
      'keydown',
      (event) => {
        if (handleMarkdownListEnter(questionInput, event)) return;
        if (
          handleMarkdownShortcuts(questionInput, event, {
            markdownEnabled: settings.cardInputMarkdownShortcuts,
            shortcuts: settings.cardInputMarkdownShortcutsMap,
          })
        )
          return;
        if (settings.cardInputTabIndentation) {
          handleTabIndentation(questionInput, event, settings.cardInputTabShortcutsMap);
        }
      },
      { capture: true },
    );

    if (settings.cardToolbarEnabled) addFormattingToolbar(questionInput);

    handleQuestionInputSubmission(questionInput, inputIndex);
  });
}

function resizeQuestionInput(textarea) {
  textarea.style.blockSize = 'auto';
  textarea.style.blockSize = `${Math.min(textarea.scrollHeight, 640)}px`;
}

function addFormattingToolbar(textarea) {
  const toolbar = document.createElement('div');
  toolbar.className = 'card-formatting-toolbar';
  toolbar.setAttribute('role', 'toolbar');
  toolbar.setAttribute('aria-label', 'Markdown formatting');

  const shortcuts = settings.cardInputMarkdownShortcutsMap;
  const formatShortcut = (shortcut) => {
    if (!shortcut) return '';
    if (shortcut.startsWith('CodeBlock+'))
      return navigator.platform.startsWith('Mac')
        ? '⌃⌘' + shortcut.split('+').pop()
        : 'Ctrl+Alt+' + shortcut.split('+').pop();
    const isMac = navigator.platform.startsWith('Mac');
    const labels = isMac
      ? { Ctrl: '⌘', Meta: '⌃', Control: '⌃', Alt: '⌥', Shift: '⇧' }
      : { Ctrl: 'Ctrl', Meta: 'Meta', Control: 'Ctrl', Alt: 'Alt', Shift: 'Shift' };
    return shortcut
      .split('+')
      .map((part) => labels[part] ?? part)
      .join(isMac ? '' : '+');
  };
  const actions = [
    {
      enabled: settings.cardToolbarBold,
      name: 'Bold',
      icon: boldIcon,
      prefix: '**',
      suffix: '**',
      shortcut: formatShortcut(shortcuts.bold),
      className: 'is-bold',
      group: 'Text formatting',
    },
    {
      enabled: settings.cardToolbarItalic,
      name: 'Italic',
      icon: italicIcon,
      prefix: '*',
      suffix: '*',
      shortcut: formatShortcut(shortcuts.italic),
      className: 'is-italic',
      group: 'Text formatting',
    },
    {
      enabled: settings.cardToolbarStrikethrough,
      name: 'Strikethrough',
      icon: strikethroughIcon,
      prefix: '~~',
      suffix: '~~',
      shortcut: formatShortcut(shortcuts.strikethrough),
      className: 'is-strikethrough',
      group: 'Text formatting',
    },
    {
      enabled: settings.cardToolbarCodeBlock,
      name: 'Code block',
      icon: codeBlockIcon,
      prefix: '```\n',
      suffix: '\n```',
      shortcut: formatShortcut(shortcuts.codeBlock),
      className: 'is-code-block',
      group: 'Code',
    },
    {
      enabled: settings.cardToolbarInlineCode,
      name: 'Inline code',
      icon: inlineCodeIcon,
      prefix: '`',
      suffix: '`',
      shortcut: formatShortcut(shortcuts.inlineCode),
      className: 'is-inline-code',
      group: 'Code',
    },
    {
      enabled: settings.cardToolbarUnorderedList,
      name: 'Unordered list',
      icon: unorderedListIcon,
      shortcut: formatShortcut(shortcuts.unorderedList),
      blockMarker: 'unordered-list',
      className: 'is-unordered-list',
      group: 'Lists and quotes',
    },
    {
      enabled: settings.cardToolbarOrderedList,
      name: 'Ordered list',
      icon: orderedListIcon,
      shortcut: formatShortcut(shortcuts.orderedList),
      blockMarker: 'ordered-list',
      className: 'is-ordered-list',
      group: 'Lists and quotes',
    },
    {
      enabled: settings.cardToolbarIndentIncrease,
      name: 'Increase indent',
      icon: indentIncreaseIcon,
      indentation: 'increase',
      shortcut: settings.cardInputTabIndentation ? formatShortcut(settings.cardInputTabShortcutsMap.increase) : '',
      className: 'is-indent-increase',
      group: 'Lists and quotes',
    },
    {
      enabled: settings.cardToolbarIndentDecrease,
      name: 'Decrease indent',
      icon: indentDecreaseIcon,
      indentation: 'decrease',
      shortcut: settings.cardInputTabIndentation ? formatShortcut(settings.cardInputTabShortcutsMap.decrease) : '',
      className: 'is-indent-decrease',
      group: 'Lists and quotes',
    },
    {
      enabled: settings.cardToolbarBlockquote,
      name: 'Blockquote',
      icon: blockquoteIcon,
      shortcut: formatShortcut(shortcuts.blockquote),
      blockMarker: 'blockquote',
      className: 'is-blockquote',
      group: 'Lists and quotes',
    },
  ];

  const groups = new Map();
  actions
    .filter((action) => action.enabled)
    .forEach((action) => {
      let group = groups.get(action.group);
      if (!group) {
        group = document.createElement('div');
        group.className = 'toolbar-group';
        group.setAttribute('role', 'group');
        group.setAttribute('aria-label', action.group);
        groups.set(action.group, group);
      }

      const button = document.createElement('button');
      button.className = `card-formatting-toolbar__button ${action.className}`;
      button.type = 'button';
      button.tabIndex = -1;
      button.innerHTML = action.icon;
      const label = action.shortcut ? `${action.name} (${action.shortcut})` : action.name;
      button.title = label;
      button.setAttribute('aria-label', label);
      button.addEventListener('mousedown', (event) => event.preventDefault());
      button.addEventListener('click', () => {
        const selectionStart = textarea.selectionStart;
        const selectionEnd = textarea.selectionEnd;
        textarea.focus();
        textarea.setSelectionRange(selectionStart, selectionEnd);
        if (action.indentation) {
          changeTextareaIndentation(textarea, action.indentation === 'decrease');
        } else if (action.blockMarker) {
          toggleMarkdownBlock(textarea, action.blockMarker);
        } else {
          toggleMarkdownFormatting(textarea, action.prefix, action.suffix);
        }
      });
      group.append(button);
    });

  ['Text formatting', 'Lists and quotes', 'Code'].forEach((groupName) => {
    const group = groups.get(groupName);
    if (group) toolbar.append(group);
  });

  if (toolbar.childElementCount) textarea.insertAdjacentElement('beforebegin', toolbar);
}

/**
 * Track an answer textarea's value and submit it with the client's answer shortcut.
 */
export function handleQuestionInputSubmission(questionInput, inputIndex) {
  questionInput.addEventListener('input', (event) => {
    const inputValue = event.currentTarget.value;

    // Store input data on AnkiDroid
    if (isAnkiDroid) {
      try {
        sessionStorage.setItem(inputIndex, inputValue);
      } catch (error) {
        console.log(`${error.name}: ${error.message}`);
      }
      // Store input data on AnkiPC, AnkiWeb, & AnkiIOS
    } else {
      state.outputAnswers.splice(inputIndex, 1, inputValue);
    }
  });

  // Return data on AnkiPC keypress.
  if (isAnkiPC) {
    const isMac = navigator.platform.startsWith('Mac');
    questionInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && (isMac ? event.metaKey : event.ctrlKey)) {
        event.preventDefault();
        globalThis.pycmd('ans');
      }
    });

    // Return data on AnkiWeb keypress.
  } else if (isAnkiWeb) {
    questionInput.addEventListener('keydown', (event) => {
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        globalThis.study.drawAnswer();
      }
    });
  }
}
