import { atom, map } from 'nanostores';

export const cvTextStore = atom('');
export const candidateLevelStore = atom(null);
export const profileStore = map({
  skills: [],
  target_titles: [],
  years_experience: 0,
  education: 'Profesional',
  search_keywords: [],
});

export const jobsStore = atom([]);
export const savedUrlsStore = atom(new Set());
export const selectedJobStore = atom(null);

export const backendStore = map({
  current: 'ollama',
  label: 'Ollama',
  model: 'llama3.2:3b',
  backends: [],
});

export const automationStore = map({
  running: false,
  status: 'detenida',
  logs: [],
});

export const uiStore = map({
  isSearching: false,
  searchError: null,
});

export function setProfile({ cv_text, candidate_level, cv_profile }) {
  cvTextStore.set(cv_text || '');
  candidateLevelStore.set(candidate_level || null);
  profileStore.set({
    skills: cv_profile?.skills || [],
    target_titles: cv_profile?.target_titles || [],
    years_experience: cv_profile?.years_experience || 0,
    education: cv_profile?.education || 'Profesional',
    search_keywords: cv_profile?.search_keywords || [],
  });
}

export function clearProfile() {
  cvTextStore.set('');
  candidateLevelStore.set(null);
  profileStore.set({
    skills: [],
    target_titles: [],
    years_experience: 0,
    education: 'Profesional',
    search_keywords: [],
  });
}

export function setBackend(data) {
  backendStore.set({
    current: data.current || 'ollama',
    label: data.info?.label || data.current || 'Ollama',
    model: data.info?.model || 'llama3.2:3b',
    backends: data.backends || [],
  });
}

export function setAutomation(data) {
  automationStore.set({
    running: data.running || false,
    status: data.status || 'detenida',
    logs: data.logs || [],
  });
}

export function addSavedUrl(url) {
  const set = new Set(savedUrlsStore.get());
  set.add(url);
  savedUrlsStore.set(set);
}

export function removeSavedUrl(url) {
  const set = new Set(savedUrlsStore.get());
  set.delete(url);
  savedUrlsStore.set(set);
}

export function setSavedUrls(urls) {
  savedUrlsStore.set(new Set(urls));
}

const SELECTED_JOB_KEY = 'jobmatch_selected_job';

export function selectJobForInterview(job) {
  selectedJobStore.set(job);
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.setItem(SELECTED_JOB_KEY, JSON.stringify(job));
    } catch {}
  }
}

export function loadSelectedJobFromStorage() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(SELECTED_JOB_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

export function clearSelectedJobStorage() {
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.removeItem(SELECTED_JOB_KEY);
    } catch {}
  }
}
