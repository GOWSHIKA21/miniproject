/**
 * useSearchState — Custom hook for persisting patent search state across navigation.
 *
 * Stores the following in sessionStorage (key: STORAGE_KEY):
 *   query, filters, page, pageSize, sortBy, results, totalMatching, totalPages, scrollY
 *
 * Session storage is chosen (over localStorage) so state is scoped to the current
 * browser tab/session and does not accumulate stale state across visits.
 */

const STORAGE_KEY = 'patentgraph_search_state';

/** Serialise state snapshot to sessionStorage. */
export function saveSearchState(snapshot) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch (e) {
    // Storage may be unavailable in some private-browsing modes — fail silently.
    console.warn('[useSearchState] Could not write to sessionStorage:', e);
  }
}

/** Read the persisted state snapshot. Returns null if absent or corrupt. */
export function loadSearchState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Basic structural validation
    if (typeof parsed !== 'object' || parsed === null) return null;
    return parsed;
  } catch (e) {
    console.warn('[useSearchState] Could not read from sessionStorage:', e);
    return null;
  }
}

/** Clear the persisted search state (called on explicit reset). */
export function clearSearchState() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn('[useSearchState] Could not clear sessionStorage:', e);
  }
}

/**
 * Save the current window scroll position into the persisted snapshot.
 * Called on user scroll or before navigating away to a patent detail or sidebar page.
 */
export function saveScrollPosition(scrollY = null) {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.scrollY = (scrollY !== null && scrollY !== undefined) ? scrollY : window.scrollY;
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
  } catch (e) {
    console.warn('[useSearchState] Could not save scroll position:', e);
  }
}

/**
 * Build a canonical state key from the current search parameters.
 * Used to detect whether URL params represent the same search as the cached state,
 * allowing us to skip re-fetching if they match.
 */
export function buildStateKey({ query, filters, page, pageSize, sortBy }) {
  const tech = (filters?.selectedTechnologies || []).join(',');
  const office = filters?.patentOffice || '';
  const priority = filters?.priorityDate || '';
  const inv = filters?.inventor || '';
  const org = filters?.organization || '';
  const dateFrom = filters?.dateFrom || '';
  const dateTo = filters?.dateTo || '';
  return [query, tech, office, priority, inv, org, dateFrom, dateTo, page, pageSize, sortBy].join('|');
}

/**
 * Synchronize state parameters to URLSearchParams.
 * Omits default/empty values to keep URLs clean and readable.
 */
export function buildSearchParamsFromState({ query, filters, page, pageSize, sortBy }) {
  const p = new URLSearchParams();
  if (query && query.trim()) p.set('q', query.trim());
  
  if (filters?.selectedTechnologies && filters.selectedTechnologies.length > 0) {
    p.set('tech', filters.selectedTechnologies.join(','));
  }
  if (filters?.patentOffice && filters.patentOffice !== 'All' && filters.patentOffice.trim()) {
    p.set('office', filters.patentOffice.trim());
  }
  if (filters?.priorityDate && filters.priorityDate.trim()) {
    p.set('priorityDate', filters.priorityDate.trim());
  }
  if (filters?.exactDate && filters.exactDate.trim()) {
    p.set('exactDate', filters.exactDate.trim());
  }
  if (filters?.dateFrom && filters.dateFrom.trim()) {
    p.set('dateFrom', filters.dateFrom.trim());
  }
  if (filters?.dateTo && filters.dateTo.trim()) {
    p.set('dateTo', filters.dateTo.trim());
  }
  if (filters?.inventor && filters.inventor.trim()) {
    p.set('inventor', filters.inventor.trim());
  }
  if (filters?.organization && filters.organization.trim()) {
    p.set('org', filters.organization.trim());
  }
  if (page && page > 1) {
    p.set('page', String(page));
  }
  if (pageSize && pageSize !== 25) {
    p.set('pageSize', String(pageSize));
  }
  if (sortBy && sortBy !== 'relevance') {
    p.set('sort', sortBy);
  }
  return p;
}

/**
 * Parse URLSearchParams into standard filter object and search state.
 */
export function parseStateFromSearchParams(searchParams, defaultFilters) {
  const q = searchParams.get('q') || '';
  const techRaw = searchParams.get('tech') || '';
  const office = searchParams.get('office') || '';
  const priority = searchParams.get('priorityDate') || '';
  const exact = searchParams.get('exactDate') || '';
  const dateFrom = searchParams.get('dateFrom') || '';
  const dateTo = searchParams.get('dateTo') || '';
  const inv = searchParams.get('inventor') || '';
  const org = searchParams.get('org') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('pageSize') || '25', 10);
  const sortBy = searchParams.get('sort') || 'relevance';

  const selectedTechnologies = techRaw ? techRaw.split(',').map(t => t.trim()).filter(Boolean) : [];

  let dateType = '';
  if (priority) dateType = 'Priority';
  else if (exact) dateType = 'Exact';
  else if (dateFrom || dateTo) dateType = 'Range';

  const filters = {
    ...defaultFilters,
    dateType,
    priorityDate: priority,
    exactDate: exact,
    dateFrom,
    dateTo,
    inventor: inv,
    organization: org,
    selectedTechnologies,
    patentOffice: office || ''
  };

  const hasParams = Boolean(
    q.trim() || selectedTechnologies.length > 0 || office || priority ||
    exact || dateFrom || dateTo || inv || org || (page > 1) || (sortBy !== 'relevance')
  );

  return {
    query: q,
    filters,
    page: Math.max(1, page),
    pageSize: pageSize > 0 ? pageSize : 25,
    sortBy,
    hasParams
  };
}
