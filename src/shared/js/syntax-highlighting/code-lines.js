export function textFromCode(node) {
  const numberedLines = [...node.children].filter((line) => line.classList.contains('code-line'));

  return numberedLines.length
    ? [...numberedLines]
        .map(
          (line) =>
            [...line.children].find((child) => child.classList.contains('code-line__content'))?.textContent ??
            line.textContent ??
            '',
        )
        .join('\n')
    : node.textContent || '';
}

function escapeText(text) {
  const node = document.createElement('span');
  node.textContent = text;
  return node.innerHTML;
}

function splitTokenNode(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    return (node.nodeValue || '').split('\n').map(escapeText);
  }

  if (node.nodeType !== Node.ELEMENT_NODE) return [''];

  const lines = [''];

  for (const child of node.childNodes) {
    const childLines = splitTokenNode(child);

    lines[lines.length - 1] += childLines[0] || '';

    for (const continuation of childLines.slice(1)) lines.push(continuation);
  }

  const opening = `<${node.localName}${[...node.attributes]
    .map((attribute) => ` ${attribute.name}="${attribute.value.replaceAll('"', '&quot;')}"`)
    .join('')}>`;
  return lines.map((content) => (content ? `${opening}${content}</${node.localName}>` : ''));
}

export function tokenHtmlByLine(tokenHtml, start) {
  const container = document.createElement('div');

  container.innerHTML = tokenHtml;

  const lines = [''];

  for (const node of container.childNodes) {
    const nodeLines = splitTokenNode(node);

    lines[lines.length - 1] += nodeLines[0] || '';

    for (const continuation of nodeLines.slice(1)) lines.push(continuation);
  }

  return lines
    .map(
      (line, index) =>
        `<span class="code-line"><span class="code-line__number" contenteditable="false" role="button" tabindex="0" data-line-number="${start + index}" aria-label="Line ${start + index}"></span><span class="code-line__content">${line || '<br data-code-placeholder="">'}</span></span>`,
    )
    .join('');
}

/** Flatten visual rows into highlighted source with real newline separators. */
export function flattenCodeLines(code) {
  const flat = code.ownerDocument.createElement('code');
  const lines = [...code.children].filter((line) => line.classList.contains('code-line'));

  if (!lines.length) {
    flat.innerHTML = code.innerHTML;
  } else {
    lines.forEach((line, index) => {
      if (index) flat.append('\n');

      const content = [...line.children].find((child) => child.classList.contains('code-line__content')) || line;
      const clone = content.cloneNode(true);

      clone.querySelectorAll('.code-line__number, [data-code-placeholder]').forEach((node) => node.remove());
      flat.append(...clone.childNodes);
    });
  }

  return flat;
}

/** Read a source offset independently of decorative gutters and token spans. */
export function codeOffset(code, node, offset) {
  const range = code.ownerDocument.createRange();

  range.selectNodeContents(code);
  range.setEnd(node, offset);

  const fragment = code.ownerDocument.createElement('code');

  fragment.append(range.cloneContents());

  return textFromCode(fragment).length;
}

export function codePointAt(code, offset) {
  const walker = code.ownerDocument.createTreeWalker(code, 4);
  let node;

  while ((node = walker.nextNode())) {
    if (offset <= node.length) return [node, offset];

    offset -= node.length;
  }

  return [code, code.childNodes.length];
}

export function codeCaret(code, offset) {
  const lines = [...code.children].filter((line) => line.classList.contains('code-line'));

  for (const line of lines) {
    const content = line.querySelector('.code-line__content');
    const length = content.textContent.length;

    if (offset <= length) return codePointAt(content, offset);

    offset -= length + 1;
  }

  return [code, code.childNodes.length];
}

export function preserveClozeMode(code, mode) {
  for (const guard of code.querySelectorAll('[data-global-kit-literal-brace]')) {
    guard.replaceWith(...guard.childNodes);
  }

  code.normalize();

  if (mode !== 'literal') return;

  // Entity escapes become ordinary braces when browser HTML is serialized.
  // Splitting each pair with a span keeps literal clozes inert after saving.
  const owner = code.ownerDocument;
  const walker = owner.createTreeWalker(code, 4);
  const leaves = [];
  let leaf;

  while ((leaf = walker.nextNode())) {
    if (/\{\{|\}\}/.test(leaf.data)) leaves.push(leaf);
  }

  for (const node of leaves) {
    const fragment = owner.createDocumentFragment();

    for (const part of node.data.split(/(\{\{|\}\})/)) {
      if (part === '{{' || part === '}}') {
        const guard = owner.createElement('span');

        guard.dataset.globalKitLiteralBrace = '';
        guard.textContent = part[0];
        fragment.append(guard, owner.createTextNode(part[1]));
      } else {
        fragment.append(owner.createTextNode(part));
      }
    }

    node.replaceWith(fragment);
  }
}
