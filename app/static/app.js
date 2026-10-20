import { request } from './api.js';
import { element, renderList, renderDetail } from './views.js';

const byId = id => document.getElementById(id);
const form = byId('form');
const editor = byId('editor');
let users = [];
let editingId = null;
let saving = false;
let offset = 0;
let listVersion = 0;
let detailVersion = 0;
const pageSize = 20;

function report(error) {
  byId('message').textContent = error.message || 'Unable to reach the server. Please try again.';
}

async function loadIssues() {
  const version = ++listVersion;
  const params = new URLSearchParams({ search: byId('search').value, limit: pageSize, offset });
  if (byId('filter').value) params.set('status', byId('filter').value);
  byId('message').textContent = 'Loading issues…';
  try {
    const issues = await request(`/issues?${params}`);
    if (version !== listVersion) return; // Discard older searches arriving late.
    renderList(byId('issues'), issues, showIssue);
    byId('page').textContent = `Page ${offset / pageSize + 1}`;
    byId('previous').disabled = offset === 0;
    byId('next').disabled = issues.length < pageSize;
    byId('message').textContent = '';
  } catch (error) {
    if (version === listVersion) report(error);
  }
}

async function showIssue(id) {
  const version = ++detailVersion;
  try {
    const issue = await request(`/issues/${id}`);
    if (version === detailVersion) renderDetail(byId('detail'), issue, users, openEditor, deleteIssue);
  } catch (error) { report(error); }
}

function openEditor(issue = null) {
  if (saving) return;
  editingId = issue?.id ?? null;
  form.reset();
  byId('form-title').textContent = issue ? `Edit issue #${issue.id}` : 'New issue';
  byId('form-error').textContent = '';
  if (issue) for (const name of ['title', 'description', 'status', 'priority', 'assignee_id']) form.elements[name].value = issue[name];
  editor.showModal();
  form.elements.title.focus();
}

async function deleteIssue(issue) {
  if (!confirm(`Delete issue #${issue.id}: ${issue.title}? This cannot be undone.`)) return;
  try {
    await request(`/issues/${issue.id}`, { method: 'DELETE' });
    ++detailVersion;
    byId('detail').replaceChildren(element('h2', 'Issue deleted'));
    offset = 0;
    await loadIssues();
  } catch (error) { report(error); }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (saving) return;
  saving = true;
  byId('new').disabled = true;
  const values = Object.fromEntries(new FormData(form));
  values.assignee_id = Number(values.assignee_id);
  byId('save').disabled = true;
  byId('cancel').disabled = true;
  try {
    const issue = await request(editingId ? `/issues/${editingId}` : '/issues', {
      method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(values),
    });
    editor.close();
    offset = 0;
    await loadIssues();
    await showIssue(issue.id);
  } catch (error) { byId('form-error').textContent = error.message; }
  finally {
    saving = false;
    byId('new').disabled = false;
    byId('save').disabled = false;
    byId('cancel').disabled = false;
  }
});

// Escape must not close and reopen the editor while a save owns its state.
editor.addEventListener('cancel', event => { if (saving) event.preventDefault(); });
byId('new').disabled = true;
byId('new').addEventListener('click', () => openEditor());
byId('cancel').addEventListener('click', () => editor.close());
byId('refresh').addEventListener('click', loadIssues);
let searchTimer;
byId('search').addEventListener('input', () => {
  ++listVersion;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { offset = 0; loadIssues(); }, 250);
});
byId('filter').addEventListener('change', () => { offset = 0; loadIssues(); });
byId('previous').addEventListener('click', () => { offset = Math.max(0, offset - pageSize); loadIssues(); });
byId('next').addEventListener('click', () => { offset += pageSize; loadIssues(); });

async function start() {
  try {
    users = await request('/users');
    for (const user of users) {
      const option = element('option', user.name);
      option.value = user.id;
      form.elements.assignee_id.append(option);
    }
    byId('new').disabled = false;
    await loadIssues();
  } catch (error) { report(error); }
}
start();
