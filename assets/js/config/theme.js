/**
 * Theme configuration — design tokens
 * Single source of truth for colors, spacing, typography
 */

const THEME = {
  colors: {
    primary: '#135bec',
    primaryHover: '#0d47c7',
    backgroundLight: '#f6f6f8',
    backgroundDark: '#101622',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
  tailwind: {
    primary: '#135bec',
    backgroundLight: '#f6f6f8',
    backgroundDark: '#101622',
    fontDisplay: ['Inter', 'sans-serif'],
    borderRadius: { DEFAULT: '0.25rem', lg: '0.5rem', xl: '0.75rem', full: '9999px' },
  },
};
