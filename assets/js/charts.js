/**
 * Chart rendering utilities - graphs driven by database data
 */

const Charts = {
  // Intensity classes for contribution heatmap (0-4)
  heatmapClasses: ['bg-slate-100 dark:bg-slate-800', 'bg-primary/20', 'bg-primary/40', 'bg-primary/60', 'bg-primary'],

  /**
   * Render releases-over-time bar chart (alternative view)
   * @param {number[]} data - daily release counts
   * @param {string} containerId - DOM element id
   */
  renderReleasesChart(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !data?.length) return;

    const w = 800;
    const h = 200;
    const padding = { top: 20, right: 20, bottom: 30, left: 20 };
    const max = Math.max(...data);
    const chartH = h - padding.top - padding.bottom;
    const chartW = w - padding.left - padding.right;
    const barW = Math.max(2, (chartW / data.length) - 2);

    const bars = data
      .map((val, i) => {
        const x = padding.left + i * (chartW / data.length);
        const barH = max > 0 ? (val / max) * chartH : 0;
        const y = padding.top + chartH - barH;
        return `<rect x="${x}" y="${y}" width="${barW}" height="${barH}" fill="#10b981" rx="2"/>`;
      })
      .join('');

    container.innerHTML = `
      <svg class="w-full h-full" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
        ${bars}
      </svg>
    `;
  },

  /**
   * Render commits-over-time area chart
   * @param {number[]} data - daily commit counts
   * @param {string} containerId - DOM element id
   */
  renderCommitsChart(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !data?.length) return;

    const w = 800;
    const h = 200;
    const padding = { top: 20, right: 20, bottom: 30, left: 20 };
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const chartH = h - padding.top - padding.bottom;
    const chartW = w - padding.left - padding.right;
    const stepX = chartW / (data.length - 1);

    let pathD = '';
    let areaD = '';

    data.forEach((val, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + chartH - ((val - min) / range) * chartH;
      if (i === 0) {
        pathD = `M ${x} ${y}`;
        areaD = `M ${x} ${h - padding.bottom}`;
      } else {
        pathD += ` L ${x} ${y}`;
        areaD += ` L ${x} ${y}`;
      }
    });

    areaD += ` L ${padding.left + (data.length - 1) * stepX} ${h - padding.bottom} Z`;

    container.innerHTML = `
      <svg class="w-full h-full" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
        <defs>
          <linearGradient id="chartGradient" x1="0%" x2="0%" y1="0%" y2="100%">
            <stop offset="0%" stop-color="#135bec" stop-opacity="0.3"></stop>
            <stop offset="100%" stop-color="#135bec" stop-opacity="0"></stop>
          </linearGradient>
        </defs>
        <path d="${areaD}" fill="url(#chartGradient)"></path>
        <path d="${pathD}" fill="none" stroke="#135bec" stroke-linecap="round" stroke-linejoin="round" stroke-width="3"></path>
      </svg>
    `;
  },

  /**
   * Render GitHub-style contribution heatmap
   * @param {number[]} heatmap - 364 values (0-4)
   * @param {string} containerId - DOM element id
   */
  renderContributionHeatmap(heatmap, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !heatmap?.length) return;

    const cols = 52;
    const rows = Math.ceil(heatmap.length / cols);
    const cells = heatmap.slice(0, cols * rows);

    container.innerHTML = cells
      .map((intensity) => {
        const cls = this.heatmapClasses[Math.min(intensity, 4)] || this.heatmapClasses[0];
        return `<div class="contribution-cell ${cls}"></div>`;
      })
      .join('');
  },

  /**
   * Render 6 activity stats as radar/spider chart (game-like)
   * @param {Object} stats - { productivity, quality, collaboration, reliability, initiative, expertise } (0-100)
   * @param {string} containerId - DOM element id
   */
  renderActivityStatsRadar(stats, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !stats) return;

    const labels = {
      productivity: i18n.t('stats.productivity'),
      quality: i18n.t('stats.quality'),
      collaboration: i18n.t('stats.collaboration'),
      reliability: i18n.t('stats.reliability'),
      initiative: i18n.t('stats.initiative'),
      expertise: i18n.t('stats.expertise'),
    };
    const keys = ['productivity', 'quality', 'collaboration', 'reliability', 'initiative', 'expertise'];
    const values = keys.map((k) => Math.min(100, Math.max(0, stats[k] ?? 50)));
    const n = keys.length;
    const padding = 50;
    const size = 180;
    const cx = padding + size / 2;
    const cy = padding + size / 2;
    const maxR = size / 2 - 20;

    const angleStep = (2 * Math.PI) / n;
    const points = values.map((v, i) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const r = (v / 100) * maxR;
      return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), label: labels[keys[i]], value: v };
    });
    const polyPoints = points.map((p) => `${p.x},${p.y}`).join(' ');
    const gridPoints = [25, 50, 75, 100].map((pct) => {
      const r = (pct / 100) * maxR;
      return keys.map((_, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
      }).join(' ');
    });

    const labelOffset = maxR + 18;
    const labelEls = points.map((p, i) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const tx = cx + labelOffset * Math.cos(angle);
      const ty = cy + labelOffset * Math.sin(angle);
      const anchor = tx < cx - 5 ? 'end' : tx > cx + 5 ? 'start' : 'middle';
      return `<text x="${tx}" y="${ty}" text-anchor="${anchor}" dominant-baseline="middle" class="fill-slate-600 dark:fill-slate-400 text-[10px] font-semibold">${p.label}</text>
        <text x="${tx}" y="${ty + 11}" text-anchor="${anchor}" dominant-baseline="middle" class="fill-primary text-[10px] font-bold">${p.value}</text>`;
    }).join('');

    const vbW = padding * 2 + size;
    const vbH = padding * 2 + size;
    container.innerHTML = `
      <svg class="w-full max-w-full" viewBox="0 0 ${vbW} ${vbH}" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="radarFill" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#135bec" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#135bec" stop-opacity="0.05"/>
          </linearGradient>
        </defs>
        ${gridPoints.map((pts, i) => `<polygon points="${pts}" fill="none" stroke="currentColor" stroke-opacity="${0.15 - i * 0.03}" stroke-width="0.5"/>`).join('')}
        ${keys.map((_, i) => {
          const angle = -Math.PI / 2 + i * angleStep;
          const x2 = cx + maxR * Math.cos(angle);
          const y2 = cy + maxR * Math.sin(angle);
          return `<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="currentColor" stroke-opacity="0.2" stroke-width="0.5"/>`;
        }).join('')}
        <polygon points="${polyPoints}" fill="url(#radarFill)" stroke="#135bec" stroke-width="2" stroke-linejoin="round"/>
        ${labelEls}
      </svg>
    `;
  },

  /**
   * Render two employees' activity stats overlapped (comparison)
   * @param {Object} stats1 - first employee stats
   * @param {Object} stats2 - second employee stats
   * @param {string} containerId - DOM element id
   * @param {string} name1 - first employee name
   * @param {string} name2 - second employee name
   */
  renderComparisonRadar(stats1, stats2, containerId, name1, name2) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const labels = {
      productivity: i18n.t('stats.productivity'),
      quality: i18n.t('stats.quality'),
      collaboration: i18n.t('stats.collaboration'),
      reliability: i18n.t('stats.reliability'),
      initiative: i18n.t('stats.initiative'),
      expertise: i18n.t('stats.expertise'),
    };
    const keys = ['productivity', 'quality', 'collaboration', 'reliability', 'initiative', 'expertise'];
    const toValues = (s) => keys.map((k) => Math.min(100, Math.max(0, (s || {})[k] ?? 50)));

    const values1 = toValues(stats1);
    const values2 = toValues(stats2);
    const n = keys.length;
    const padding = 50;
    const size = 200;
    const cx = padding + size / 2;
    const cy = padding + size / 2;
    const maxR = size / 2 - 28;
    const angleStep = (2 * Math.PI) / n;

    const toPoints = (vals) =>
      vals.map((v, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        const r = (v / 100) * maxR;
        return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
      });

    const points1 = toPoints(values1);
    const points2 = toPoints(values2);
    const poly1 = points1.map((p) => `${p.x},${p.y}`).join(' ');
    const poly2 = points2.map((p) => `${p.x},${p.y}`).join(' ');

    const gridPoints = [25, 50, 75, 100].map((pct) => {
      const r = (pct / 100) * maxR;
      return keys.map((_, i) => {
        const angle = -Math.PI / 2 + i * angleStep;
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
      }).join(' ');
    });

    const labelOffset = maxR + 22;
    const labelEls = keys.map((k, i) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const tx = cx + labelOffset * Math.cos(angle);
      const ty = cy + labelOffset * Math.sin(angle);
      const anchor = tx < cx - 5 ? 'end' : tx > cx + 5 ? 'start' : 'middle';
      return `<text x="${tx}" y="${ty}" text-anchor="${anchor}" dominant-baseline="middle" class="fill-slate-600 dark:fill-slate-400 text-[10px] font-semibold">${labels[k]}</text>`;
    }).join('');

    const vbW = padding * 2 + size;
    const vbH = padding * 2 + size + 40;
    const uid = 'cmp-' + Math.random().toString(36).slice(2, 9);
    container.innerHTML = `
      <svg class="w-full max-w-full" viewBox="0 0 ${vbW} ${vbH}" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="${uid}-blue" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#135bec" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#135bec" stop-opacity="0.05"/>
          </linearGradient>
          <linearGradient id="${uid}-emerald" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="#10b981" stop-opacity="0.05"/>
          </linearGradient>
        </defs>
        ${gridPoints.map((pts, i) => `<polygon points="${pts}" fill="none" stroke="currentColor" stroke-opacity="${0.12 - i * 0.02}" stroke-width="0.5"/>`).join('')}
        ${keys.map((_, i) => {
          const angle = -Math.PI / 2 + i * angleStep;
          const x2 = cx + maxR * Math.cos(angle);
          const y2 = cy + maxR * Math.sin(angle);
          return `<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="currentColor" stroke-opacity="0.15" stroke-width="0.5"/>`;
        }).join('')}
        <polygon points="${poly1}" fill="url(#${uid}-blue)" stroke="#135bec" stroke-width="2" stroke-linejoin="round"/>
        <polygon points="${poly2}" fill="url(#${uid}-emerald)" stroke="#10b981" stroke-width="2" stroke-linejoin="round"/>
        ${labelEls}
        <text x="${cx}" y="${size + padding + 32}" text-anchor="middle" font-size="10">
          <tspan fill="#135bec" font-weight="600">● ${(name1 || '').substring(0, 12)}</tspan>
          <tspan dx="14" fill="#10b981" font-weight="600">● ${(name2 || '').substring(0, 12)}</tspan>
        </text>
      </svg>
    `;
  },

  /**
   * Render work-life balance circular gauge
   * @param {number} score - 0-100
   * @param {string} status - e.g. "Healthy"
   * @param {string} containerId - DOM element id
   */
  renderWorkLifeGauge(score, status, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const dashArray = `${score} ${100 - score}`;
    const statusColor = score >= 70 ? 'text-green-500' : score >= 50 ? 'text-amber-500' : 'text-red-500';

    container.innerHTML = `
      <div class="relative size-40 flex items-center justify-center">
        <svg class="size-full -rotate-90" viewBox="0 0 36 36">
          <circle class="stroke-slate-100 dark:stroke-slate-800" cx="18" cy="18" fill="none" r="16" stroke-width="3"></circle>
          <circle class="stroke-primary" cx="18" cy="18" fill="none" r="16" stroke-dasharray="${dashArray}" stroke-linecap="round" stroke-width="3"></circle>
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <span class="text-2xl font-bold text-slate-900 dark:text-slate-100">${score}%</span>
          <span class="text-[10px] uppercase font-bold ${statusColor} tracking-wider">${status}</span>
        </div>
      </div>
    `;
  },
};
