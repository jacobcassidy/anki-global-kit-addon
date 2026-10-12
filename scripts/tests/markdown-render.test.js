import assert from 'node:assert/strict';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { markdownToHtml } from '../../src/cards/js/markdown/render.js';

test('ordered lists retain non-default starting numbers, including zero', () => {
  for (const start of [0, 1, 5, 42]) {
    const dom = new JSDOM(markdownToHtml(`${start}. First\n${start + 1}. Second`));
    try {
      const list = dom.window.document.querySelector('ol');
      assert.equal(list.start, start);
      assert.equal(list.children.length, 2);
      assert.equal(list.children[0].textContent.trim(), 'First');
      if (start === 1) assert.equal(list.hasAttribute('start'), false);
    } finally {
      dom.window.close();
    }
  }
});

test('nested ordered lists retain their own starting number without restarting their parent', () => {
  const dom = new JSDOM(markdownToHtml('4. Parent\n  7. Child\n  8. Next child\n5. Next parent'));
  try {
    const [parent, child] = dom.window.document.querySelectorAll('ol');
    assert.equal(parent.start, 4);
    assert.equal(child.start, 7);
    assert.equal(parent.children.length, 2);
    assert.equal(child.children.length, 2);
    assert.equal(child.parentElement, parent.children[0]);
  } finally {
    dom.window.close();
  }
});

test('separate lists and mixed list types preserve each ordered run start', () => {
  const dom = new JSDOM(markdownToHtml('3. First\n\n9. Separate\n- Unordered\n  6. Nested ordered'));
  try {
    const lists = [...dom.window.document.querySelectorAll('ol')];
    assert.deepEqual(
      lists.map((list) => list.start),
      [3, 9, 6],
    );
    assert.equal(lists[2].parentElement.parentElement.tagName, 'UL');
  } finally {
    dom.window.close();
  }
});
