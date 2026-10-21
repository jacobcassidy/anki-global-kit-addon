/* Bundled highlight.js engine with review languages registered explicitly. */

import hljs from 'highlight.js/lib/core';
import bash from 'highlight.js/lib/languages/bash';
import c from 'highlight.js/lib/languages/c';
import cpp from 'highlight.js/lib/languages/cpp';
import csharp from 'highlight.js/lib/languages/csharp';
import css from 'highlight.js/lib/languages/css';
import go from 'highlight.js/lib/languages/go';
import java from 'highlight.js/lib/languages/java';
import javascript from 'highlight.js/lib/languages/javascript';
import json from 'highlight.js/lib/languages/json';
import kotlin from 'highlight.js/lib/languages/kotlin';
import markdown from 'highlight.js/lib/languages/markdown';
import php from 'highlight.js/lib/languages/php';
import powershell from 'highlight.js/lib/languages/powershell';
import python from 'highlight.js/lib/languages/python';
import ruby from 'highlight.js/lib/languages/ruby';
import rust from 'highlight.js/lib/languages/rust';
import sql from 'highlight.js/lib/languages/sql';
import typescript from 'highlight.js/lib/languages/typescript';
import xml from 'highlight.js/lib/languages/xml';
import { reviewLanguageAliases } from '../../../shared/js/syntax-highlighting/language-aliases.js';

export { reviewLanguageAliases };

const grammars = {
  bash,
  c,
  cpp,
  csharp,
  css,
  go,
  java,
  javascript,
  json,
  kotlin,
  markdown,
  php,
  powershell,
  python,
  ruby,
  rust,
  sql,
  typescript,
  html: xml,
};

Object.entries(grammars).forEach(([name, grammar]) => hljs.registerLanguage(name, grammar));

export function highlightReviewCode(source, language) {
  const canonical = reviewLanguageAliases[String(language || '').toLowerCase()];
  if (!canonical) return null;

  try {
    return hljs.highlight(source, { language: canonical, ignoreIllegals: true }).value;
  } catch {
    return null;
  }
}
