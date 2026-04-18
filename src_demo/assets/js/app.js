/**
 * Main application logic
 * Employee Evaluation Platform
 * Restores theme/lang from page memory (localStorage)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Restore theme from memory
  if (typeof Storage !== 'undefined') {
    const savedTheme = Storage.getTheme();
    if (savedTheme === 'dark') document.documentElement.classList.add('dark');
    else if (savedTheme === 'light') document.documentElement.classList.remove('dark');
  }

  // Load components if data-include is used
  document.querySelectorAll('[data-include]').forEach(async (el) => {
    const src = el.getAttribute('data-include');
    try {
      const res = await fetch(src);
      if (res.ok) el.innerHTML = await res.text();
    } catch (err) {
      console.warn('Could not load component:', src, err);
    }
  });

  // Theme toggle — persist to memory
  document.addEventListener('click', (e) => {
    if (e.target.closest('#theme-toggle')) {
      document.documentElement.classList.toggle('dark');
      if (typeof Storage !== 'undefined') {
        Storage.setTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
      }
    }
  });
});
