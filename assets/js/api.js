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
};
