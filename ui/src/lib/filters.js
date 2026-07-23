const LEVELS = ['Ninguno', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function filterByKeyword(jobs, keyword) {
  if (!keyword) return jobs;
  const kw = keyword.toLowerCase();
  return jobs.filter((j) =>
    (j.title || '').toLowerCase().includes(kw) ||
    (j.description_short || '').toLowerCase().includes(kw) ||
    (j.company || '').toLowerCase().includes(kw)
  );
}

export function filterByModality(jobs, modality) {
  if (!modality || modality === 'Todas') return jobs;
  const modalities = modality.split(',').map((m) => m.trim().toLowerCase());
  return jobs.filter((j) => modalities.includes((j.modality || '').toLowerCase()));
}

export function filterByLocation(jobs, locations) {
  if (!locations || locations.length === 0) return jobs;
  const locs = locations.map((l) => l.toLowerCase().trim()).filter(Boolean);
  return jobs.filter((j) =>
    locs.some((loc) => (j.location || '').toLowerCase().includes(loc))
  );
}

export function filterBySalaryMin(jobs, minSalary) {
  if (!minSalary || minSalary <= 0) return jobs;
  return jobs.filter((j) => parseSalaryMin(j.salary) >= minSalary);
}

function parseSalaryMin(salary) {
  if (!salary || salary === 'No disponible') return 0;
  const cleaned = salary.replace(/,/g, '');
  const matches = cleaned.match(/[\d.]+/g);
  if (!matches) return 0;
  let raw = matches[0];
  if ((raw.match(/\./g) || []).length > 1) raw = raw.replace(/\./g, '');
  const val = parseFloat(raw);
  return Number.isNaN(val) ? 0 : val;
}

export function filterByEnglishLevel(jobs, levels) {
  if (!levels || levels.length === 0) return jobs;
  const groups = {
    'A1-A2': ['A1', 'A2'],
    'B1-B2': ['B1', 'B2'],
    'C1-C2': ['C1', 'C2'],
  };
  const expanded = new Set();
  for (const lvl of levels) {
    if (groups[lvl]) {
      groups[lvl].forEach((l) => expanded.add(l));
    } else {
      expanded.add(lvl);
    }
  }
  return jobs.filter((j) => expanded.has(j.english_level || 'Ninguno'));
}

export function filterByCompanies(jobs, companies) {
  if (!companies || companies.length === 0) return jobs;
  const comps = companies.map((c) => c.toLowerCase().trim()).filter(Boolean);
  return jobs.filter((j) =>
    comps.some((c) => (j.company || '').toLowerCase().includes(c))
  );
}

export function filterByExperience(jobs, maxYears) {
  if (maxYears === undefined || maxYears === null || maxYears <= 0) return jobs;
  return jobs.filter((j) => {
    const text = `${j.description_short || ''} ${j.title || ''}`.toLowerCase();
    const matches = text.match(/(\d+)\+?\s*(?:años|years)/);
    if (!matches) return true;
    const years = parseInt(matches[1], 10);
    return Number.isNaN(years) ? true : years <= maxYears;
  });
}

export function addMatchFlag(jobs, candidateLevel) {
  const candIdx = LEVELS.indexOf(candidateLevel || 'Ninguno');
  return jobs.map((j) => {
    const req = LEVELS.includes(j.english_level) ? j.english_level : 'Ninguno';
    const reqIdx = LEVELS.indexOf(req);
    return { ...j, english_match: candIdx >= reqIdx };
  });
}

export function applyFilters(jobs, filters) {
  let result = [...jobs];
  result = filterByKeyword(result, filters.keyword);
  result = filterByModality(result, filters.modality);
  result = filterByLocation(result, filters.locations);
  result = filterByEnglishLevel(result, filters.englishLevels);
  result = filterByCompanies(result, filters.companies);
  result = filterBySalaryMin(result, filters.minSalary);
  result = filterByExperience(result, filters.maxExperience);
  return result;
}

export function sortByDate(jobs) {
  return [...jobs].sort((a, b) => {
    const da = a.created_at && a.created_at !== 'Fecha desconocida' ? a.created_at : '0000-00-00';
    const db = b.created_at && b.created_at !== 'Fecha desconocida' ? b.created_at : '0000-00-00';
    return db.localeCompare(da);
  });
}

export function getUniqueLocations(jobs) {
  const set = new Set();
  for (const j of jobs) {
    const loc = (j.location || '').split(',')[0].trim();
    if (loc) set.add(loc);
  }
  return Array.from(set).sort();
}

export function getUniqueCompanies(jobs) {
  const set = new Set();
  for (const j of jobs) {
    const c = (j.company || '').trim();
    if (c && c !== 'No disponible') set.add(c);
  }
  return Array.from(set).sort();
}
