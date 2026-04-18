/**
 * Icon registry — Material Symbols mapping
 * Centralized icon definitions for nav, activity types, UI
 */

const ICONS = {
  // Navigation & layout
  nav: {
    logo: 'analytics',
    dashboard: 'dashboard',
    team: 'group',
    repositories: 'source',
    pullRequests: 'account_tree',
    addEmployee: 'person_add',
    comparison: 'compare_arrows',
    settings: 'settings',
    search: 'search',
    notifications: 'notifications',
    chat: 'chat_bubble',
    calendar: 'calendar_today',
    breadcrumb: 'chevron_right',
    close: 'close',
    info: 'info',
  },
  // Theme toggle
  theme: {
    light: 'light_mode',
    dark: 'dark_mode',
  },
  // Activity feed types → { icon, color }
  activity: {
    commit: { icon: 'commit', color: 'emerald' },
    review: { icon: 'rate_review', color: 'blue' },
    merge: { icon: 'merge_type', color: 'amber' },
    deploy: { icon: 'rocket_launch', color: 'primary' },
    fix: { icon: 'bug_report', color: 'red' },
    security: { icon: 'security', color: 'red' },
  },
  // Profile stats
  stats: {
    commits: 'commit',
    review: 'rate_review',
    bugs: 'bug_report',
  },
};
