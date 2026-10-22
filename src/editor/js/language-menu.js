const MENU_ID = 'anki-global-kit-language-menu';
let dismissMenu;

function closeLanguageMenu() {
  dismissMenu?.();
  dismissMenu = null;
  document.getElementById(MENU_ID)?.remove();
}

export function showLanguageMenu(languages, current, anchor) {
  closeLanguageMenu();

  const menu = document.createElement('div');
  menu.id = MENU_ID;
  menu.className = 'anki-global-kit-language-menu';
  menu.setAttribute('role', 'menu');

  const rect = Array.isArray(anchor)
    ? anchor
    : (() => {
        const button = document.querySelector('[data-command="anki_global_kit_syntax_language"]');
        const bounds = button?.getBoundingClientRect();

        return bounds ? [bounds.left, bounds.bottom] : null;
      })();

  if (!rect) return;

  menu.style.left = `${Math.max(8, Math.min(rect[0], innerWidth - 240))}px`;
  menu.style.top = `${rect[1] + 8}px`;

  if (current) {
    const selected = document.createElement('button');
    selected.type = 'button';
    selected.className = 'anki-global-kit-language-menu__current';
    selected.textContent = languages.find(({ alias }) => alias === current)?.label || current;
    selected.setAttribute('role', 'menuitem');
    selected.addEventListener('click', closeLanguageMenu);
    menu.append(selected);

    const divider = document.createElement('div');
    divider.className = 'anki-global-kit-language-menu__divider';
    divider.setAttribute('role', 'separator');
    menu.append(divider);
  }

  for (const { alias, label } of languages) {
    if (alias === current) continue;

    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'anki-global-kit-language-menu__item';
    item.textContent = label;
    item.setAttribute('role', 'menuitem');
    item.addEventListener('click', () => {
      closeLanguageMenu();
      globalThis.pycmd?.(`anki-global-kit:language-choice:${JSON.stringify(alias)}`);
    });
    menu.append(item);
  }

  document.body.append(menu);
  const dismiss = (event) => {
    if (!menu.contains(event.target)) closeLanguageMenu();
  };
  const keydown = (event) => {
    if (event.key === 'Escape') closeLanguageMenu();
  };

  dismissMenu = () => {
    document.removeEventListener('mousedown', dismiss, true);
    document.removeEventListener('keydown', keydown);
  };
  document.addEventListener('mousedown', dismiss, true);
  document.addEventListener('keydown', keydown);
}

export function installLanguageMenu() {
  const api = (globalThis.ankiGlobalKitEditor ||= {});
  api.showLanguageMenu = showLanguageMenu;
}
