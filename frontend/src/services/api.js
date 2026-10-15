const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * PatentGraph AI REST API Client
 */
export const api = {
  // Health check
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      return await res.json();
    } catch (err) {
      console.warn('Backend not responding to health check:', err);
      return { status: 'offline' };
    }
  },

  // System and taxonomy stats
  async getStats() {
    try {
      const res = await fetch(`${API_BASE_URL}/stats`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      return null;
    }
  },

  // Hybrid search with metadata filters and server-side pagination
  async search(query = '', filters = {}, page = 1, pageSize = 25, sortBy = 'relevance', method = 'hybrid') {
    try {
      const selectedTechs = filters.selectedTechnologies || [];
      const payload = {
        query: query ? query.trim() : '',
        filters: {
          field_of_invention: selectedTechs.length === 1 ? selectedTechs[0] : (filters.field_of_invention || null),
          fields_of_invention: selectedTechs.length > 0 ? selectedTechs : null,
          ipo_location: filters.patentOffice && filters.patentOffice !== 'All' && filters.patentOffice !== 'All Patent Offices' 
            ? filters.patentOffice 
            : (filters.ipo_location || null),
          inventor: filters.inventor ? filters.inventor.trim() : null,
          organization: filters.organization ? filters.organization.trim() : null,
          application_type: filters.application_type || null,
          date_type: filters.dateType || null,
          priority_date: filters.priorityDate || null,
          exact_date: filters.exactDate || null,
          date_from: filters.dateFrom || null,
          date_to: filters.dateTo || null,
          status: filters.status && filters.status !== 'All' ? filters.status : null
        },
        page: page,
        page_size: pageSize,
        sort_by: sortBy,
        retrieval_method: method
      };

      const res = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`Search error ${res.status}`);
      const data = await res.json();
      const total = data.total_found ?? data.total_matching ?? (data.results ? data.results.length : 0);
      const effectivePage = data.page ?? page;
      const effectivePageSize = data.page_size ?? pageSize;
      const totalPages = data.total_pages ?? Math.ceil(total / effectivePageSize);

      return {
        total: total,
        totalMatching: total,
        page: effectivePage,
        pageSize: effectivePageSize,
        totalPages: Math.max(1, totalPages),
        results: (data.results || []).map(r => ({
          ...r.patent,
          relevanceScore: r.score,
          retrievalMethod: r.retrieval_method,
          matchEvidence: r.match_evidence,
          provenance: r.provenance
        }))
      };
    } catch (err) {
      console.error('Search request failed:', err);
      return null;
    }
  },

  // Individual patent details
  async getPatentById(id) {
    try {
      const encodedId = encodeURIComponent(id);
      const res = await fetch(`${API_BASE_URL}/patents/${encodedId}`);
      if (!res.ok) throw new Error(`Patent fetch error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error(`Failed to fetch patent ${id}:`, err);
      return null;
    }
  },

  // Related patents via graph
  async getRelatedPatents(id, limit = 6) {
    try {
      const encodedId = encodeURIComponent(id);
      const res = await fetch(`${API_BASE_URL}/patents/${encodedId}/related?limit=${limit}`);
      if (!res.ok) return [];
      const data = await res.json();
      return data.related || [];
    } catch (err) {
      console.error(`Failed to fetch related patents for ${id}:`, err);
      return [];
    }
  },

  // Knowledge graph sample for explorer
  async getGraphSample() {
    try {
      const res = await fetch(`${API_BASE_URL}/graph/sample`);
      if (!res.ok) throw new Error(`Graph error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch graph sample:', err);
      return null;
    }
  },

  // Patent-specific knowledge graph
  async getPatentGraph(id) {
    try {
      const encodedId = encodeURIComponent(id);
      const res = await fetch(`${API_BASE_URL}/graph/patent/${encodedId}`);
      if (!res.ok) throw new Error(`Patent graph error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error(`Failed to fetch graph for patent ${id}:`, err);
      return null;
    }
  },

  // RAG Chat QA
  async askQuestion(query, history = []) {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, history })
      });
      if (!res.ok) throw new Error(`Chat error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error('RAG question answering failed:', err);
      return null;
    }
  }
};
