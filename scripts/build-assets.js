import { execFileSync } from 'node:child_process';
import { stdout } from 'node:process';
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

const colors = {
  yellow: '\u001B[33m',
  green: '\u001B[32m',
  reset: '\u001B[0m',
};

function runGenerator(script, { colorOutput = false } = {}) {
  const output = execFileSync('python3', [fileURLToPath(new URL(`./${script}`, import.meta.url))], {
    encoding: 'utf8',
    stdio: ['inherit', 'pipe', 'inherit'],
  });

  if (output) {
    const message = output.trimEnd();
    stdout.write(colorOutput ? `${colors.yellow}${message}${colors.reset}\n` : output);
  }
}

runGenerator('export_syntax_themes.py');

await Promise.all([
  build(cardsJsBuildOptions),
  build(cardsCssBuildOptions),
  build(editorJsBuildOptions),
  build(editorFieldsCssBuildOptions),
  build(editorUiCssBuildOptions),
]);
runGenerator('font_notices.py', { colorOutput: true });
await updateDevAddonName();
console.log(`${colors.green}${formatBuildMessage('Built card and editor assets.')}${colors.reset}`);
