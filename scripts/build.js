import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';
import {
  cardsCssBuildOptions,
  cardsJsBuildOptions,
  editorFieldsCssBuildOptions,
  editorJsBuildOptions,
  editorUiCssBuildOptions,
} from './build.config.js';

await Promise.all([
  build(cardsJsBuildOptions),
  build(cardsCssBuildOptions),
  build(editorJsBuildOptions),
  build(editorFieldsCssBuildOptions),
  build(editorUiCssBuildOptions),
]);
execFileSync('python3', [fileURLToPath(new URL('./font_notices.py', import.meta.url))], { stdio: 'inherit' });
console.log('Built card and editor assets.');
