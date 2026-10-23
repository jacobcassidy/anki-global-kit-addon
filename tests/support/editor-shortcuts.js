import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Keep keyboard fixtures aligned with the definitions injected by Anki Desktop.
export const editorBlockShortcuts = JSON.parse(
  execFileSync(
    'python3',
    [
      '-c',
      'import json; from tests.support.anki_stubs import load_shortcut_helpers; print(json.dumps(load_shortcut_helpers().EDITOR_BLOCK_SHORTCUTS))',
    ],
    { cwd: fileURLToPath(new URL('../../', import.meta.url)), encoding: 'utf8' },
  ),
);
