/**
 * Convert common Markdown syntax to safe HTML for the submitted answer.
 */
export function markdownToHtml(markdown) {
  const escapeHtml = (text) =>
    text.replace(/[&<>"']/g, (character) => {
      const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
      return entities[character];
    });

  const renderInline = (text) => {
    const fragments = [];
    // Protect code and complete links before formatting surrounding text.
    // Render link labels separately so Markdown never rewrites the URL.
    let html = escapeHtml(
      text.replace(/`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, code, label, url) => {
        const token = `\u0000${fragments.length}\u0000`;
        fragments.push(
          code !== undefined
            ? `<code>${escapeHtml(code)}</code>`
            : `<a href="${escapeHtml(url)}">${renderInline(label)}</a>`,
        );
        return token;
      }),
    );

    html = html
      .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
      .replace(/__([^_]+)__/g, '<b>$1</b>')
      .replace(/\*([^*\n]+)\*/g, '<i>$1</i>')
      .replace(/_([^_\n]+)_/g, '<i>$1</i>')
      .replace(/~~([^~]+)~~/g, '<s>$1</s>');

    // Restore protected HTML after formatting the surrounding text.
    // eslint-disable-next-line no-control-regex
    html = html.replace(/\u0000(\d+)\u0000/g, (_, index) => fragments[Number(index)]);

    return html;
  };

  const formatBlocks = (html) => {
    const blockTags = new Set([
      'blockquote',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'li',
      'ol',
      'p',
      'pre',
      'ul',
    ]);
    const tokens = html.match(/<[^>]+>|[^<]+/g) || [];
    const output = [];
    let depth = 0;
    let line = '';
    let lineIndent = 0;
    let inPre = false;

    const flushLine = (blankBefore = false, indent = lineIndent) => {
      const content = line.trim();
      if (content) {
        if (blankBefore && output.length) output.push('');
        output.push(`${'  '.repeat(indent)}${content}`);
      }
      line = '';
      lineIndent = depth;
    };

    for (const token of tokens) {
      const tag = token.match(/^<(\/)?([a-z0-9]+)\b[^>]*>$/i);
      if (!tag) {
        if (inPre) {
          line += token;
        } else {
          line += token.replace(/\s+/g, ' ');
        }
        continue;
      }

      const [, closing, name] = tag;
      const tagName = name.toLowerCase();
      if (!blockTags.has(tagName)) {
        line += token;
        continue;
      }

      if (closing) {
        if (inPre && tagName !== 'pre') {
          line += token;
          continue;
        }
        if (tagName === 'pre') {
          inPre = false;
          flushLine();
          depth = Math.max(0, depth - 1);
          line = token;
          lineIndent = depth;
          flushLine();
        } else if (line) {
          line = `${line.trimEnd()}${token}`;
          flushLine(false, lineIndent);
          depth = Math.max(0, depth - 1);
        } else {
          depth = Math.max(0, depth - 1);
          line = token;
          lineIndent = depth;
          flushLine();
        }
      } else {
        flushLine(tagName[0] === 'h');
        line = token;
        lineIndent = depth;
        depth += 1;
        if (tagName === 'pre') inPre = true;
      }
    }

    flushLine();
    return output.join('\n').replace(/\n+$/, '');
  };

  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const blocks = [];
  let paragraph = [];
  let code = [];
  let inCodeBlock = false;
  let codeLanguage = '';
  let lastHeadingLevel = 1;

  const renderCodeBlock = () => {
    const languageAttribute = codeLanguage ? ` data-language="${escapeHtml(codeLanguage)}"` : '';
    blocks.push(`<pre><code${languageAttribute}>${escapeHtml(code.join('\n'))}</code></pre>`);
    code = [];
    codeLanguage = '';
  };
  const listStack = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push(`<p>${renderInline(paragraph.join('\n')).replace(/\n/g, '<br>')}</p>`);
      paragraph = [];
    }
  };
  const closeTopList = () => {
    const list = listStack.pop();
    if (list) blocks.push(`</li></${list.type}>`);
  };
  const closeLists = () => {
    while (listStack.length) closeTopList();
  };
  const openList = (type, indent, start = '1') => {
    const startAttribute = type === 'ol' && start !== '1' ? ` start="${start}"` : '';
    blocks.push(`<${type}${startAttribute}><li>`);
    listStack.push({ type, indent });
  };

  for (const line of lines) {
    const fence = line.match(/^\s*```(.*)$/);
    if (fence) {
      flushParagraph();
      closeLists();
      if (inCodeBlock) {
        renderCodeBlock();
      } else {
        codeLanguage = fence[1].trim().split(/\s+/, 1)[0] || '';
      }
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (inCodeBlock) {
      code.push(line);
      continue;
    }

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+)$/);
    const listItem = line.match(/^([ \t]*)(?:([-+*])\s+|(\d+)\.\s+)(.*)$/);
    // Craft exports toggle headings with `+` list markers. Explicit Markdown
    // headings keep their level; unmarked question toggles become the next
    // heading level after the most recent heading. Other `+` items remain lists.
    const craftHeading = listItem?.[2] === '+' ? listItem[4].match(/^(?:(#{1,6})\s+(.+)|(.+\?))$/) : null;
    const quote = line.match(/^\s*>\s?(.*)$/);
    if (!line.trim() || heading || craftHeading || listItem || quote) flushParagraph();

    if (!line.trim()) {
      closeLists();
    } else if (heading || craftHeading) {
      closeLists();
      const level = heading
        ? heading[1].length
        : craftHeading[1]
          ? craftHeading[1].length
          : Math.min(lastHeadingLevel + 1, 6);
      const text = heading ? heading[2] : craftHeading[2] || craftHeading[3];
      lastHeadingLevel = level;
      blocks.push(`<h${level}>${renderInline(text)}</h${level}>`);
    } else if (listItem) {
      const indent = listItem[1].replace(/\t/g, '    ').length;
      const nextListType = listItem[3] ? 'ol' : 'ul';

      while (listStack.length && indent < listStack[listStack.length - 1].indent) {
        closeTopList();
      }

      const currentList = listStack[listStack.length - 1];
      if (!currentList) {
        openList(nextListType, indent, listItem[3]);
      } else if (indent > currentList.indent) {
        // A more-indented item is nested inside the preceding list item.
        openList(nextListType, indent, listItem[3]);
      } else if (indent === currentList.indent && currentList.type !== nextListType) {
        closeTopList();
        openList(nextListType, indent, listItem[3]);
      } else {
        // Continue the current list at the same indentation.
        blocks.push('</li><li>');
      }
      blocks.push(renderInline(listItem[4]));
    } else if (quote) {
      closeLists();
      blocks.push(`<blockquote><p>${renderInline(quote[1])}</p></blockquote>`);
    } else {
      closeLists();
      paragraph.push(line);
    }
  }

  flushParagraph();
  closeLists();
  if (inCodeBlock) renderCodeBlock();
  return formatBlocks(blocks.join('\n').replace(/<li>\n/g, '<li>'));
}
