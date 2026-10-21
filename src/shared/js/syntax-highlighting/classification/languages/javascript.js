import { parser } from '@lezer/javascript';
import { Scope, ancestor, child, descendants, text as sourceText } from '../scopes.js';

const FUNCTIONS = ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunction', 'MethodDeclaration'];
const CLASSES = ['ClassDeclaration', 'ClassExpression'];
const STOP_BINDINGS = [...FUNCTIONS, ...CLASSES];
const BUILTINS = new Map();

for (const name of `Object Function Boolean Symbol Number BigInt Math Date String RegExp Array
  Int8Array Uint8Array Uint8ClampedArray Int16Array Uint16Array Int32Array Uint32Array
  Float32Array Float64Array BigInt64Array BigUint64Array Map Set WeakMap WeakSet
  ArrayBuffer SharedArrayBuffer DataView Atomics JSON Promise Reflect Proxy Intl
  WeakRef FinalizationRegistry Error AggregateError EvalError RangeError ReferenceError
  SyntaxError TypeError URIError`.split(/\s+/)) {
  BUILTINS.set(name, { role: 'class', builtin: true });
}

for (const name of 'eval isFinite isNaN parseFloat parseInt decodeURI decodeURIComponent encodeURI encodeURIComponent'.split(
  ' ',
)) {
  BUILTINS.set(name, { role: 'function', builtin: true });
}

for (const name of ['undefined', 'NaN', 'Infinity']) {
  BUILTINS.set(name, { role: 'constant', builtin: true });
}

BUILTINS.set('globalThis', { role: 'variable', builtin: true });

function text(node, source) {
  const value = sourceText(node, source);

  if (!['VariableName', 'VariableDefinition', 'PropertyName', 'PropertyDefinition'].includes(node.name)) return value;

  return value.replace(/\\u(?:\{([\da-fA-F]{1,6})\}|([\da-fA-F]{4}))/g, (_match, codepoint, unit) =>
    String.fromCodePoint(Number.parseInt(codepoint || unit, 16)),
  );
}

function isFunction(node) {
  return FUNCTIONS.includes(node.name) || (node.name === 'Property' && child(node, 'ParamList'));
}

function initializer(node) {
  const siblings = node.parent.children;
  const index = siblings.indexOf(node);

  return siblings[index + 1]?.name === 'Equals' ? siblings[index + 2] : null;
}

function variableRole(node) {
  let value = initializer(node);

  while (value?.name === 'ParenthesizedExpression') {
    value = value.children.find((item) => item.name !== '(' && item.name !== ')');
  }

  if (value && isFunction(value)) return 'function';

  if (value && CLASSES.includes(value.name)) return 'class';

  return 'variable';
}

function bindingScope(node) {
  const declaration = ancestor(node, ['VariableDeclaration', 'ForInSpec', 'ForOfSpec']);
  let scope = node.scope;

  if (declaration?.children.some((item) => item.name === 'var')) {
    while (scope.parent && scope.kind !== 'function') scope = scope.parent;
  }

  return scope;
}

function isCallTarget(node) {
  let target = node;

  while (target.parent?.name === 'ParenthesizedExpression') target = target.parent;

  const parent = target.parent;

  return ['CallExpression', 'TaggedTemplateExpression'].includes(parent?.name) && parent.children[0] === target;
}

function propertyRole(node) {
  const parent = node.parent;

  if (parent.name === 'MemberExpression') return isCallTarget(parent) ? 'method' : 'property';

  if (parent.name === 'MethodDeclaration' || (parent.name === 'Property' && child(parent, 'ParamList'))) {
    return parent.children.some((item) => item.name === 'get' || item.name === 'set') ? 'property' : 'method';
  }

  if (parent.name === 'Property') {
    if (parent.children.some((item) => FUNCTIONS.includes(item.name))) return 'method';

    // A shorthand property is also a reference to the local binding.
    if (parent.children.length === 1) return null;
  }

  return 'property';
}

/** Collect JavaScript scopes before resolving references, including hoisted names. */
function classify(nodes, source, budget) {
  const root = new Scope();

  root.budget = budget;

  for (const node of nodes) {
    budget.check();
    node.scope = node.parent?.scope || root;

    if (isFunction(node)) {
      const outer = node.scope;
      const name = child(node, 'VariableDefinition');
      const scope = new Scope(outer, 'function');

      node.scope = scope;

      if (name && node.name !== 'ArrowFunction') {
        name.binding = (node.name === 'FunctionDeclaration' ? outer : scope).define(text(name, source), 'function');
      }

      const parameters = child(node, 'ParamList');
      const bindings = parameters ? descendants(parameters, STOP_BINDINGS, budget) : node.children;

      for (const parameter of bindings) {
        if (parameter.name === 'VariableDefinition' && !parameter.binding) {
          parameter.binding = scope.define(text(parameter, source), 'parameter');
        }
      }
    } else if (CLASSES.includes(node.name)) {
      const outer = node.scope;
      const name = child(node, 'VariableDefinition');

      node.scope = new Scope(outer, 'class');

      if (name) {
        name.binding = (node.name === 'ClassDeclaration' ? outer : node.scope).define(text(name, source), 'class');
      }
    } else if (['Block', 'CatchClause', 'ForStatement', 'SwitchBody'].includes(node.name)) {
      node.scope = new Scope(node.scope, node.name === 'Block' && isFunction(node.parent) ? 'function' : 'block');
    }

    if (node.name === 'VariableDefinition' && !node.binding) {
      const imported = ancestor(node, ['ImportDeclaration']);
      const namespace = imported?.children.some((item) => item.name === 'Star');
      const role = imported ? (namespace ? 'namespace' : null) : variableRole(node);

      const scope = bindingScope(node);
      const parameter = scope.kind === 'function' && scope.parent?.bindings.get(text(node, source));
      const declaration = ancestor(node, ['VariableDeclaration']);

      node.binding =
        parameter?.role === 'parameter' && declaration?.children.some((item) => item.name === 'var')
          ? parameter
          : scope.define(text(node, source), role);
    }
  }

  const spans = [];

  for (const node of nodes) {
    budget.check();

    const name = text(node, source);
    let result = null;

    if (node.binding) {
      result = { ...node.binding, role: node.binding.role || 'variable' };
    } else if (['function', 'class', 'let', 'const', 'var'].includes(node.name)) {
      result = { role: 'declaration' };
    } else if (['true', 'false', 'null'].includes(node.name)) {
      result = { role: 'constant', builtin: true };
    } else if (['this', 'super'].includes(node.name)) {
      result = { role: 'variable', builtin: true };
    } else if (
      ['PropertyName', 'PropertyDefinition', 'PrivatePropertyName', 'PrivatePropertyDefinition'].includes(node.name)
    ) {
      const role = propertyRole(node);

      const binding = node.scope.lookup(name);

      result = role
        ? { role }
        : binding
          ? { ...binding, role: binding.role || 'variable' }
          : BUILTINS.get(name) || { role: 'variable' };
    } else if (node.name === 'VariableName') {
      const binding = node.scope.lookup(name);

      if (ancestor(node, ['ImportDeclaration'])) {
        result = { role: 'variable' };
      } else if (binding?.role) {
        result = binding;
      } else if (!binding && BUILTINS.has(name)) {
        result = BUILTINS.get(name);
      } else {
        const parent = node.parent;
        const constructor =
          parent?.name === 'NewExpression' && parent.children.find((item) => item.name !== 'new') === node;

        result = { role: constructor ? 'class' : isCallTarget(node) ? 'function' : 'variable' };
      }
    }

    if (result) spans.push({ from: node.from, to: node.to, builtin: false, ...result });
  }

  return spans;
}

export default { parser, classify };
