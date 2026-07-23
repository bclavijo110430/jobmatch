const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      ...(options.body && !(options.body instanceof FormData) && { 'Content-Type': 'application/json' }),
    },
    ...options,
  });

  let data;
  const text = await res.text();
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!res.ok) {
    const msg = data?.detail || data?.message || `Error ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export const api = {
  health: () => request('/health'),
  getBackends: () => request('/llm/backends'),
  configureBackend: (backend) => request('/llm/configure', {
    method: 'POST',
    body: JSON.stringify({ backend }),
  }),

  getProfile: () => request('/profile'),
  uploadProfile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/profile', {
      method: 'POST',
      body: formData,
    });
  },
  deleteProfile: () => request('/profile', { method: 'DELETE' }),

  search: (params) => request('/search', {
    method: 'POST',
    body: JSON.stringify(params),
  }),

  getSaved: () => request('/jobs/saved'),
  saveJob: (job) => request('/jobs/saved', {
    method: 'POST',
    body: JSON.stringify({ job }),
  }),
  deleteSaved: (id) => request(`/jobs/saved/${id}`, { method: 'DELETE' }),

  getDiscovered: () => request('/jobs/discovered'),
  deleteDiscovered: (id) => request(`/jobs/discovered/${id}`, { method: 'DELETE' }),
  clearDiscovered: () => request('/jobs/discovered', { method: 'DELETE' }),

  startInterview: (job) => request('/interview/start', {
    method: 'POST',
    body: JSON.stringify({ job }),
  }),
  continueInterview: (job, history) => request('/interview/continue', {
    method: 'POST',
    body: JSON.stringify({ job, history }),
  }),

  getAutomationStatus: () => request('/automation/status'),
  startAutomation: (params) => request('/automation/start', {
    method: 'POST',
    body: JSON.stringify(params),
  }),
  stopAutomation: () => request('/automation/stop', { method: 'POST' }),
  resetAutomation: () => request('/automation/reset', { method: 'POST' }),
  testTelegram: (params) => request('/automation/test-telegram', {
    method: 'POST',
    body: JSON.stringify(params),
  }),
  getAutomationLogs: () => request('/automation/logs'),
};

export default api;
