import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { installCodeBlockHighlighting } from '../../../src/editor/js/formatting/code-block.js';

function withEditor(html, callback) {
  const dom = new JSDOM(`<body><anki-editable contenteditable="true">${html}</anki-editable></body>`);
  const previous = {
    document: globalThis.document,
    window: globalThis.window,
    Node: globalThis.Node,
    InputEvent: globalThis.InputEvent,
    pycmd: globalThis.pycmd,
    require: globalThis.require,
    api: globalThis.ankiGlobalKitEditor,
    settings: globalThis.ankiGlobalKitEditorSettings,
  };
  globalThis.document = dom.window.document;
  globalThis.window = dom.window;
  globalThis.Node = dom.window.Node;
  globalThis.InputEvent = dom.window.InputEvent;
  globalThis.pycmd = (message) => callback.message?.(message);
  globalThis.ankiGlobalKitEditor = {};
  globalThis.ankiGlobalKitEditorSettings = {
    anki_editor_syntax_highlighting_line_numbers: true,
    anki_editor_syntax_highlighting_line_number_start: 50,
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

test('highlight action submits selection and applies returned tokens as one edit', () => {
  withEditor('<p>const answer = 42;</p>', (document, window) => {
    const field = document.querySelector('anki-editable');
    selectText(document, window, field.querySelector('p'));
    let request;
    globalThis.pycmd = (message) => {
      if (message.startsWith('anki-global-kit:syntax-highlight:')) {
        request = JSON.parse(message.slice(message.indexOf('{')));
      }
    };

    assert.equal(globalThis.ankiGlobalKitEditor.highlightCode('', 'javascript'), true);
    assert.equal(request.source, 'const answer = 42;');
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
    assert.equal(field.querySelector('pre.agk-code-block').dataset.language, 'javascript');
    assert.equal(field.querySelector('code').textContent, request.source);
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
  withEditor('<p>first\nsecond</p>', (document, window) => {
    const field = document.querySelector('anki-editable');
    selectText(document, window, field.querySelector('p'));
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
    const block = field.querySelector('pre.agk-code-block');
    assert.equal(block.dataset.lineNumbers, 'true');
    assert.equal(block.dataset.lineStart, '50');
    assert.deepEqual(
      [...block.querySelectorAll('.agk-code-line')].map((line) => line.dataset.lineNumber),
      ['50', '51'],
    );

    selectText(document, window, block.querySelector('code'));
    globalThis.ankiGlobalKitEditor.highlightCode('', 'javascript');
    assert.equal(request.source, 'first\nsecond');
    assert.equal(request.lineNumbers, true);
    assert.equal(request.lineStart, 50);
  });
});

test('language priority is explicit choice, existing block, Topic, remembered, then default', () => {
  withEditor('<pre class="agk-code-block"><code data-language="python">print(1)</code></pre>', (document, window) => {
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
  });
});
