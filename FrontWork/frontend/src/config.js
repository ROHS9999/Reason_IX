// One place for the backend URL. Set VITE_API_URL in .env (or in Vercel) for deployment.
export const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Every browser gets a random id once; the backend keeps a separate set of documents per id,
// so different people never see each other's uploads.
export function sessionId() {
  let id = localStorage.getItem("reasonix_session");
  if (!id) {
    const rand = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}${Math.random().toString(16).slice(2)}`);
    id = rand.replace(/-/g, "");
    localStorage.setItem("reasonix_session", id);
  }
  return id;
}

// fetch() that always sends the session id.
export function apiFetch(path, options = {}) {
  return fetch(`${API}${path}`, {
    ...options,
    headers: { ...(options.headers || {}), "X-Session-Id": sessionId() },
  });
}
