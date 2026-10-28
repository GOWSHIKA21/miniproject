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
 * Called just before navigating away to a patent detail page.
 */
export function saveScrollPosition() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.scrollY = window.scrollY;
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
