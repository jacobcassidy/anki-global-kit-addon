import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';
import { formatBuildMessage } from './build_logging.js';
import { updateDevAddonName } from './dev_metadata.js';
import {
  cardsCssBuildOptions,
  cardsJsBuildOptions,
  editorFieldsCssBuildOptions,
  editorJsBuildOptions,
  editorUiCssBuildOptions,
} from './build.config.js';

execFileSync('python3', [fileURLToPath(new URL('./export_syntax_themes.py', import.meta.url))], {
  stdio: 'inherit',
});

await Promise.all([
  build(cardsJsBuildOptions),
  build(cardsCssBuildOptions),
  build(editorJsBuildOptions),
  build(editorFieldsCssBuildOptions),
  build(editorUiCssBuildOptions),
]);
execFileSync('python3', [fileURLToPath(new URL('./font_notices.py', import.meta.url))], { stdio: 'inherit' });
await updateDevAddonName();
console.log(formatBuildMessage('Built card and editor assets.'));
