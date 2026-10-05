import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const addonWebAssets = `${root}addon/web/assets`;

export const cardsJsBuildOptions = {
  entryPoints: [`${root}src/cards/js/index.js`],
  outfile: `${addonWebAssets}/js/_anki-global-kit.min.js`,
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: ['es2018'],
  legalComments: 'none',
  minify: true,
  banner: { js: 'var hasMyCustomScript = true;' },
  loader: { '.svg': 'text' },
};

export const cardsCssBuildOptions = {
  entryPoints: [`${root}src/cards/css/index.css`],
  outfile: `${addonWebAssets}/css/_anki-global-kit.min.css`,
  bundle: true,
  legalComments: 'none',
  minify: true,
  external: ['*.woff', '*.woff2'],
};

export const editorFieldsCssBuildOptions = {
  entryPoints: [`${root}src/editor/css/editor-fields.css`],
  outfile: `${root}addon/desktop/editor/assets/css/editor-fields.min.css`,
  bundle: true,
  legalComments: 'none',
  minify: true,
};

export const editorUiCssBuildOptions = {
  entryPoints: [`${root}src/editor/css/editor-ui.css`],
  outfile: `${root}addon/desktop/editor/assets/css/editor-ui.min.css`,
  bundle: true,
  legalComments: 'none',
  minify: true,
};

export const editorJsBuildOptions = {
  entryPoints: [`${root}src/editor/js/index.js`],
  outfile: `${root}addon/desktop/editor/assets/js/editor.min.js`,
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: ['es2020'],
  legalComments: 'none',
  minify: true,
};
