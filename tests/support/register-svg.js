import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';

// Match esbuild's text loader when source-module tests import shared icons.
registerHooks({
  load(url, context, nextLoad) {
    if (new URL(url).pathname.endsWith('.svg')) {
      return {
        format: 'module',
        source: `export default ${JSON.stringify(readFileSync(new URL(url), 'utf8'))};`,
        shortCircuit: true,
      };
    }

    return nextLoad(url, context);
  },
});
