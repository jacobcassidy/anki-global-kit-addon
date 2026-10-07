import { lstat, mkdir, realpath, symlink } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const addon = fileURLToPath(new URL('../addon/', import.meta.url));

function defaultAddonsFolder() {
  if (process.env.ANKI_BASE) return join(process.env.ANKI_BASE, 'addons21');
  switch (process.platform) {
    case 'darwin':
      return join(homedir(), 'Library', 'Application Support', 'Anki2', 'addons21');
    case 'win32':
      return join(process.env.APPDATA || join(homedir(), 'AppData', 'Roaming'), 'Anki2', 'addons21');
    case 'linux':
      return join(process.env.XDG_DATA_HOME || join(homedir(), '.local', 'share'), 'Anki2', 'addons21');
    default:
      throw new Error('Pass your Anki add-ons folder explicitly on this platform.');
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length > 1) throw new Error('Usage: npm run link:addon -- [addons-folder]');
  if (args[0] === '--help') {
    console.log('Usage: npm run link:addon -- [addons-folder]');
    return;
  }

  const addonsFolder = resolve(args[0] || defaultAddonsFolder());
  const destination = join(addonsFolder, 'anki-global-kit-dev');
  const source = await realpath(addon);
  let existing;
  try {
    existing = await lstat(destination);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  if (existing) {
    if (existing.isSymbolicLink() && (await realpath(destination)) === source) {
      console.log(`Already linked: ${destination} -> ${source}`);
      return;
    }
    throw new Error(`Refusing to overwrite ${destination}. Move or remove it before linking this checkout.`);
  }

  await mkdir(addonsFolder, { recursive: true });
  await symlink(source, destination, process.platform === 'win32' ? 'junction' : 'dir');
  console.log(`Linked: ${destination} -> ${source}`);
  console.log('Build assets with npm run build:addon or npm run watch, then restart Anki to load Python changes.');
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
