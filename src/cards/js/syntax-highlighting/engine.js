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

export const reviewLanguageAliases = {
  bash: 'bash',
  shell: 'bash',
  sh: 'bash',
  c: 'c',
  cpp: 'cpp',
  'c++': 'cpp',
  csharp: 'csharp',
  'c#': 'csharp',
  css: 'css',
  go: 'go',
  golang: 'go',
  java: 'java',
  javascript: 'javascript',
  js: 'javascript',
  node: 'javascript',
  json: 'json',
  kotlin: 'kotlin',
  markdown: 'markdown',
  md: 'markdown',
  html: 'html',
  xml: 'html',
  php: 'php',
  powershell: 'powershell',
  ps1: 'powershell',
  python: 'python',
  py: 'python',
  ruby: 'ruby',
  rb: 'ruby',
  rust: 'rust',
  rs: 'rust',
  sql: 'sql',
  typescript: 'typescript',
  ts: 'typescript',
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
