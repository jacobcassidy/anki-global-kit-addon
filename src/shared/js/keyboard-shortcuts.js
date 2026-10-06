/** Split Qt shortcut names while retaining a literal plus as the final key. */
export function splitKeyboardShortcut(shortcut) {
  if (shortcut === '+') return ['+'];
  const parts = shortcut.split('+');
  if (shortcut.endsWith('++')) parts.splice(-2, 2, '+');
  return parts;
}

/** Match portable Qt modifier names against browser keyboard events. */
export function matchesKeyboardShortcut(event, shortcut, isMac) {
  const parts = splitKeyboardShortcut(shortcut);
  const key = parts.pop();
  if (!key) return false;
  const modifiers = new Set(parts.map((part) => part.toLowerCase()));
  const codeBlock = modifiers.has('codeblock');
  const eventKey = event.key.toLowerCase();
  // Use the character the platform reports after keyboard remapping. `code`
  // is a fallback for the code-block shortcut when a keyboard layout maps the
  // physical C key to a different character.
  const keyMatches = eventKey === key.toLowerCase() || (codeBlock && event.code === `Key${key.toUpperCase()}`);
  if (!keyMatches) return false;
  const qtCtrl = modifiers.has('ctrl');
  const qtMeta = modifiers.has('meta');
  const ctrl = (isMac ? qtMeta : qtCtrl) || modifiers.has('control') || codeBlock;
  const meta = (isMac ? qtCtrl : qtMeta) || (codeBlock && isMac);
  const alt = modifiers.has('alt') || (codeBlock && !isMac);
  const shift = modifiers.has('shift');
  return event.ctrlKey === ctrl && event.metaKey === meta && event.altKey === alt && event.shiftKey === shift;
}
