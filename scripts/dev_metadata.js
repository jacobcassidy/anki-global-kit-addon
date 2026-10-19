import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const defaultAddonDirectory = fileURLToPath(new URL('../addon/', import.meta.url));

/** Refresh local installation metadata without changing release files or saved settings. */
export async function updateDevAddonName({ addonDirectory = defaultAddonDirectory, create = false } = {}) {
  const metadataPath = join(addonDirectory, 'meta.json');
  let metadata;
  try {
    metadata = JSON.parse(await readFile(metadataPath, 'utf8'));
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    if (!create) return;
    metadata = {};
  }
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
    throw new Error('Expected an object in local addon/meta.json; refusing to overwrite it.');
  }
  const manifest = JSON.parse(await readFile(join(addonDirectory, 'manifest.json'), 'utf8'));
  if (
    typeof manifest.name !== 'string' ||
    !manifest.name.trim() ||
    typeof manifest.version !== 'string' ||
    !manifest.version.trim()
  ) {
    throw new Error('The add-on manifest must contain a name and version for the development label.');
  }
  const name = `${manifest.name} (dev v${manifest.version})`;
  if (metadata.name === name) return;
  metadata.name = name;
  await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
}
