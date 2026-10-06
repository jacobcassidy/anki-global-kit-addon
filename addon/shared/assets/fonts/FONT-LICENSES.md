# MesloLGL Nerd Font attribution and licenses

This folder contains the shared card and editor font `_mesloLGL-NF.woff2`. **NF means Nerd Font.** The font incorporates upstream works with separate notices and terms, collected here and in `licenses/`.

## Font identity and provenance

The bundled font was converted from the official **Nerd Fonts v3.5.1 Meslo LG L Regular** TTF. Its embedded metadata identifies:

- Family: `MesloLGL Nerd Font`
- Full name: `MesloLGL Nerd Font Regular`
- PostScript name: `MesloLGLNF-Regular`
- Version: `Version 1.210;Nerd Fonts 3.5.1`
- Unique identifier: `MesloLGL Nerd Font Regular 3.5.1`
- Glyph count: 13,579

The source is [MesloLGLNerdFont-Regular.ttf](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/patched-fonts/Meslo/L/MesloLGLNerdFont-Regular.ttf), at release commit `b894ea7803af6aade63d60a4381e006098ec9c4d`. The downloaded TTF was verified against the official Git blob `58d65f3e64589d76397ea8f68a39fb9c1cf67664`.

| File                | SHA-256                                                            |
| ------------------- | ------------------------------------------------------------------ |
| Official source TTF | `6c680892d577e70aa3f2c9a0aa230a0c9990ca08eed3e9c7fe8b3c07ac4f509f` |
| Bundled WOFF2       | `5174d94cf2df71b1989035d28bfc94fb15cf891c2fe67538b9adb82525b0b3b8` |

The TTF was converted directly with Google's [WOFF2 encoder](https://github.com/google/woff2), version **1.0.2**, using `woff2_compress`. No subsetting or manual glyph edits were applied. The WOFF2 is 1,173,436 bytes. The installed media filename and CSS family alias remain `_mesloLGL-NF.woff2` and `MesloLGL NF`.

### Recreate the bundled WOFF2

With `woff2_compress` 1.0.2 installed, run from the repository root:

```sh
font_workdir="$(mktemp -d)"
curl -fL 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/b894ea7803af6aade63d60a4381e006098ec9c4d/patched-fonts/Meslo/L/MesloLGLNerdFont-Regular.ttf' -o "$font_workdir/MesloLGL.ttf"
echo "6c680892d577e70aa3f2c9a0aa230a0c9990ca08eed3e9c7fe8b3c07ac4f509f  $font_workdir/MesloLGL.ttf" > "$font_workdir/ttf.sha256"
shasum -a 256 -c "$font_workdir/ttf.sha256" && woff2_compress "$font_workdir/MesloLGL.ttf"
echo "5174d94cf2df71b1989035d28bfc94fb15cf891c2fe67538b9adb82525b0b3b8  $font_workdir/MesloLGL.woff2" > "$font_workdir/woff2.sha256"
shasum -a 256 -c "$font_workdir/woff2.sha256" && cp "$font_workdir/MesloLGL.woff2" addon/shared/assets/fonts/_mesloLGL-NF.woff2
```

The checksums stop conversion or replacement if the source or encoder output differs. If intentionally changing the release or encoder, review the result and update these hashes and notices together.

## Base font and Nerd Fonts notices

The base font is [Meslo LG by André Berg](https://github.com/andreberg/Meslo-Font), derived from Apple's Menlo and Bitstream Vera Sans Mono. Nerd Fonts uses a version patched for Powerline by [opeik](https://github.com/opeik), as described in its [Meslo README](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/patched-fonts/Meslo/L/README.md).

Meslo's [release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/patched-fonts/Meslo/L/LICENSE.txt) states **Copyright 2009, 2010, 2013 André Berg** and Apache License 2.0. Copies are provided in [Meslo.txt](licenses/Meslo.txt) and [Apache-2.0.txt](licenses/Apache-2.0.txt).

The font metadata and Meslo's upstream attribution retain:

- Copyright © 2009 Apple Inc.
- Copyright © 2006 by Tavmjong Bah.
- Copyright © 2003 by Bitstream, Inc. All Rights Reserved.
- Menlo is a trademark of Apple Inc.
- Bitstream Vera is a trademark of Bitstream, Inc., designed by Jim Lyles.

The complete [Nerd Fonts v3.5.1 licensing notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/LICENSE) is preserved in [Nerd-Fonts.txt](licenses/Nerd-Fonts.txt). It identifies Ryan L McIntyre's contributions and the project's various licenses. It does not replace the notices of Meslo or contributed glyph sources.

## Contributed glyph sources

The release's [Meslo README](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/patched-fonts/Meslo/L/README.md) lists its icon sources and versions. Copies below come from the same Nerd Fonts commit or the indicated upstream version. Line endings, trailing whitespace, and a UTF-8 byte-order mark have been normalized without changing license wording.

| Glyph source           | Version or attribution                                                     | Included notice                                                                                            | Notice source                                                                                                                  |
| ---------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Codicons               | 0.0.45; Microsoft; CC BY 4.0                                               | [CC-BY-4.0.txt](licenses/CC-BY-4.0.txt)                                                                    | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/codicons/LICENSE.txt)                          |
| Devicons               | Devicon 2.17.0; konpa; MIT                                                 | [Devicons.txt](licenses/Devicons.txt)                                                                      | [v2.17.0 license](https://github.com/devicons/devicon/blob/v2.17.0/LICENSE)                                                    |
| Extra glyphs           | Source Foundry's Hack; MIT and retained upstream notices                   | [Hack.txt](licenses/Hack.txt)                                                                              | [Release source license](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/unpatched-fonts/Hack/LICENSE.md)              |
| Font Awesome           | 6.5.1; Fonticons, Inc.; font files use OFL 1.1, SVG/JS icons use CC BY 4.0 | [Font-Awesome.txt](licenses/Font-Awesome.txt), [CC-BY-4.0.txt](licenses/CC-BY-4.0.txt)                     | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/font-awesome/LICENSE.txt)                      |
| Font Awesome Extension | 0.0.3; André Luiz Gava; MIT                                                | [Font-Awesome-Extension.txt](licenses/Font-Awesome-Extension.txt)                                          | [Upstream notice](https://github.com/AndreLZGava/font-awesome-extension/blob/09d80249058ee8018a45da30add4339289dbb466/LICENCE) |
| Font Logos             | 1.3.0; Lukas-W and contributors; upstream version includes the Unlicense   | [Font-Logos.txt](licenses/Font-Logos.txt)                                                                  | [v1.3.0 license](https://github.com/lukas-w/font-logos/blob/v1.3.0/LICENSE)                                                    |
| Material Design Icons  | October 6, 2022 font; Pictogrammers; Apache 2.0                            | [Material-Design-Icons.txt](licenses/Material-Design-Icons.txt), [Apache-2.0.txt](licenses/Apache-2.0.txt) | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/materialdesign/LICENSE)                        |
| Octicons               | 18.3.0; GitHub Inc.; MIT                                                   | [Octicons.txt](licenses/Octicons.txt)                                                                      | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/octicons/LICENSE)                              |
| Seti and original      | Seti-UI 0.8.1; Jesse Weed; MIT, plus Nerd Fonts' original contributions    | [Seti-UI.txt](licenses/Seti-UI.txt), [Nerd-Fonts.txt](licenses/Nerd-Fonts.txt)                             | [v0.8.1 license](https://github.com/jesseweed/seti-ui/blob/v0.8.1/LICENSE.md)                                                  |
| Pomicons               | 1.001; Gabriele Lana; OFL 1.1, reserved font name Pomicons                 | [Pomicons.txt](licenses/Pomicons.txt)                                                                      | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/pomicons/LICENSE)                              |
| Powerline Extra        | 1.200; Ryan L McIntyre; MIT                                                | [Powerline-Extra-Symbols.txt](licenses/Powerline-Extra-Symbols.txt)                                        | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/powerline-extra/LICENSE)                       |
| Powerline Symbols      | 1.000; Kim Silkebækken and contributors; MIT                               | [Powerline.txt](licenses/Powerline.txt)                                                                    | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/powerline-symbols/LICENSE.txt)                 |
| IEC Power Symbols      | February 2015; Joe Loughry; MIT                                            | [IEC-Power-Symbols.txt](licenses/IEC-Power-Symbols.txt)                                                    | [Upstream notice](https://github.com/jloughry/Unicode/blob/805536fb6f93604da985d80e0c6b099f98f8b4d9/LICENSE.txt)               |
| Weather Icons          | 2.0.10 (font 1.100); Erik Flowers and Lukas Bischoff; OFL 1.1              | [Weather-Icons.txt](licenses/Weather-Icons.txt)                                                            | [Release notice](https://github.com/ryanoasis/nerd-fonts/blob/v3.5.1/src/glyphs/weather-icons/OFL.txt)                         |

A separate copy of the common OFL 1.1 text is provided in [OFL-1.1.txt](licenses/OFL-1.1.txt). Weather Icons' supplied upstream notice includes unfilled template fields; those fields are retained as supplied. Its authors are identified in the table above and in the donor font metadata. Brand marks belong to their respective owners. The Nerd Fonts README labels Font Logos as unlicensed; the version-specific Font Logos license linked above supplies the Unlicense, which is retained here.

## Updating and packaging

Nerd Fonts v3 changed some icon code points from v2. Notes containing pasted Nerd Font icons may need their characters updated using the [Nerd Fonts cheat sheet](https://www.nerdfonts.com/cheat-sheet). The add-on refreshes the font on profile open; sync media afterward to update other clients.

The packager includes this document and `licenses/` under `shared/assets/fonts/`. Keep the notices with the font when redistributing the add-on. The current media installer copies only the font binary to `collection.media`; these notices are packaged with the Desktop add-on.
