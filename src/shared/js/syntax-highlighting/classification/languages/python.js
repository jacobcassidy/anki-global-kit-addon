import { parser } from '@lezer/python';
import { Scope, ancestor, child, moduleScope, nonlocalScope, text } from '../scopes.js';

const COMPREHENSIONS = [
  'ArrayComprehensionExpression',
  'DictionaryComprehensionExpression',
  'SetComprehensionExpression',
  'ComprehensionExpression',
];

const BUILTINS = new Map();

for (const name of `abs aiter all anext any ascii bin breakpoint callable chr compile delattr dir divmod
  enumerate eval exec filter format getattr globals hasattr hash help hex id input isinstance
  issubclass iter len locals map max min next oct open ord pow print repr reversed round
  setattr sorted sum vars zip __import__`.split(/\s+/)) {
  BUILTINS.set(name, { role: 'function', builtin: true });
}

for (const name of `bool bytearray bytes classmethod complex dict float frozenset int list memoryview
  object property range set slice staticmethod str super tuple type BaseException BaseExceptionGroup
  Exception ExceptionGroup ArithmeticError AssertionError AttributeError BlockingIOError BrokenPipeError
  BufferError BytesWarning ChildProcessError ConnectionAbortedError ConnectionError ConnectionRefusedError
  ConnectionResetError DeprecationWarning EOFError EncodingWarning EnvironmentError FileExistsError
  FileNotFoundError FloatingPointError FutureWarning GeneratorExit IOError ImportError ImportWarning
  IndentationError IndexError InterruptedError IsADirectoryError KeyError KeyboardInterrupt LookupError
  MemoryError ModuleNotFoundError NameError NotADirectoryError NotImplementedError OSError OverflowError
  PendingDeprecationWarning PermissionError ProcessLookupError RecursionError ReferenceError ResourceWarning
  RuntimeError RuntimeWarning StopAsyncIteration StopIteration SyntaxError SyntaxWarning SystemError
  SystemExit TabError TimeoutError TypeError UnboundLocalError UnicodeDecodeError UnicodeEncodeError
  UnicodeError UnicodeTranslateError UnicodeWarning UserWarning ValueError Warning ZeroDivisionError`.split(/\s+/)) {
  BUILTINS.set(name, { role: 'class', builtin: true });
}

for (const name of ['True', 'False', 'None', 'Ellipsis', 'NotImplemented', '__debug__']) {
  BUILTINS.set(name, { role: 'constant', builtin: true });
}

for (const name of [
  '__name__',
  '__file__',
  '__package__',
  '__doc__',
  '__spec__',
  '__loader__',
  '__builtins__',
  '__annotations__',
]) {
  BUILTINS.set(name, { role: 'variable', builtin: true });
}

function outsideClass(scope) {
  while (scope.kind === 'class') scope = scope.parent;

  return scope;
}

function isCallTarget(node) {
  let target = node;

  while (target.parent?.name === 'ParenthesizedExpression') target = target.parent;

  return target.parent?.name === 'CallExpression' && target.parent.children[0] === target;
}

function assignmentRole(value) {
  while (value?.name === 'ParenthesizedExpression') {
    value = value.children.find((item) => item.name !== '(' && item.name !== ')');
  }

  return value?.name === 'LambdaExpression' ? 'function' : 'variable';
}

function lastAssignment(parts) {
  for (let index = parts.length - 1; index >= 0; index -= 1) {
    if (parts[index].name === 'AssignOp') return index;
  }

  return -1;
}

function targetNames(node) {
  if (node.name === 'VariableName') return [node];

  if (
    !['TupleExpression', 'ArrayExpression', 'CapturePattern', 'StarPattern', 'SequencePattern', 'AsPattern'].includes(
      node.name,
    )
  )
    return [];

  const names = [];
  const pending = [...node.children];

  while (pending.length) {
    const item = pending.pop();

    if (item.name === 'VariableName') names.push(item);
    else if (item.name !== 'MemberExpression') pending.push(...item.children);
  }

  return names;
}

function declare(node, role, source, pending, scope = node.scope) {
  const name = text(node, source);
  const directive = scope.directives.get(name);

  if (directive === 'global') scope = moduleScope(scope);

  if (directive === 'nonlocal') {
    pending.push({ node, name, role, scope });
    return;
  }

  node.binding = scope.define(name, role);
}

function declareTargets(nodes, role, source, pending, scope) {
  for (const target of nodes) {
    for (const name of targetNames(target)) declare(name, role, source, pending, scope || name.scope);
  }
}

function parameterBindings(node, source, pending) {
  const params = child(node, 'ParamList');

  if (!params) return;

  let expectingName = true;

  for (const item of params.children) {
    if (item.name === ',' || item.name === '*' || item.name === '**') expectingName = true;

    if (item.name === 'VariableName' && expectingName) {
      declare(item, 'parameter', source, pending, node.scope);
      expectingName = false;
    }
  }
}

function importBindings(node, source, pending) {
  const parts = node.children;
  const fromImport = parts[0]?.name === 'from';
  let importing = !fromImport;
  let firstInGroup = true;
  let alias = false;

  // Parenthesized from-imports wrap their names in ImportList.
  const items = [];

  for (const item of parts) items.push(...(item.name === 'ImportList' ? item.children : [item]));

  for (let index = 0; index < items.length; index += 1) {
    node.scope.budget.check();

    const item = items[index];

    if (item.name === 'import') {
      importing = true;
      continue;
    }

    if (item.name === ',') {
      firstInGroup = true;
      alias = false;
      continue;
    }

    if (item.name === 'as') {
      alias = true;
      continue;
    }

    if (item.name !== 'VariableName') continue;

    item.importRole = 'namespace';

    if (!importing) continue;

    let hasAlias = false;

    for (let next = index + 1; next < items.length && items[next].name !== ','; next += 1) {
      node.scope.budget.check();

      if (items[next].name === 'as') hasAlias = true;
    }

    if (alias || (firstInGroup && !hasAlias)) {
      declare(item, fromImport ? null : 'namespace', source, pending, node.scope);
    }

    if (fromImport) item.importRole = 'variable';

    firstInGroup = false;
  }
}

function propertyDefinition(node, source) {
  const decorated = node.parent?.name === 'DecoratedStatement' ? node.parent : null;

  if (!decorated) return false;

  for (const decorator of decorated.children.filter((item) => item.name === 'Decorator')) {
    const expression = text(decorator, source).replace(/^@\s*/, '').trim();

    if (expression === 'property' && !node.definitionScope.lookup('property')) return true;

    const accessor = /^(\w+)\.(getter|setter|deleter)$/.exec(expression);

    if (accessor && node.definitionScope.lookup(accessor[1])?.role === 'property') return true;
  }

  return false;
}

/** Resolve Python bindings, including function-wide locals and comprehension scopes. */
function classify(nodes, source, budget) {
  const root = new Scope();
  const pending = [];

  root.budget = budget;

  for (const node of nodes) {
    budget.check();
    node.scope = node.parent?.scope || root;

    if (node.parent?.name === 'ParamList' && node.scope.owner?.definitionScope) {
      // A lambda/default nested in a Python signature also closes over its outer scope.
      node.scope = node.scope.owner.definitionScope;
    }

    if (
      ['FunctionDefinition', 'LambdaExpression', 'ClassDefinition'].includes(node.name) ||
      COMPREHENSIONS.includes(node.name)
    ) {
      node.definitionScope = node.scope;

      const kind =
        node.name === 'ClassDefinition' ? 'class' : COMPREHENSIONS.includes(node.name) ? 'comprehension' : 'function';

      node.scope = new Scope(outsideClass(node.scope), kind);
      node.scope.owner = node;
    }
  }

  for (const node of nodes) {
    budget.check();

    if (node.name === 'ScopeStatement') {
      const directive = node.children[0]?.name;

      for (const name of node.children.filter((item) => item.name === 'VariableName')) {
        node.scope.directives.set(text(name, source), directive);
      }
    }
  }

  for (const node of nodes) {
    budget.check();

    if (node.name === 'FunctionDefinition' || node.name === 'ClassDefinition') {
      const name = child(node, 'VariableName');
      const role =
        node.name === 'ClassDefinition' ? 'class' : node.definitionScope.kind === 'class' ? 'method' : 'function';

      if (name) declare(name, role, source, pending, node.definitionScope);

      parameterBindings(node, source, pending);
    } else if (node.name === 'LambdaExpression') {
      parameterBindings(node, source, pending);
    } else if (node.name === 'AssignStatement') {
      const parts = node.children;
      const lastAssign = lastAssignment(parts);

      if (lastAssign >= 0) {
        const role = assignmentRole(parts[lastAssign + 1]);

        // Every expression followed by an assignment operator is a target.
        let start = 0;

        for (let index = 0; index <= lastAssign; index += 1) {
          if (parts[index].name === 'AssignOp') {
            const targets = parts.slice(start, index).filter((item) => item.name !== 'TypeDef');

            declareTargets(targets, role, source, pending);
            start = index + 1;
          }
        }
      } else {
        declareTargets(parts.slice(0, 1), 'variable', source, pending);
      }
    } else if (node.name === 'UpdateStatement') {
      declareTargets(node.children.slice(0, 1), 'variable', source, pending);
    } else if (node.name === 'DeleteStatement') {
      declareTargets(node.children.slice(1), 'variable', source, pending);
    } else if (node.name === 'ForStatement' || COMPREHENSIONS.includes(node.name)) {
      const parts = node.children;

      for (let index = 0; index < parts.length; index += 1) {
        if (parts[index].name !== 'for') continue;

        const inIndex = parts.findIndex((item, position) => position > index && item.name === 'in');

        if (inIndex >= 0) declareTargets(parts.slice(index + 1, inIndex), 'variable', source, pending);
      }
    } else if (node.name === 'NamedExpression') {
      let scope = node.scope;

      while (scope.kind === 'comprehension') scope = scope.parent;
      declareTargets(node.children.slice(0, 1), 'variable', source, pending, scope);
    } else if (node.name === 'WithStatement' || node.name === 'TryStatement') {
      for (let index = 0; index < node.children.length - 1; index += 1) {
        if (node.children[index].name === 'as') {
          declareTargets([node.children[index + 1]], 'variable', source, pending);
        }
      }
    } else if (node.name === 'CapturePattern') {
      declareTargets([node], 'variable', source, pending);
    } else if (node.name === 'ImportStatement') {
      importBindings(node, source, pending);
    }
  }

  for (const declaration of pending) {
    const scope = nonlocalScope(declaration.scope, declaration.name);

    if (scope) declaration.node.binding = scope.bindings.get(declaration.name);
  }

  for (const node of nodes) {
    if (node.name !== 'FunctionDefinition' || node.definitionScope.kind !== 'class') continue;

    const name = child(node, 'VariableName');

    if (name?.binding && propertyDefinition(node, source)) {
      name.binding.role = 'property';
      node.definitionScope.bindings.get(text(name, source)).role = 'property';
    }
  }

  const spans = [];

  for (const node of nodes) {
    budget.check();

    const name = text(node, source);
    let result = null;

    if (node.binding) {
      result = { ...node.binding, role: node.binding.role || 'variable' };
    } else if (node.name === 'def' || node.name === 'class') {
      result = { role: 'declaration' };
    } else if (node.name === 'Boolean' || node.name === 'None') {
      result = { role: 'constant', builtin: true };
    } else if (node.name === 'PropertyName') {
      result = { role: isCallTarget(node.parent) ? 'method' : 'property' };
    } else if (node.name === 'VariableName') {
      let scope = node.scope;
      const params = ancestor(node, ['ParamList']);
      const comprehension = ancestor(node, COMPREHENSIONS);
      const annotation = ancestor(node, ['TypeDef']);

      // Defaults and annotations are evaluated outside the function being defined.
      if (params && params.scope === scope) scope = scope.owner?.definitionScope || scope;

      if (annotation?.parent?.name === 'FunctionDefinition') scope = annotation.parent.definitionScope;

      if (comprehension && scope === comprehension.scope) {
        const firstIn = comprehension.children.findIndex((item) => item.name === 'in');
        const iterable = comprehension.children[firstIn + 1];

        if (iterable && node.from >= iterable.from && node.to <= iterable.to) scope = comprehension.definitionScope;
      }

      const binding = scope.lookup(name);

      if (node.importRole) {
        result = { role: node.importRole };
      } else if (
        node.parent?.name === 'Decorator' &&
        node.parent.children[node.parent.children.indexOf(node) - 1]?.name === '.'
      ) {
        result = { role: 'property' };
      } else if (
        node.parent?.name === 'ArgList' &&
        node.parent.children[node.parent.children.indexOf(node) + 1]?.name === 'AssignOp'
      ) {
        result = { role: 'parameter' };
      } else if (binding?.role) {
        result = binding;
      } else if (!binding && BUILTINS.has(name)) {
        result = BUILTINS.get(name);
      } else {
        result = { role: isCallTarget(node) ? 'function' : 'variable' };
      }
    }

    if (result) spans.push({ from: node.from, to: node.to, builtin: false, ...result });
  }

  return spans;
}

export default { parser, classify };
