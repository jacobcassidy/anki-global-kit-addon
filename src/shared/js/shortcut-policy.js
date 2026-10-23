import { splitKeyboardShortcut } from './keyboard-shortcuts.js';

/** Keep Tab and Backtab available for native focus navigation. */
export function recoverIndentationShortcut(shortcut, fallback) {
  if (typeof shortcut !== 'string') return fallback;
  const key = splitKeyboardShortcut(shortcut).at(-1).trim().toLowerCase();

  return ['tab', 'backtab'].includes(key) ? fallback : shortcut;
}

/** Card-only aliases must never reach native editor shortcut matching. */
export function recoverEditorShortcut(shortcut, fallback) {
  return typeof shortcut !== 'string' || shortcut.toLowerCase().startsWith('codeblock+') ? fallback : shortcut;
}
