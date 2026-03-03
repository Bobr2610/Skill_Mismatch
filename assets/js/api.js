/**
 * API client for DevMetrics backend
 * Fetches employee and dashboard data from Python backend
 * Uses in-memory + localStorage cache to minimize load
 */

const API = {
  baseUrl: (typeof APP_CONFIG !== 'undefined' && APP_CONFIG?.app?.apiBaseUrl) || '/api',
  _mem: {},
  _memTTL: 2 * 60 * 1000,

  _cached(key, fetcher) {
    const cached = typeof Storage !== 'undefined' ? Storage.getCache(key) : null;
    if (cached) return Promise.resolve(cached);
    const mem = this._mem[key];
    if (mem && Date.now() < mem.expires) return Promise.resolve(mem.data);
    return fetcher().then((data) => {
      this._mem[key] = { data, expires: Date.now() + this._memTTL };
      if (typeof Storage !== 'undefined') Storage.setCache(key, data);
      return data;
    });
  },

  async getDashboard() {
    return this._cached('dashboard', async () => {
      const res = await fetch(`${this.baseUrl}/dashboard`);
      if (!res.ok) throw new Error('Failed to fetch dashboard');
      return res.json();
    });
  },

  async getEmployees() {
    return this._cached('employees', async () => {
      const res = await fetch(`${this.baseUrl}/employees`);
      if (!res.ok) throw new Error('Failed to fetch employees');
      return res.json();
    });
  },

  async getEmployee(id) {
    return this._cached(`employee:${id}`, async () => {
      const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error('Failed to fetch employee');
      return res.json();
    });
  },

  invalidateCache() {
    this._mem = {};
    if (typeof Storage !== 'undefined') {
      const s = Storage.get();
      if (s.cache) Storage.set({ cache: {} });
    }
  },

  async createEmployee(data) {
    const res = await fetch(`${this.baseUrl}/employees`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to create employee');
    }
    this.invalidateCache();
    return res.json();
  },

  async updateEmployee(id, data) {
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update employee');
    this.invalidateCache();
    return res.json();
  },

  async deleteEmployee(id) {
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete employee');
    this.invalidateCache();
    return res.json();
  },

  async refreshEmployeeStats(id) {
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}/refresh-stats`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to refresh stats');
    return res.json();
  },

  async getCareerRecommendation(id) {
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}/recommendation`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to get recommendation');
    return res.json();
  },

  async monthlyRecalculate(id, monthlyValue) {
    const body = monthlyValue ? { monthlyValue } : {};
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}/monthly-recalculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error('Failed to recalculate');
    this.invalidateCache();
    return res.json();
  },

  async recalculateAll() {
    const res = await fetch(`${this.baseUrl}/employees/recalculate-all`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to recalculate all');
    this.invalidateCache();
    return res.json();
  },

  async getStatsHistory(id) {
    const res = await fetch(`${this.baseUrl}/employees/${encodeURIComponent(id)}/stats-history`);
    if (!res.ok) throw new Error('Failed to fetch stats history');
    return res.json();
  },

  async getGitHubActivity() {
    const res = await fetch(`${this.baseUrl}/github/activity`);
    if (!res.ok) throw new Error('Failed to fetch GitHub activity');
    return res.json();
  },

  async getGitHubContributors() {
    return this._cached('github-contributors', async () => {
      const res = await fetch(`${this.baseUrl}/github/contributors`);
      if (!res.ok) throw new Error('Failed to fetch GitHub contributors');
      return res.json();
    });
  },

  async getDecayCoefficients() {
    return this._cached('decay-coefficients', async () => {
      const res = await fetch(`${this.baseUrl}/decay-coefficients`);
      if (!res.ok) throw new Error('Failed to fetch coefficients');
      return res.json();
    });
  },
};
