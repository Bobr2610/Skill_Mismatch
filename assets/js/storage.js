/**
 * Page memory — localStorage persistence for app state
 * Minimizes re-fetches and preserves user preferences
 */

const Storage = {
  KEY: 'devmetrics',
  TTL: 5 * 60 * 1000, // 5 min cache

  get() {
    try {
      const raw = localStorage.getItem(this.KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  },

  set(data) {
    try {
      const current = this.get();
      localStorage.setItem(this.KEY, JSON.stringify({ ...current, ...data }));
    } catch {}
  },

  getTheme() {
    return this.get().theme ?? null;
  },

  setTheme(theme) {
    this.set({ theme });
  },

  getLang() {
    return this.get().lang ?? null;
  },

  setLang(lang) {
    this.set({ lang });
  },

  getLastProfile() {
    return this.get().lastProfileId ?? null;
  },

  setLastProfile(id) {
    this.set({ lastProfileId: id });
  },

  getComparison() {
    return this.get().comparison ?? { id1: null, id2: null };
  },

  setComparison(id1, id2) {
    this.set({ comparison: { id1, id2 } });
  },

  getCache(key) {
    const cache = this.get().cache ?? {};
    const entry = cache[key];
    if (!entry) return null;
    if (Date.now() > entry.expires) {
      delete cache[key];
      this.set({ cache });
      return null;
    }
    return entry.data;
  },

  setCache(key, data) {
    const cache = this.get().cache ?? {};
    cache[key] = { data, expires: Date.now() + this.TTL };
    this.set({ cache });
  },
};
