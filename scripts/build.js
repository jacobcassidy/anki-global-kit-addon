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
console.log('Built card and editor assets.');
