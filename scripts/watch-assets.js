import { execFileSync } from 'node:child_process';
import { watch } from 'node:fs';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { context, formatMessages } from 'esbuild';
import { formatBuildMessage } from './build_logging.js';
import { updateDevAddonName } from './dev_metadata.js';
import {
  cardsCssBuildOptions,
  cardsJsBuildOptions,
  editorFieldsCssBuildOptions,
  editorJsBuildOptions,
  editorUiCssBuildOptions,
} from './build.config.js';

const colors = {
  yellow: '\u001B[33m',
  green: '\u001B[32m',
  red: '\u001B[31m',
  reset: '\u001B[0m',
};

const contentByPath = new Map();
const pendingChanges = new Set();
const inputsByOutput = new Map();
const changedOutputs = new Set();
let changeTimer;

const repositoryRoot = fileURLToPath(new URL('../', import.meta.url));
const themeSourceDirectory = resolve(repositoryRoot, 'addon/desktop/syntax_highlighting');
const fontDirectory = resolve(repositoryRoot, 'addon/assets/fonts');
const fontLicenseDirectory = join(fontDirectory, 'licenses');
const fontAttributionPath = join(fontDirectory, 'FONT-LICENSES.md');

function runGenerator(script) {
  execFileSync('python3', [fileURLToPath(new URL(`./${script}`, import.meta.url))], {
    stdio: 'inherit',
  });
}

function tryRunGenerator(script) {
  try {
    runGenerator(script);
  } catch (error) {
    console.error(`${colorize('Generator failed:', colors.red)} ${script}: ${error.message}`);
  }
}

runGenerator('export_syntax_themes.py');
runGenerator('font_notices.py');

await updateDevAddonName();
// Watch the directory so replacing manifest.json during a save remains visible.
let metadataRefresh = Promise.resolve();
watch(fileURLToPath(new URL('../addon/', import.meta.url)), (_eventType, filename) => {
  if (filename && filename.toString() !== 'manifest.json') return;
  metadataRefresh = metadataRefresh
    .then(() => updateDevAddonName())
    .catch((error) => {
      console.error(`Could not refresh the development add-on name: ${error.message}`);
    });
});

function colorize(text, color) {
  return `${color}${text}${colors.reset}`;
}

async function indexDirectory(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await indexDirectory(path);
    } else if (entry.isFile()) {
      contentByPath.set(path, await readFile(path));
    }
  }
}

for (const sourceDirectory of [
  'src/cards/js',
  'src/cards/css',
  'src/editor/js',
  'src/editor/css',
  'src/shared/js',
  'src/shared/css',
  'addon/assets/icons',
  'addon/desktop/syntax_highlighting',
  'addon/assets/fonts',
]) {
  const absoluteDirectory = fileURLToPath(new URL(`../${sourceDirectory}`, import.meta.url));
  await indexDirectory(absoluteDirectory);

  const watcher = watch(absoluteDirectory, { recursive: true });
  watcher.on('change', (_eventType, filename) => {
    if (!filename) return;
    const path = join(absoluteDirectory, filename.toString());
    pendingChanges.add(path);

    clearTimeout(changeTimer);
    changeTimer = setTimeout(async () => {
      let regenerateThemeCss = false;
      let regenerateFontNotice = false;

      for (const changedPath of pendingChanges) {
        const content = await readFile(changedPath).catch(() => null);
        const previousContent = contentByPath.get(changedPath);
        if (content && previousContent?.equals(content)) continue;
        if (!content && !previousContent) continue;

        if (content) contentByPath.set(changedPath, content);
        else contentByPath.delete(changedPath);

        const absolutePath = resolve(changedPath);

        if (absolutePath.startsWith(`${themeSourceDirectory}${sep}`) && absolutePath.endsWith('.py')) {
          regenerateThemeCss = true;
        }

        if (
          absolutePath === fontAttributionPath ||
          (absolutePath.startsWith(`${fontLicenseDirectory}${sep}`) && absolutePath.endsWith('.txt'))
        ) {
          regenerateFontNotice = true;
        }

        for (const [outfile, inputs] of inputsByOutput) {
          if (inputs.has(absolutePath)) changedOutputs.add(outfile);
        }
        const file = relative(fileURLToPath(new URL('../', import.meta.url)), changedPath);
        console.log(colorize(`Changed: ${file}`, colors.yellow));
      }
      pendingChanges.clear();

      if (regenerateThemeCss) tryRunGenerator('export_syntax_themes.py');

      if (regenerateFontNotice) tryRunGenerator('font_notices.py');
    }, 120);
  });
}

function createWatchPlugin(outfile) {
  let initialBuild = true;

  return {
    name: 'watch-logging',
    setup(build) {
      build.onEnd(async (result) => {
        const wasInitialBuild = initialBuild;
        initialBuild = false;
        const hasErrors = result.errors.length > 0;
        if (result.metafile) {
          const inputs = Object.values(result.metafile.outputs).flatMap((output) =>
            Object.keys(output.inputs).map((input) => resolve(input)),
          );
          inputsByOutput.set(outfile, new Set(inputs));
        }

        if (!hasErrors) {
          await Promise.all(result.outputFiles.map((outputFile) => writeFile(outputFile.path, outputFile.contents)));
        }

        // Let the filesystem watcher compare contents and print changed paths first.
        await new Promise((resolve) => setTimeout(resolve, 180));

        for (const warning of result.warnings) {
          const [formatted] = await formatMessages([warning], {
            kind: 'warning',
            color: true,
          });
          console.warn(`${colorize('Warning:', colors.red)}\n${formatted}`);
        }
        for (const error of result.errors) {
          const [formatted] = await formatMessages([error], {
            kind: 'error',
            color: true,
          });
          console.error(`${colorize('Error:', colors.red)}\n${formatted}`);
        }

        if (!wasInitialBuild && !hasErrors && changedOutputs.delete(outfile)) {
          const file = relative(fileURLToPath(new URL('../', import.meta.url)), outfile);
          console.log(colorize(formatBuildMessage(`Rebuilt: ${file}`), colors.green));
        }
      });
    },
  };
}

const contexts = await Promise.all(
  [
    cardsJsBuildOptions,
    cardsCssBuildOptions,
    editorJsBuildOptions,
    editorFieldsCssBuildOptions,
    editorUiCssBuildOptions,
  ].map((options) =>
    context({
      ...options,
      metafile: true,
      write: false,
      logLevel: 'silent',
      plugins: [createWatchPlugin(options.outfile)],
    }),
  ),
);

await Promise.all(contexts.map((buildContext) => buildContext.watch()));
console.log(
  'Watching card, editor, and shared sources plus icons, syntax theme sources, and font notices. Press Ctrl+C to stop.',
);
