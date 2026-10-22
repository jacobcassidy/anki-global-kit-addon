import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { codeOffset, textFromCode } from '../../../src/shared/js/syntax-highlighting/code-lines.js';
import { installCodeBlockHighlighting } from '../../../src/editor/js/formatting/code-block.js';

function withEditor(html, callback) {
  const dom = new JSDOM(`<body><anki-editable contenteditable="true">${html}</anki-editable></body>`);
  const previous = {
    document: globalThis.document,
    window: globalThis.window,
    Node: globalThis.Node,
    InputEvent: globalThis.InputEvent,
    ShadowRoot: globalThis.ShadowRoot,
    pycmd: globalThis.pycmd,
    require: globalThis.require,
    api: globalThis.ankiGlobalKitEditor,
    settings: globalThis.ankiGlobalKitEditorSettings,
  };
  globalThis.document = dom.window.document;
  globalThis.window = dom.window;
  globalThis.Node = dom.window.Node;
  globalThis.InputEvent = dom.window.InputEvent;
  globalThis.ShadowRoot = dom.window.ShadowRoot;
  globalThis.pycmd = (message) => callback.message?.(message);
  globalThis.ankiGlobalKitEditor = {};
  globalThis.ankiGlobalKitEditorSettings = {
    anki_editor_syntax_highlighting_line_numbers: true,
    anki_editor_syntax_highlighting_languages: ['python', 'javascript', 'bash'],
  };
  installCodeBlockHighlighting();

  try {
    callback(dom.window.document, dom.window);
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
    dom.window.close();
  }
}

function selectText(document, window, node) {
  const range = document.createRange();
  range.selectNodeContents(node);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

function mockOptionsEditing(document, window) {
  globalThis.pycmd = (message) => {
    if (!message.startsWith('anki-global-kit:code-block-options:')) return;

    const request = JSON.parse(message.slice(message.indexOf('{')));

    document.optionsRequest = request;
    document.options = {
      lineStart: { value: String(request.lineStart) },
      lineNumbers: { checked: request.lineNumbers },
      clozeMode: { value: request.clozeMode },
    };
  };
  document.execCommand = (_command, _showUi, html) => {
    const range = window.getSelection().getRangeAt(0);

    range.deleteContents();
    range.insertNode(range.createContextualFragment(html));

    return true;
  };
}

function applyOptions(document) {
  return globalThis.ankiGlobalKitEditor.applyCodeBlockOptions(document.optionsRequest.id, {
    lineStart: Number(document.options.lineStart.value),
    lineNumbers: document.options.lineNumbers.checked,
    clozeMode: document.options.clozeMode.value,
  });
}

function optionsDialog(document) {
  return {
    querySelector: (selector) => document.options[selector.match(/name="(.*?)"/)[1]],
  };
}

test('new blocks start at line 1 despite old global preferences and apply tokens as one edit', () => {
  withEditor('<p>const answer = 42;</p>', (document, window) => {
    const field = document.querySelector('anki-editable');
    selectText(document, window, field.querySelector('p'));
    let request;
    globalThis.pycmd = (message) => {
      if (message.startsWith('anki-global-kit:syntax-highlight:')) {
        request = JSON.parse(message.slice(message.indexOf('{')));
      }
    };

    // Previously saved global preferences must not affect new blocks.
    globalThis.ankiGlobalKitEditorSettings.anki_editor_syntax_highlighting_line_number_start = 50;
    assert.equal(globalThis.ankiGlobalKitEditor.highlightCode('', 'javascript'), true);
    assert.equal(request.source, 'const answer = 42;');
    assert.equal(request.lineStart, 1);
    document.execCommand = (_command, _showUi, html) => {
      const range = window.getSelection().getRangeAt(0);
      range.deleteContents();
      range.insertNode(range.createContextualFragment(html));
      return true;
    };

    assert.equal(
      globalThis.ankiGlobalKitEditor.applyHighlightResult(
        request.id,
        request.source,
        'javascript',
        '<span class="k">const</span> answer = <span class="m">42</span>;',
      ),
      true,
    );
    assert.equal(field.querySelector('pre.global-kit-code-block').dataset.language, 'javascript');
    assert.equal(field.querySelector('.code-block__language').textContent, 'JavaScript');
    assert.equal(field.querySelector('.code-block__copy').hidden, false);
    assert.equal(field.querySelectorAll('[data-language]').length, 1);
    assert.equal(field.querySelector('code').attributes.length, 0);
    assert.equal(field.querySelector('code').textContent, request.source);
    assert.equal(field.querySelector('[data-global-kit-token="declaration"]').textContent, 'const');
    assert.equal(field.querySelector('[data-global-kit-token="variable"]').textContent, 'answer');
  });
});

test('literal clozes remain inert through HTML annotation, line wrapping, and native insertion', () => {
  withEditor('<p>const value = {{c1::hidden.name}};</p>', (document, window) => {
    const field = document.querySelector('anki-editable');

    selectText(document, window, field.querySelector('p'));

    let request;

    globalThis.confirm = () => false;
    globalThis.pycmd = (message) => {
      if (message.startsWith('anki-global-kit:syntax-highlight:'))
        request = JSON.parse(message.slice(message.indexOf('{')));
    };
    document.execCommand = (_command, _ui, html) => {
      const range = window.getSelection().getRangeAt(0);

      range.deleteContents();
      range.insertNode(range.createContextualFragment(html));

      return true;
    };

    try {
      globalThis.ankiGlobalKitEditor.highlightCode('', 'javascript');
      assert.equal(request.clozeMode, 'literal');
      globalThis.ankiGlobalKitEditor.applyHighlightResult(
        request.id,
        request.source,
        'javascript',
        '<span class="kd">const</span> value = &#123;&#123;c1::hidden.name&#125;&#125;;',
        false,
        1,
        'literal',
      );

      const block = field.querySelector('pre');

      assert.equal(block.querySelector('code').textContent, request.source);
      assert.doesNotMatch(block.outerHTML, /\{\{c1::/);
      assert.equal(block.querySelectorAll('[data-global-kit-literal-brace]').length, 2);
      assert.equal(block.querySelector('[data-global-kit-token="variable"]').textContent, 'value');
    } finally {
      delete globalThis.confirm;
    }
  });
});

test('stale responses leave a changed field untouched', () => {
  withEditor('<p>source</p>', (document, window) => {
    const field = document.querySelector('anki-editable');
    selectText(document, window, field.querySelector('p'));
    let request;
    globalThis.pycmd = (message) => {
      request = JSON.parse(message.slice(message.indexOf('{')));
    };
    globalThis.ankiGlobalKitEditor.highlightCode('', 'python');
    field.innerHTML = '<p>changed</p>';

    assert.equal(globalThis.ankiGlobalKitEditor.applyHighlightResult(request.id, request.source, 'python', 'x'), false);
    assert.equal(field.textContent, 'changed');
  });
});

test('multiline blocks preserve source and their starting line number when refreshed', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-language="python" data-line-numbers="true" data-line-start="50"><code>first\nsecond</code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      selectText(document, window, field.querySelector('code'));
      let request;
      globalThis.pycmd = (message) => {
        request = JSON.parse(message.slice(message.indexOf('{')));
      };
      globalThis.ankiGlobalKitEditor.highlightCode('', 'python');
      assert.equal(request.source, 'first\nsecond');
      assert.equal(request.lineNumbers, true);
      assert.equal(request.lineStart, 50);

      document.execCommand = (_command, _showUi, html) => {
        const range = window.getSelection().getRangeAt(0);
        range.deleteContents();
        range.insertNode(range.createContextualFragment(html));
        return true;
      };
      assert.equal(
        globalThis.ankiGlobalKitEditor.applyHighlightResult(
          request.id,
          request.source,
          'python',
          'first\nsecond',
          request.lineNumbers,
          request.lineStart,
        ),
        true,
      );
      const block = field.querySelector('pre.global-kit-code-block');
      assert.equal(block.dataset.lineNumbers, 'true');
      assert.equal(block.dataset.lineStart, '50');
      assert.deepEqual(
        [...block.querySelectorAll('.code-line__number')].map((line) => line.dataset.lineNumber),
        ['50', '51'],
      );

      selectText(document, window, block.querySelector('code'));
      globalThis.ankiGlobalKitEditor.highlightCode('', 'javascript');
      assert.equal(request.source, 'first\nsecond');
      assert.equal(request.existingLanguage, 'python');
      assert.equal(request.lineNumbers, true);
      assert.equal(request.lineStart, 50);
    },
  );
});

test('Code Block Options changes only the selected block starting number', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-language="python" data-line-start="1"><code><span class="code-line" data-line-number="1">first</span><span class="code-line" data-line-number="2">second</span></code></pre><pre class="global-kit-code-block" data-line-start="99"><code>other</code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      selectText(document, window, field.querySelector('code'));
      mockOptionsEditing(document, window);

      assert.equal(globalThis.ankiGlobalKitEditor.openCodeBlockOptions(), true);
      const dialog = optionsDialog(document);
      dialog.querySelector('[name="lineStart"]').value = '50';
      dialog.querySelector('[name="lineNumbers"]').checked = true;
      applyOptions(document, window);

      const blocks = field.querySelectorAll('pre');
      assert.equal(blocks[0].dataset.lineStart, '50');
      assert.equal(blocks[0].dataset.lineNumbers, 'true');
      assert.deepEqual(
        [...blocks[0].querySelectorAll('.code-line__number')].map((line) => line.dataset.lineNumber),
        ['50', '51'],
      );
      assert.equal(blocks[1].dataset.lineStart, '99');
    },
  );
});

test('Code Block Options numbers Markdown blocks and toggles literal clozes without losing source or tokens', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-language="python"><code><span class="nb">print</span>({{c1::value}})\nnext</code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      let edits = 0;

      field.addEventListener('input', () => edits++);
      mockOptionsEditing(document, window);
      selectText(document, window, field.querySelector('code'));

      assert.equal(globalThis.ankiGlobalKitEditor.openCodeBlockOptions(), true);

      const dialog = optionsDialog(document);

      dialog.querySelector('[name="lineStart"]').value = '5';
      dialog.querySelector('[name="lineNumbers"]').checked = true;
      dialog.querySelector('[name="clozeMode"]').value = 'literal';
      applyOptions(document, window);

      const block = field.querySelector('pre');

      assert.equal(edits, 1);
      assert.equal(block.dataset.lineNumbers, 'true');
      assert.equal(block.dataset.clozeMode, 'literal');
      assert.deepEqual(
        [...block.querySelectorAll('.code-line__number')].map((line) => line.dataset.lineNumber),
        ['5', '6'],
      );
      assert.equal(block.querySelector('.nb').textContent, 'print');
      assert.equal(block.querySelectorAll('[data-global-kit-literal-brace]').length, 2);
      assert.doesNotMatch(block.innerHTML, /\{\{c1::/);
      assert.equal(
        [...block.querySelectorAll('.code-line__content')].map((line) => line.textContent).join('\n'),
        'print({{c1::value}})\nnext',
      );

      selectText(document, window, block.querySelector('code'));
      globalThis.ankiGlobalKitEditor.openCodeBlockOptions();
      document.options.lineNumbers.checked = false;
      document.options.clozeMode.value = 'active';
      applyOptions(document, window);

      assert.equal(edits, 2);
      assert.equal(field.querySelector('pre').dataset.lineNumbers, 'false');
      assert.equal(field.querySelector('pre').dataset.clozeMode, 'active');
      assert.equal(field.querySelectorAll('[data-global-kit-literal-brace]').length, 0);
      assert.match(field.innerHTML, /\{\{c1::value\}\}/);
    },
  );
});

test('Code Block Options leaves newer field edits untouched', () => {
  withEditor('<pre class="global-kit-code-block"><code>original</code></pre>', (document, window) => {
    const field = document.querySelector('anki-editable');

    mockOptionsEditing(document, window);
    selectText(document, window, field.querySelector('code'));
    globalThis.ankiGlobalKitEditor.openCodeBlockOptions();
    field.innerHTML = '<p>new edits</p>';
    applyOptions(document, window);

    assert.equal(field.innerHTML, '<p>new edits</p>');
  });
});

test('Code Block Options applies from a caret after Anki recreates unchanged field nodes', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-line-start="1"><code>other</code></pre><pre class="global-kit-code-block" data-line-start="1"><code><span class="code-line" data-line-number="1"><span class="nb">print</span>(1)</span><span class="code-line" data-line-number="2">next</span></code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      const originalBlock = field.querySelectorAll('pre')[1];
      const originalHtml = field.innerHTML;
      const range = document.createRange();

      range.setStart(originalBlock.querySelector('.nb').firstChild, 2);
      range.collapse(true);
      window.getSelection().addRange(range);
      mockOptionsEditing(document, window);

      assert.equal(globalThis.ankiGlobalKitEditor.openCodeBlockOptions(), true);

      // Anki's rich-text/HTML mirror can recreate identical nodes on blur.
      field.innerHTML = originalHtml;
      assert.equal(originalBlock.isConnected, false);
      document.options.lineNumbers.checked = true;
      document.options.lineStart.value = '20';
      applyOptions(document, window);

      const blocks = field.querySelectorAll('pre');

      assert.equal(blocks[0].dataset.lineStart, '1');
      assert.equal(blocks[1].dataset.lineStart, '20');
      assert.equal(blocks[1].dataset.lineNumbers, 'true');
      assert.deepEqual(
        [...blocks[1].querySelectorAll('.code-line__number')].map((line) => line.dataset.lineNumber),
        ['20', '21'],
      );
      assert.equal(blocks[1].querySelector('.nb').textContent, 'print');
    },
  );
});

test('language priority is explicit choice, existing block, Topic, remembered, then default', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-language="python"><code>print(1)</code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      selectText(document, window, field.querySelector('code'));
      let requests = [];
      globalThis.pycmd = (message) => {
        requests.push(JSON.parse(message.slice(message.indexOf('{'))));
      };
      globalThis.require = () => ({
        instances: [
          {
            fields: [
              {
                name: 'Topic',
                editingArea: { content: { subscribe: (callback) => (callback('JavaScript'), () => {}) } },
              },
            ],
          },
        ],
      });
      globalThis.ankiGlobalKitEditor.setLanguageContext(null, 'bash');

      globalThis.ankiGlobalKitEditor.highlightCode('', 'python');
      assert.equal(requests[0].language, 'python');
      assert.equal(requests[0].explicitLanguage, false);

      globalThis.ankiGlobalKitEditor.setExplicitLanguage('javascript');
      globalThis.ankiGlobalKitEditor.highlightCode('', 'python');
      assert.equal(requests[1].language, 'javascript');
      assert.equal(requests[1].explicitLanguage, true);
    },
  );
});

function editInput(document, window, inputType, data = null) {
  const event = new window.InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType, data });

  document.querySelector('code').dispatchEvent(event);
  assert.equal(event.defaultPrevented, true);
}

function caret(document, window, node, offset) {
  const range = document.createRange();

  range.setStart(node, offset);
  range.collapse(true);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);
}

test('editing adds and removes protected line numbers while preserving tokens and caret', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-line-numbers="true" data-line-start="9"><code><span class="nb">print</span>(1)</code></pre>',
    (document, window) => {
      mockOptionsEditing(document, window);
      caret(document, window, document.querySelector('.nb').firstChild, 5);
      editInput(document, window, 'insertParagraph');

      let code = document.querySelector('code');

      assert.deepEqual(
        [...code.querySelectorAll('.code-line__number')].map((node) => node.dataset.lineNumber),
        ['9', '10'],
      );
      assert.ok(
        [...code.querySelectorAll('.code-line__number')].every(
          (node) => node.getAttribute('contenteditable') === 'false' && node.textContent === '',
        ),
      );
      assert.equal(codeOffset(code, window.getSelection().anchorNode, window.getSelection().anchorOffset), 6);
      assert.equal(code.querySelector('.nb').textContent, 'print');
      editInput(document, window, 'deleteContentBackward');
      code = document.querySelector('code');
      assert.equal(code.querySelectorAll('.code-line').length, 1);
      assert.equal(code.querySelector('.code-line__content').textContent, 'print(1)');
    },
  );
});

test('multiline paste uses plain source and renumbers including trailing empty lines', () => {
  withEditor('<pre class="global-kit-code-block" data-line-start="50"><code>old</code></pre>', (document, window) => {
    mockOptionsEditing(document, window);
    selectText(document, window, document.querySelector('code'));

    const event = new window.Event('paste', { bubbles: true, cancelable: true });

    Object.defineProperty(event, 'clipboardData', {
      value: { getData: (type) => (type === 'text/plain' ? 'one\r\ntwo\r\n' : '<b>wrong</b>') },
    });
    document.querySelector('code').dispatchEvent(event);
    assert.equal(event.defaultPrevented, true);
    assert.deepEqual(
      [...document.querySelectorAll('.code-line__content')].map((node) => node.textContent),
      ['one', 'two', ''],
    );
    assert.deepEqual(
      [...document.querySelectorAll('.code-line__number')].map((node) => node.dataset.lineNumber),
      ['50', '51', '52'],
    );
    assert.ok(document.querySelector('[data-code-placeholder]'));
    editInput(document, window, 'insertText', 'last');
    assert.equal(document.querySelectorAll('.code-line__content')[2].textContent, 'last');
  });
});

function clipboardEvent(window, type, values) {
  const event = new window.Event(type, { bubbles: true, cancelable: true });

  Object.defineProperty(event, 'clipboardData', {
    value: {
      setData: (format, text) => {
        values[format] = text;
      },
      getData: (format) => values[format] || '',
    },
  });

  return event;
}

test('clicking a gutter selects only source and supports copy, paste, cut, and deletion', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-line-start="5" data-line-numbers="true"><code>first\nsecond</code></pre>',
    (document, window) => {
      mockOptionsEditing(document, window);
      selectText(document, window, document.querySelector('code'));
      globalThis.ankiGlobalKitEditor.openCodeBlockOptions();
      applyOptions(document);

      const click = (index) =>
        document
          .querySelectorAll('.code-line__number')
          .item(index)
          .dispatchEvent(new window.MouseEvent('mousedown', { bubbles: true, cancelable: true, button: 0 }));

      click(1);
      assert.equal(window.getSelection().toString(), 'second');

      const copied = {};
      const copy = clipboardEvent(window, 'copy', copied);

      document.querySelector('code').dispatchEvent(copy);
      assert.equal(copy.defaultPrevented, true);
      assert.deepEqual(copied, { 'text/plain': 'second' });
      document.querySelector('code').dispatchEvent(clipboardEvent(window, 'paste', { 'text/plain': 'replacement' }));
      assert.equal(document.querySelectorAll('.code-line__content')[1].textContent, 'replacement');
      click(0);

      const cut = {};

      document.querySelector('code').dispatchEvent(clipboardEvent(window, 'cut', cut));
      assert.deepEqual(cut, { 'text/plain': 'first' });
      assert.equal(document.querySelector('.code-line__content').textContent, '');
      click(1);
      editInput(document, window, 'deleteContentForward');
      assert.equal(document.querySelectorAll('.code-line__content')[1].textContent, '');
      assert.deepEqual(
        [...document.querySelectorAll('.code-line__number')].map((node) => node.dataset.lineNumber),
        ['5', '6'],
      );
    },
  );
});

test('keyboard line selection and multiline copy omit gutters and retain source newlines', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-line-start="10"><code>one\ntwo</code></pre>',
    (document, window) => {
      mockOptionsEditing(document, window);
      selectText(document, window, document.querySelector('code'));
      editInput(document, window, 'insertText', 'one\ntwo');
      document
        .querySelectorAll('.code-line__number')[1]
        .dispatchEvent(new window.KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Enter' }));
      assert.equal(window.getSelection().toString(), 'two');
      selectText(document, window, document.querySelector('code'));

      const copied = {};

      document.querySelector('code').dispatchEvent(clipboardEvent(window, 'copy', copied));
      assert.deepEqual(copied, { 'text/plain': 'one\ntwo' });
    },
  );
});

test('typing after Undo restores the old caret instead of replacing the restored field', () => {
  withEditor(
    '<pre class="global-kit-code-block" data-line-start="1"><code>first\nsecond</code></pre>',
    (document, window) => {
      const field = document.querySelector('anki-editable');
      let undoHtml;

      document.execCommand = (_command, _showUi, html) => {
        undoHtml = field.innerHTML;

        const range = window.getSelection().getRangeAt(0);

        range.deleteContents();
        range.insertNode(range.createContextualFragment(html));

        return true;
      };
      caret(document, window, document.querySelector('code').firstChild, 3);
      editInput(document, window, 'insertParagraph');
      field.innerHTML = undoHtml;
      field.dispatchEvent(new window.InputEvent('input', { bubbles: true, composed: true, inputType: 'historyUndo' }));

      const code = field.querySelector('code');
      const selection = window.getSelection();

      assert.equal(textFromCode(code), 'first\nsecond');
      assert.equal(selection.isCollapsed, true);
      assert.equal(codeOffset(code, selection.anchorNode, selection.anchorOffset), 3);
      assert.equal(field.querySelector('[data-anki-global-kit-edit-position]'), null);
      editInput(document, window, 'insertText', 'X');
      assert.equal(textFromCode(field.querySelector('code')), 'firXst\nsecond');
    },
  );
});
