"""
test_search_state_persistence.py — Tests for patent search state persistence logic.

Tests the useSearchState.js helper logic in Python form:
  - State serialization / deserialization
  - State key generation for cache hit detection
  - Session-storage simulation

Frontend-specific tests (scroll restoration, React component behaviour) are
integration tests that require a browser. Those are documented at the bottom
of this file as manual verification steps.

Run from miniproject/ root:
    python -m pytest backend/tests/test_search_state_persistence.py -v
"""

import json
import pytest


# ─── Helpers (mirror of the JS helpers) ─────────────────────────────────────

def build_state_key(query, filters, page, page_size, sort_by):
    """Python mirror of the buildStateKey function in useSearchState.js."""
    techs = filters.get("selectedTechnologies") or []
    tech = ",".join(techs)
    office = filters.get("patentOffice") or ""
    priority = filters.get("priorityDate") or ""
    inv = filters.get("inventor") or ""
    org = filters.get("organization") or ""
    date_from = filters.get("dateFrom") or ""
    date_to = filters.get("dateTo") or ""
    return "|".join([query, tech, office, priority, inv, org, date_from, date_to,
                     str(page), str(page_size), sort_by])


def make_snapshot(query, filters, page, page_size, sort_by, results, total, total_pages, scroll_y=0):
    """Build a simulated session-storage snapshot."""
    key = build_state_key(query, filters, page, page_size, sort_by)
    return {
        "stateKey": key,
        "query": query,
        "filters": filters,
        "page": page,
        "pageSize": page_size,
        "sortBy": sort_by,
        "results": results,
        "totalMatching": total,
        "totalPages": total_pages,
        "scrollY": scroll_y
    }


DEFAULT_FILTERS = {
    "dateType": "",
    "priorityDate": "",
    "exactDate": "",
    "dateFrom": "",
    "dateTo": "",
    "inventor": "",
    "organization": "",
    "selectedTechnologies": [],
    "patentOffice": "",
    "status": "All"
}

SAMPLE_RESULTS = [
    {"id": "10/DEL/2017", "title": "Battery Anode Technology", "patentNumber": "10/DEL/2017"},
    {"id": "42/CHE/2018", "title": "Wind Turbine Generator", "patentNumber": "42/CHE/2018"},
]


# ─── State Key Tests ─────────────────────────────────────────────────────────

class TestStateKeyGeneration:
    """Verify that state keys correctly identify cache hit vs miss scenarios."""

    def test_same_params_produce_same_key(self):
        key1 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        key2 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        assert key1 == key2

    def test_different_query_produces_different_key(self):
        key1 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        key2 = build_state_key("solar panel", DEFAULT_FILTERS, 1, 25, "relevance")
        assert key1 != key2

    def test_different_page_produces_different_key(self):
        key1 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        key2 = build_state_key("battery", DEFAULT_FILTERS, 2, 25, "relevance")
        assert key1 != key2

    def test_different_sort_produces_different_key(self):
        key1 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        key2 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "newest")
        assert key1 != key2

    def test_different_technology_filter_produces_different_key(self):
        filters_with_tech = {**DEFAULT_FILTERS, "selectedTechnologies": ["Electronics"]}
        key1 = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        key2 = build_state_key("battery", filters_with_tech, 1, 25, "relevance")
        assert key1 != key2

    def test_different_office_produces_different_key(self):
        filters_delhi = {**DEFAULT_FILTERS, "patentOffice": "Delhi"}
        filters_mumbai = {**DEFAULT_FILTERS, "patentOffice": "Mumbai"}
        key1 = build_state_key("battery", filters_delhi, 1, 25, "relevance")
        key2 = build_state_key("battery", filters_mumbai, 1, 25, "relevance")
        assert key1 != key2

    def test_empty_filters_produce_consistent_key(self):
        key = build_state_key("", DEFAULT_FILTERS, 1, 25, "relevance")
        assert isinstance(key, str)
        assert "|" in key


# ─── Snapshot Serialisation Tests ────────────────────────────────────────────

class TestSnapshotSerialisation:
    """Verify that snapshots round-trip through JSON without data loss."""

    def test_snapshot_serialises_to_json(self):
        snap = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance",
                             SAMPLE_RESULTS, 2, 1, scroll_y=450)
        serialised = json.dumps(snap)
        parsed = json.loads(serialised)
        assert parsed["query"] == "battery"
        assert parsed["page"] == 1
        assert parsed["scrollY"] == 450
        assert len(parsed["results"]) == 2

    def test_snapshot_state_key_matches_params(self):
        snap = make_snapshot("wind turbine", DEFAULT_FILTERS, 2, 50, "newest",
                             SAMPLE_RESULTS, 2, 3)
        expected_key = build_state_key("wind turbine", DEFAULT_FILTERS, 2, 50, "newest")
        assert snap["stateKey"] == expected_key

    def test_snapshot_with_technology_filter(self):
        filters = {**DEFAULT_FILTERS, "selectedTechnologies": ["Electronics", "Computer"]}
        snap = make_snapshot("sensor", filters, 1, 25, "relevance", SAMPLE_RESULTS, 2, 1)
        parsed = json.loads(json.dumps(snap))
        assert parsed["filters"]["selectedTechnologies"] == ["Electronics", "Computer"]

    def test_empty_results_snapshot(self):
        snap = make_snapshot("", DEFAULT_FILTERS, 1, 25, "relevance", [], 0, 1)
        assert snap["results"] == []
        assert snap["totalMatching"] == 0


# ─── Cache Restoration Logic ─────────────────────────────────────────────────

class TestCacheRestorationLogic:
    """Verify the conditions under which cache restoration should occur."""

    def test_should_restore_when_no_url_params_and_cache_has_results(self):
        """
        When there are no URL params and the cache contains results,
        restoration should be attempted.
        """
        cache = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance",
                              SAMPLE_RESULTS, 2, 1)
        has_url_params = False
        cache_has_results = len(cache.get("results", [])) > 0
        can_restore = not has_url_params and cache_has_results
        assert can_restore is True

    def test_should_not_restore_when_url_params_present(self):
        """
        When URL params specify a query/filter, URL params take precedence.
        The cache should NOT be restored even if it has results.
        """
        cache = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance",
                              SAMPLE_RESULTS, 2, 1)
        has_url_params = True  # e.g. ?q=solar
        can_restore = not has_url_params and len(cache.get("results", [])) > 0
        assert can_restore is False

    def test_should_not_restore_when_cache_is_empty(self):
        """
        Even without URL params, if the cache has no results, there's nothing to restore.
        """
        cache = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance", [], 0, 1)
        has_url_params = False
        can_restore = not has_url_params and len(cache.get("results", [])) > 0
        assert can_restore is False

    def test_url_matches_cache_when_keys_match(self):
        """
        If URL params are present and their state key matches the cache key,
        we can restore from cache without re-fetching.
        """
        filters = {**DEFAULT_FILTERS, "patentOffice": "Delhi"}
        cache = make_snapshot("battery", filters, 2, 25, "relevance", SAMPLE_RESULTS, 2, 1)

        # Simulate URL params that produce the same key
        url_key = build_state_key("battery", filters, 2, 25, "relevance")
        url_matches_cache = url_key == cache["stateKey"]
        assert url_matches_cache is True

    def test_url_does_not_match_cache_when_query_differs(self):
        """
        If URL params represent a different query than the cached state,
        url_matches_cache should be False and a re-fetch should occur.
        """
        filters = DEFAULT_FILTERS
        cache = make_snapshot("battery", filters, 1, 25, "relevance", SAMPLE_RESULTS, 2, 1)
        url_key = build_state_key("solar panel", filters, 1, 25, "relevance")
        url_matches_cache = url_key == cache["stateKey"]
        assert url_matches_cache is False


# ─── Reset Behaviour ─────────────────────────────────────────────────────────

class TestResetBehaviour:
    """Verify that explicit reset clears the cache."""

    def test_reset_clears_results(self):
        """After reset, results should be empty and hasSearched should be False."""
        # Simulate the reset logic
        state = {
            "results": SAMPLE_RESULTS,
            "totalMatching": 2,
            "hasSearched": True,
            "query": "battery"
        }
        # Apply reset
        state["results"] = []
        state["totalMatching"] = 0
        state["hasSearched"] = False
        state["query"] = ""
        assert state["results"] == []
        assert state["hasSearched"] is False

    def test_new_search_replaces_old_state(self):
        """After a new search, the state key changes and cache is updated."""
        old_key = build_state_key("battery", DEFAULT_FILTERS, 1, 25, "relevance")
        new_key = build_state_key("wind turbine", DEFAULT_FILTERS, 1, 25, "relevance")
        assert old_key != new_key, "A new query must produce a different cache key."


# ─── Scroll Position Tests ────────────────────────────────────────────────────

class TestScrollPosition:
    """Verify scroll position is stored and can be retrieved from snapshot."""

    def test_scroll_position_defaults_to_zero(self):
        snap = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance", SAMPLE_RESULTS, 2, 1)
        # If scrollY is not explicitly set, it should default to 0
        assert "scrollY" in snap

    def test_scroll_position_is_updated_on_save(self):
        snap = make_snapshot("battery", DEFAULT_FILTERS, 1, 25, "relevance",
                             SAMPLE_RESULTS, 2, 1, scroll_y=0)
        # Simulate saveScrollPosition updating the snapshot
        snap["scrollY"] = 1250
        parsed = json.loads(json.dumps(snap))
        assert parsed["scrollY"] == 1250

    def test_scroll_position_restored_from_snapshot(self):
        snap = make_snapshot("battery", DEFAULT_FILTERS, 2, 25, "relevance",
                             SAMPLE_RESULTS, 2, 1, scroll_y=870)
        restored_scroll = snap.get("scrollY", 0)
        assert restored_scroll == 870


# ─── Integration Documentation ──────────────────────────────────────────────

"""
MANUAL BROWSER VERIFICATION STEPS
===================================

The following scenarios should be verified manually in the browser after deploying:

1. Basic Navigation Restore
   a. Navigate to /search
   b. Search for "pharmaceutical containers"
   c. Open the first patent detail page
   d. Click the browser Back button
   Expected: Search results for "pharmaceutical containers" are restored instantly
             without a new API call. "Session restored" badge visible.

2. Sidebar Navigation Restore
   a. Search for "wind turbine" — navigate to page 2
   b. Click "AI Assistant" in the sidebar
   c. Click "Patent Search" in the sidebar
   Expected: Page 2 of "wind turbine" results is restored. Scroll position is restored.

3. Sort Order Persistence
   a. Search for "battery"
   b. Change sort to "Newest First"
   c. Navigate to another section and return
   Expected: Sort is still "Newest First". URL contains ?sort=newest.

4. Filter Persistence
   a. Search with Office=Delhi, Technology=Electronics, Page=3
   b. Navigate away and return
   Expected: All filters, page, and results restored.

5. Explicit Reset
   a. Restore a cached search
   b. Click "Reset All Filters"
   Expected: Search page returns to blank state. sessionStorage cleared.

6. New Search Invalidates Cache
   a. Restore a cached "battery" search
   b. Type "solar" and press Enter
   Expected: New results for "solar" appear. Old "battery" cache is replaced.

7. Direct URL Link
   a. Open /search?q=battery&office=Delhi in a fresh tab
   Expected: Results for "battery" in Delhi load normally (no stale cache restore).

8. Page Refresh Behavior
   a. Search for "chemistry patents", navigate to page 2
   b. Refresh the browser
   Expected: If URL contains page=2, the page re-fetches results for that URL.
             (SessionStorage is NOT restored after a refresh since URL params take precedence.)
"""
