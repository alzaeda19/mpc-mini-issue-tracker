// Controller regression tests use a tiny DOM stand-in; these are not browser tests.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Control {
  constructor() { this.listeners = {}; this.disabled = false; this.value = ''; this.open = false; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  append() {}
  replaceChildren() {}
  reset() {}
  focus() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  dispatch(name) {
    const event = { defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } };
    const result = this.listeners[name]?.(event);
    // Browsers close a dialog on Escape unless its cancel event is prevented.
    if (name === 'cancel' && !event.defaultPrevented) this.close();
    return result;
  }
}

async function controller() {
  const controls = new Map();
  const get = id => {
    if (!controls.has(id)) controls.set(id, new Control());
    return controls.get(id);
  };
  const form = get('form');
  form.elements = Object.fromEntries(['title', 'description', 'status', 'priority', 'assignee_id'].map(name => [name, new Control()]));
  let resolveSave, rejectSave;
  const saved = new Promise((resolve, reject) => { resolveSave = resolve; rejectSave = reject; });
  const issue = { id: 1, title: 'Test', description: 'Details', status: 'Open', priority: 'Medium', assignee_id: 1 };
  const context = {
    document: { getElementById: get }, URLSearchParams, setTimeout, clearTimeout,
    FormData: class { *[Symbol.iterator]() { yield* Object.entries(issue).filter(([key]) => key !== 'id'); } },
    element: () => new Control(), renderList() {}, renderDetail() {}, confirm: () => true,
    request: async (url, options = {}) => {
      if (url === '/users') return [{ id: 1, name: 'Demo' }];
      if (options.method === 'POST') return saved;
      if (url.startsWith('/issues?')) return [];
      return issue;
    },
  };
  const source = fs.readFileSync(path.join(__dirname, '../app/static/app.js'), 'utf8').replace(/^import .*;\n/gm, '');
  vm.runInNewContext(source, context);
  await new Promise(setImmediate); // Complete startup's resolved promises.
  return { get, issue, resolveSave, rejectSave };
}

test('Escape cannot dismiss an issue editor while its save is in flight', async () => {
  const app = await controller();
  app.get('new').dispatch('click');
  const pending = app.get('form').dispatch('submit');
  try {
    app.get('editor').dispatch('cancel');
    assert.equal(app.get('editor').open, true, 'pending save must keep ownership of the open editor');
  } finally {
    app.resolveSave(app.issue);
    await pending;
  }
  assert.equal(app.get('editor').open, false);
  assert.equal(app.get('save').disabled, false);
});

test('A failed save keeps the draft open and restores cancellation', async () => {
  const app = await controller();
  app.get('new').dispatch('click');
  const pending = app.get('form').dispatch('submit');
  app.rejectSave(new Error('Storage unavailable'));
  await pending;
  assert.equal(app.get('editor').open, true);
  assert.equal(app.get('form-error').textContent, 'Storage unavailable');
  assert.equal(app.get('save').disabled, false);
  assert.equal(app.get('cancel').disabled, false);
  app.get('editor').dispatch('cancel');
  assert.equal(app.get('editor').open, false);
});
