const MENU_ID = 'anki-global-kit-language-menu';
const LANGUAGE_BUTTON_SELECTOR = '[data-command="anki_global_kit_syntax_language"]';
let dismissMenu;
let suppressNextMenuResponse = false;
let languageOptions = [];

function refreshLanguageButton() {
  const language = globalThis.ankiGlobalKitEditor?.getActiveLanguage?.();
  const label = languageOptions.find(({ alias }) => alias === language)?.label;
  const button = document.querySelector(LANGUAGE_BUTTON_SELECTOR);

  if (button && label) button.textContent = label;
}

function closeLanguageMenu() {
  dismissMenu?.();
  dismissMenu = null;
  document.getElementById(MENU_ID)?.remove();
}

export function showLanguageMenu(languages, current, anchor) {
  if (suppressNextMenuResponse) {
    suppressNextMenuResponse = false;
    return;
  }

  if (document.getElementById(MENU_ID)) {
    closeLanguageMenu();
    return;
  }

  closeLanguageMenu();

  const activeLanguage = globalThis.ankiGlobalKitEditor?.getActiveLanguage?.(current) || current;
  const activeLabel = languages.find(({ alias }) => alias === activeLanguage)?.label;
  const languageButton = document.querySelector('[data-command="anki_global_kit_syntax_language"]');

  if (languageButton && activeLabel) languageButton.textContent = activeLabel;

  const menu = document.createElement('div');
  menu.id = MENU_ID;
  menu.className = 'anki-global-kit-language-menu';
  menu.setAttribute('role', 'menu');

  const rect = Array.isArray(anchor)
    ? anchor
    : (() => {
        const button = document.querySelector(LANGUAGE_BUTTON_SELECTOR);
        const bounds = button?.getBoundingClientRect();

        return bounds ? [bounds.left, bounds.bottom] : null;
      })();

  if (!rect) return;

  menu.style.left = `${Math.max(8, Math.min(rect[0], innerWidth - 240))}px`;
  menu.style.top = `${rect[1] + 6}px`;

  if (activeLanguage) {
    const selected = document.createElement('div');
    selected.className = 'anki-global-kit-language-menu__current';
    selected.textContent = activeLabel || activeLanguage;
    selected.setAttribute('role', 'menuitem');
    selected.tabIndex = 0;
    selected.addEventListener('mousedown', (event) => event.preventDefault());
    selected.addEventListener('click', closeLanguageMenu);
    selected.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') closeLanguageMenu();
    });
    menu.append(selected);

    const divider = document.createElement('div');
    divider.className = 'anki-global-kit-language-menu__divider';
    divider.setAttribute('role', 'separator');
    menu.append(divider);
  }

  for (const { alias, label } of languages) {
    if (alias === activeLanguage) continue;

    const item = document.createElement('div');
    item.className = 'anki-global-kit-language-menu__item';
    item.textContent = label;
    item.setAttribute('role', 'menuitem');
    item.tabIndex = 0;
    item.addEventListener('mousedown', (event) => event.preventDefault());
    const choose = () => {
      closeLanguageMenu();
      globalThis.pycmd?.(`anki-global-kit:language-choice:${JSON.stringify(alias)}`);
    };
    item.addEventListener('click', () => {
      choose();
    });
    item.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        choose();
      }
    });
    menu.append(item);
  }

  document.body.append(menu);
  const dismiss = (event) => {
    if (event.composedPath().some((target) => target?.matches?.(LANGUAGE_BUTTON_SELECTOR))) {
      return;
    }

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
  api.setLanguageOptions = (languages) => {
    languageOptions = Array.isArray(languages) ? languages : [];
    refreshLanguageButton();
  };

  if (!api.languageButtonToggleInstalled) {
    api.languageButtonToggleInstalled = true;
    document.addEventListener(
      'click',
      (event) => {
        if (!event.composedPath().some((target) => target?.matches?.(LANGUAGE_BUTTON_SELECTOR))) {
          return;
        }

        if (document.getElementById(MENU_ID)) {
          closeLanguageMenu();
          suppressNextMenuResponse = true;
        } else {
          suppressNextMenuResponse = false;
        }
      },
      true,
    );
  }

  if (!api.languageButtonTrackingInstalled) {
    api.languageButtonTrackingInstalled = true;
    document.addEventListener('selectionchange', refreshLanguageButton);
    document.addEventListener('focusin', refreshLanguageButton);
  }
}
