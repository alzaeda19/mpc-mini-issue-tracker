// One place to translate HTTP failures into readable messages.
export async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail.map(error => `${error.loc.slice(1).join('.')}: ${error.msg}`).join('; ')
      : detail;
    throw new Error(message || 'Request failed. Please try again.');
  }
  return response.status === 204 ? null : response.json();
}
