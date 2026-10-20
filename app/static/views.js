// User content is always assigned as text, never parsed as HTML.
export function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function renderList(container, issues, select) {
  container.replaceChildren();
  if (!issues.length) container.append(element('p', 'No issues match. Try another search or create an issue.'));
  for (const issue of issues) {
    const button = element('button', undefined, 'issue');
    button.append(element('small', `#${issue.id} · ${issue.status} · ${issue.priority}`), element('strong', issue.title));
    button.addEventListener('click', () => select(issue.id));
    container.append(button);
  }
}

export function renderDetail(container, issue, users, edit, remove) {
  container.replaceChildren(element('small', `ISSUE #${issue.id}`), element('h2', issue.title));
  container.append(element('p', issue.description, 'description'));
  const fields = element('dl');
  const values = {
    Status: issue.status,
    Priority: issue.priority,
    Assignee: users.find(user => user.id === issue.assignee_id)?.name || 'Unknown user',
    Created: new Date(issue.created_at).toLocaleString(),
    Updated: new Date(issue.updated_at).toLocaleString(),
  };
  for (const [name, value] of Object.entries(values)) fields.append(element('dt', name), element('dd', value));
  const editButton = element('button', 'Edit / change status');
  editButton.addEventListener('click', () => edit(issue));
  const deleteButton = element('button', 'Delete issue', 'danger');
  deleteButton.addEventListener('click', () => remove(issue));
  const actions = element('div', undefined, 'actions');
  actions.append(editButton, deleteButton);
  container.append(fields, actions);
}
