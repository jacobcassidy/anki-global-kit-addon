# Development dependency advisories

Reviewed on 2026-10-07. These notes cover the npm development tools used to build, lint, and check this repository.

## Patched dependency overrides

`package.json` pins these transitive dependencies through npm overrides:

| Dependency      | Version  | Advisory                                                                 |
| --------------- | -------- | ------------------------------------------------------------------------ |
| `source-map-js` | `1.2.2`  | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) |
| `smol-toml`     | `1.9.0`  | [GHSA-r4xh-jqrq-34v2](https://github.com/advisories/GHSA-r4xh-jqrq-34v2) |
| `katex`         | `0.18.2` | [GHSA-238p-pmpm-9mq7](https://github.com/advisories/GHSA-238p-pmpm-9mq7) |

Markdownlint CLI2 0.23.3 pins `smol-toml` to 1.8.0, and its math extension selects KaTeX from the 0.16 series. Overrides select patched versions despite those parent constraints. The `source-map-js` override prevents resolving versions older than the selected patch.

Review these overrides when updating the parent tools. Remove an override once the normal dependency resolution selects a compatible patched version, then update the lockfile and repeat the dependency audit, lint, and build checks.

## Remaining braces advisory

`braces@3.0.3` remains affected by [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). The advisory currently lists no patched release. Deeply nested brace patterns can exhaust the parser's call stack and stop the Node.js process.

The dependency is used by `micromatch`, `fast-glob`, and `globby` in the Stylelint and Markdownlint development toolchains. They process glob patterns supplied through repository configuration and command-line arguments. The repository's lint commands use fixed glob patterns; keep those patterns under developer control when running the tools.

These four dependencies are excluded from the add-on package and its card/editor bundles. Card fields, submitted answers, and Anki settings do not pass through their development-tool parsers.

`npm audit` can report the same underlying `braces` advisory against several parent packages and exit with a nonzero status. On the review date, it reported 15 affected package entries from this single advisory. Compare the current output with this remaining advisory and investigate any new findings. Recheck for a patched release when updating dependencies.

## Check the current dependency state

```sh
npm ls braces source-map-js smol-toml katex --all
npm audit
npm run lint:scripts
npm run lint:styles
npm run lint:docs
npm run check
npm run build:addon
npm run check:assets
```

The dependency audit requires access to the npm registry. The package manifest and lockfile should be updated together when changing an override.
