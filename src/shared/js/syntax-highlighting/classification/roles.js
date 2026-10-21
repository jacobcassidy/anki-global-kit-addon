/** Convert language-neutral classifications into the shared theme's roles. */
export function themeRole({ role, builtin = false }) {
  if (builtin) {
    if (role === 'constant') return 'builtin-constant';
    if (role === 'variable') return 'library-variable';
    if (role === 'function' || role === 'class') return 'builtin';
  }

  if (role === 'property') return 'attribute';

  return role;
}
