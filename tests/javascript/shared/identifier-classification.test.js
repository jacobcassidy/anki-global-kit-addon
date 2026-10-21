import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import {
  classifyCode,
  createClassificationBudget,
  supportsClassification,
} from '../../../src/shared/js/syntax-highlighting/classification/index.js';
import { enhanceHighlightHtml } from '../../../src/shared/js/syntax-highlighting/classification/markup.js';
import { themeRole } from '../../../src/shared/js/syntax-highlighting/classification/roles.js';
import { highlightReviewCode } from '../../../src/cards/js/syntax-highlighting/engine.js';

function tokens(source, language) {
  const spans = classifyCode(source, language, { budget: createClassificationBudget(2000) });

  return spans.map((span) => ({ text: source.slice(span.from, span.to), ...span }));
}

function roles(source, language, name) {
  return tokens(source, language)
    .filter((item) => item.text === name)
    .map(themeRole);
}

test('the supplied JavaScript example distinguishes functions, methods, parameters, and properties', () => {
  const source = readFileSync(
    new URL('../../fixtures/syntax-highlighting/javascript-identifiers.txt', import.meta.url),
    'utf8',
  );
  const expected = {
    updateClozeTooltips: 'function',
    clozeButtons: 'function',
    forEach: 'method',
    replace: 'method',
    button: 'parameter',
    index: 'parameter',
    labels: 'variable',
    updated: 'variable',
    function: 'declaration',
    const: 'declaration',
  };

  for (const [name, role] of Object.entries(expected)) {
    assert.ok(roles(source, 'javascript', name).length, name);
    assert.ok(
      roles(source, 'javascript', name).every((actual) => actual === role),
      name,
    );
  }

  assert.deepEqual(roles(source, 'javascript', 'title'), [
    'variable',
    'attribute',
    'variable',
    'attribute',
    'attribute',
  ]);
});

test('JavaScript resolves callbacks, destructuring, lexical scopes, and shadowed builtins', () => {
  const source = `const result = String(value);
function outer(String, callback, {title: label}, ...rest) {
  const f = (value) => value.title;
  callback(label);
  String(rest);
  { const callback = value; callback(); }
  return f(label) + callback(rest);
}`;

  assert.deepEqual(roles(source, 'javascript', 'String'), ['builtin', 'parameter', 'parameter']);
  assert.deepEqual(roles(source, 'javascript', 'callback'), [
    'parameter',
    'parameter',
    'variable',
    'variable',
    'parameter',
  ]);
  assert.deepEqual(roles(source, 'javascript', 'label'), ['parameter', 'parameter', 'parameter']);
  assert.deepEqual(roles(source, 'javascript', 'title'), ['attribute', 'attribute']);
  assert.deepEqual(roles(source, 'javascript', 'f'), ['function', 'function']);
  assert.deepEqual(roles(source, 'javascript', 'rest'), ['parameter', 'parameter', 'parameter']);
});

test('JavaScript handles imports, named expressions, var hoisting, classes, and optional members', () => {
  const source = `import * as helpers from 'helpers';
import {String} from 'custom';
const f = function named(param) { return named(param); };
function g(param = String) { var String; var param; return param; }
class Demo { method(value) { this.title = value; return this?.title?.replace(value); } }
helpers.run(String); f(1); named(1); new Demo();`;

  assert.deepEqual(roles(source, 'javascript', 'helpers'), ['namespace', 'namespace']);
  assert.ok(roles(source, 'javascript', 'String').every((role) => role === 'variable'));
  assert.deepEqual(roles(source, 'javascript', 'named'), ['function', 'function', 'function']);
  assert.deepEqual(roles(source, 'javascript', 'param'), [
    'parameter',
    'parameter',
    'parameter',
    'parameter',
    'parameter',
  ]);
  assert.deepEqual(roles(source, 'javascript', 'Demo'), ['class', 'class']);
  assert.deepEqual(roles(source, 'javascript', 'method'), ['method']);
  assert.deepEqual(roles(source, 'javascript', 'title'), ['attribute', 'attribute']);
  assert.deepEqual(roles(source, 'javascript', 'replace'), ['method']);
});

test('Python colors methods, builtin calls, parameters and their references', () => {
  const source = `import math as maths
class Demo:
    def format(self, value: str, callback):
        result = str(value)
        self.title = result
        callback(value)
        return True, self.title, maths.pi, __name__
`;

  assert.deepEqual(roles(source, 'python', 'Demo'), ['class']);
  assert.deepEqual(roles(source, 'python', 'format'), ['method']);
  assert.ok(roles(source, 'python', 'self').every((role) => role === 'parameter'));
  assert.ok(roles(source, 'python', 'value').every((role) => role === 'parameter'));
  assert.deepEqual(roles(source, 'python', 'callback'), ['parameter', 'parameter']);
  assert.deepEqual(roles(source, 'python', 'str'), ['builtin', 'builtin']);
  assert.deepEqual(roles(source, 'python', 'title'), ['attribute', 'attribute']);
  assert.deepEqual(roles(source, 'python', 'maths'), ['namespace', 'namespace']);
  assert.deepEqual(roles(source, 'python', 'True'), ['builtin-constant']);
  assert.deepEqual(roles(source, 'python', '__name__'), ['library-variable']);
  assert.deepEqual(roles(source, 'python', 'def'), ['declaration']);
});

test('closures in Python defaults do not capture the function being defined', () => {
  const source = 'def f(str=lambda: str()):\n return str()\n';

  assert.deepEqual(roles(source, 'python', 'str'), ['parameter', 'builtin', 'parameter']);
  assert.deepEqual(roles('convert = (lambda value: value)\nconvert(1)\n', 'python', 'convert'), [
    'function',
    'function',
  ]);
});

test('JavaScript preserves escaped bindings and distinguishes accessors from methods', () => {
  const source = String.raw`const f = (function named(value) { return value; });
const \u0061 = (value) => value;
class Demo { get title() { return this.name; } set title(value) { this.name = value; } }
a(1); named; ({String});`;

  assert.deepEqual(roles(source, 'javascript', 'f'), ['function']);
  assert.deepEqual(roles(source, 'javascript', 'a'), ['function']);
  assert.deepEqual(roles(source, 'javascript', 'named'), ['function', 'variable']);
  assert.deepEqual(roles(source, 'javascript', 'title'), ['attribute', 'attribute']);
  assert.deepEqual(roles(source, 'javascript', 'String'), ['builtin']);
});

test('Python resolves function-wide locals, defaults, comprehensions, and shadowing', () => {
  const source = `def f(items, str, *, extra=1, **kwargs):
    convert = lambda value: value
    return [convert(str(item)) for item in items if item], str(extra), kwargs
def g(value=str) -> str:
    str = custom
    return str(value)
str(value)
`;

  assert.deepEqual(roles(source, 'python', 'str'), [
    'parameter',
    'parameter',
    'parameter',
    'builtin',
    'builtin',
    'variable',
    'variable',
    'builtin',
  ]);
  assert.deepEqual(roles(source, 'python', 'convert'), ['function', 'function']);
  assert.ok(roles(source, 'python', 'items').every((role) => role === 'parameter'));
  assert.ok(roles(source, 'python', 'kwargs').every((role) => role === 'parameter'));
  assert.ok(roles(source, 'python', 'item').every((role) => role === 'variable'));
});

test('Python handles global and nonlocal bindings, property decorators, and imports', () => {
  const source = `from custom import str as convert
import os.path as path, math
value = 1
def outer(callback):
    def inner():
        nonlocal callback
        global value
        callback = replacement
        value = callback()
    return inner
class Demo:
    @property
    def title(self):
        return self.name
    @title.setter
    def title(self, value):
        self.name = value
convert(path.name)
`;

  assert.ok(roles(source, 'python', 'callback').every((role) => role === 'parameter'));
  assert.ok(
    roles(source, 'python', 'value')
      .slice(0, 3)
      .every((role) => role === 'variable'),
  );
  assert.deepEqual(roles(source, 'python', 'title'), ['attribute', 'attribute', 'attribute']);
  assert.deepEqual(roles(source, 'python', 'convert'), ['variable', 'function']);
  assert.deepEqual(roles(source, 'python', 'path'), ['namespace', 'namespace', 'namespace']);
});

test('classification recovers snippets and ignores literal contents but visits interpolations', () => {
  assert.deepEqual(roles('items.forEach((button, index) => { button.title = labels[index]', 'javascript', 'button'), [
    'parameter',
    'parameter',
  ]);
  assert.deepEqual(roles('    return self.title.replace(value)\n', 'python', 'replace'), ['method']);

  const source = '// fake.call(param)\nconst label = `😀 ${value.title}`; const regex = /fake.call(param)/;';

  assert.deepEqual(roles(source, 'javascript', 'fake'), []);
  assert.deepEqual(roles(source, 'javascript', 'title'), ['attribute']);
  assert.deepEqual(roles('value = f"😀 {person.title}"\n', 'python', 'title'), ['attribute']);

  const spans = tokens(source, 'javascript');

  for (let index = 1; index < spans.length; index += 1) assert.ok(spans[index].from >= spans[index - 1].to);
});

test('cloze ranges remain opaque and offsets stay correct after nested clozes and emoji', () => {
  const source = 'const note = {{c1::😀 {{c2::hidden.name}}::hint}}; callback(value.title);';
  const spans = tokens(source, 'javascript');

  assert.ok(spans.every((span) => span.to <= source.indexOf('{{') || span.from >= source.indexOf('; callback')));
  assert.deepEqual(roles(source, 'javascript', 'callback'), ['function']);
  assert.deepEqual(roles(source, 'javascript', 'title'), ['attribute']);
});

test('unsupported languages, oversized input, and expired budgets retain base highlighting', () => {
  assert.equal(supportsClassification('typescript'), false);
  assert.equal(supportsClassification('constructor'), false);
  assert.equal(supportsClassification('py'), true);
  assert.deepEqual(classifyCode('x();', 'ruby'), []);
  assert.deepEqual(classifyCode('x '.repeat(25_001), 'javascript'), []);

  let time = 0;
  const budget = createClassificationBudget(1, () => time++);

  assert.deepEqual(classifyCode('def f(value): return value', 'python', { budget }), []);
});

test('the HTML overlay handles split token leaves, Unicode, escaping, and clozes without changing text', () => {
  const dom = new JSDOM('');
  const owner = dom.window.document;
  const html =
    '<span class="kd">function</span> <span class="nx">ex</span><span class="nx">ample</span>(value) { return "😀 &lt;b&gt;" + value.title + {{c1::hidden.name}}; }';

  try {
    const enriched = enhanceHighlightHtml(html, 'javascript', {
      document: owner,
      budget: createClassificationBudget(2000),
    });
    const base = owner.createElement('div');
    const result = owner.createElement('div');

    base.innerHTML = html;
    result.innerHTML = enriched;
    assert.equal(result.textContent, base.textContent);
    assert.deepEqual(
      [...result.querySelectorAll('[data-global-kit-token="function"]')].map((span) => span.textContent),
      ['ex', 'ample'],
    );
    assert.equal(result.querySelector('[data-global-kit-token="attribute"]').textContent, 'title');
    assert.match(enriched, /\{\{c1::hidden.name\}\}/);

    const expired = createClassificationBudget(0);

    assert.equal(enhanceHighlightHtml(html, 'javascript', { document: owner, budget: expired }), html);
  } finally {
    dom.window.close();
  }
});

test('Pygments editor output and highlight.js review output receive identical identifier roles', () => {
  const dom = new JSDOM('');
  const owner = dom.window.document;
  const sources = {
    javascript: 'function example(value) { return value.title.replace(String(value)); }',
    python: 'def example(value):\n    return str(value.title), True\n',
  };

  try {
    for (const [language, source] of Object.entries(sources)) {
      const pygments = execFileSync(
        'python3',
        [
          '-c',
          'import sys; from scripts.addon_module_loader import load_addon_module; print(load_addon_module("desktop.syntax_highlighting.rendering").render_code(sys.stdin.read(), sys.argv[1])[0], end="")',
          language,
        ],
        { input: source, encoding: 'utf8' },
      );
      const editor = enhanceHighlightHtml(pygments, language, {
        document: owner,
        budget: createClassificationBudget(2000),
      });
      const review = highlightReviewCode(source, language, {
        document: owner,
        budget: createClassificationBudget(2000),
      });
      const annotations = (html) => {
        const container = owner.createElement('div');

        container.innerHTML = html;

        return [...container.querySelectorAll('[data-global-kit-token]')].map((item) => [
          item.textContent,
          item.dataset.globalKitToken,
        ]);
      };

      assert.deepEqual(annotations(editor), annotations(review), language);
    }
  } finally {
    dom.window.close();
  }
});
