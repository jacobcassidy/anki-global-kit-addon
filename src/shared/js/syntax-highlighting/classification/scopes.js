/** A lexical scope. Adapters choose its parent according to language rules. */
export class Scope {
  constructor(parent = null, kind = 'module') {
    this.parent = parent;
    this.kind = kind;
    this.bindings = new Map();
    this.directives = new Map();
    this.budget = parent?.budget;
  }

  define(name, role, builtin = false) {
    this.budget?.check();

    const existing = this.bindings.get(name);

    // Reassigning a parameter does not change its role throughout the scope.
    if (existing?.role === 'parameter') return existing;

    const binding = { role, builtin };

    this.bindings.set(name, binding);

    return binding;
  }

  lookup(name) {
    let scope = this;

    while (scope) {
      this.budget?.check();
      const directive = scope.directives.get(name);

      if (directive === 'global') {
        scope = moduleScope(scope);
      } else if (directive === 'nonlocal') {
        scope = nonlocalScope(scope, name);

        if (!scope) return { role: null, builtin: false };
      }

      if (scope.bindings.has(name)) return scope.bindings.get(name);

      scope = scope.parent;
    }

    return null;
  }
}

export function moduleScope(scope) {
  while (scope.parent) scope = scope.parent;

  return scope;
}

export function nonlocalScope(scope, name) {
  for (let parent = scope.parent; parent; parent = parent.parent) {
    if (parent.kind !== 'module' && parent.bindings.has(name)) return parent;
  }

  return null;
}

export function child(node, name) {
  return node?.children.find((item) => item.name === name);
}

export function ancestor(node, names) {
  for (let parent = node.parent; parent; parent = parent.parent) {
    if (names.includes(parent.name)) return parent;
  }

  return null;
}

export function text(node, source) {
  return source.slice(node.from, node.to);
}

/** Walk a subtree without recursive calls or descending into excluded nodes. */
export function descendants(node, stop = [], budget) {
  const result = [];
  const pending = [...node.children].reverse();

  while (pending.length) {
    budget?.check();
    const current = pending.pop();

    if (stop.includes(current.name)) continue;

    result.push(current);

    for (let index = current.children.length - 1; index >= 0; index -= 1) {
      pending.push(current.children[index]);
    }
  }

  return result;
}

/** Materialize parser nodes once, retaining parent links and document order. */
export function readTree(tree, budget) {
  const cursor = tree.cursor();
  const nodes = [];
  let parent = null;

  for (;;) {
    budget.check();

    const node = {
      name: cursor.name,
      from: cursor.from,
      to: cursor.to,
      error: cursor.type.isError,
      parent,
      children: [],
    };

    nodes.push(node);
    parent?.children.push(node);

    if (cursor.firstChild()) {
      parent = node;
      continue;
    }

    while (!cursor.nextSibling()) {
      if (!cursor.parent()) return nodes;
      parent = parent.parent;
    }
  }
}
