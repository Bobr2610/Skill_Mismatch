/**
 * Page-specific rendering - fetches data from API and binds to DOM
 */

const Pages = {
  _dashboardData: null,
  _activityShown: 5,

  async init() {
    const path = window.location.pathname;
    try {
      if (path.includes('dashboard')) await this.initDashboard();
      else if (path.includes('profile')) await this.initProfile();
      else if (path.includes('comparison')) await this.initComparison();
    } catch (err) {
      console.error('Failed to load page data:', err);
      this._showError(err.message);
    }
  },

  _showError(msg) {
    const errMsg = msg.includes('fetch') || msg.includes('Failed to fetch')
      ? i18n.t('common.error_backend')
      : msg;
    const containers = ['contributors-tbody', 'recent-activity', 'comparison-content', 'team-list'];
    containers.forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `<p class="text-red-500 dark:text-red-400 py-4 text-sm">${errMsg}</p>`;
    });
    const kpiIds = ['kpi-commits', 'kpi-prs', 'kpi-cycle', 'kpi-deploy'];
    kpiIds.forEach((id) => this._setText(id, '—'));
  },

  async initDashboard() {
    const db = await API.getDashboard();
    if (!db) return;
    this._dashboardData = db;
    this._activityShown = 5;

    const kpis = db.teamKPIs || {};
    this._setText('kpi-commits', (kpis.totalCommits ?? 0).toLocaleString());
    this._setText('kpi-commits-trend', kpis.totalCommitsTrend ?? '');
    this._setText('kpi-prs', kpis.activePRs ?? '—');
    this._setText('kpi-prs-trend', kpis.activePRsTrend ?? '');
    this._setText('kpi-cycle', (kpis.avgCycleTimeDays ?? 0) + ' Days');
    this._setText('kpi-cycle-trend', kpis.avgCycleTimeTrend ?? '');
    this._setText('kpi-deploy', (kpis.deploymentFreq ?? 0) + ' / day');
    this._setText('kpi-deploy-trend', kpis.deploymentFreqTrend ?? '');

    Charts.renderCommitsChart(db.commitsOverTime || [], 'commits-chart');

    const tbody = document.getElementById('contributors-tbody');
    if (tbody && db.employees?.length) {
      const sorted = [...db.employees].sort((a, b) => (b.impactScore || 0) - (a.impactScore || 0)).slice(0, 4);
      tbody.innerHTML = sorted
        .map(
          (e) => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
          <td class="px-6 py-4 flex items-center gap-3">
            <div class="size-8 rounded-full bg-slate-200 dark:bg-slate-700 bg-cover" style="background-image: url('${e.avatar || ''}')"></div>
            <a href="profile.html?id=${e.id}" class="font-semibold text-slate-900 dark:text-white hover:text-primary">${e.name}</a>
          </td>
          <td class="px-6 py-4">${e.commits ?? 0}</td>
          <td class="px-6 py-4">${e.prsActive ?? 0}</td>
          <td class="px-6 py-4">
            <div class="flex items-center gap-2">
              <div class="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div class="bg-primary h-full" style="width: ${e.impactScore ?? 0}%"></div>
              </div>
              <span class="text-xs font-medium">${e.impactScore ?? 0}%</span>
            </div>
          </td>
        </tr>
      `
        )
        .join('');
    }

    this._renderActivity(5);

    const commitsBtn = document.getElementById('chart-btn-commits');
    const releasesBtn = document.getElementById('chart-btn-releases');
    const commitsData = db.commitsOverTime || [];
    const releasesData = commitsData.map((v) => Math.max(0, Math.floor(v * 0.15) + (v % 3)));
    if (commitsBtn) {
      commitsBtn.addEventListener('click', () => {
        Charts.renderCommitsChart(commitsData, 'commits-chart');
        commitsBtn.className = 'px-3 py-1.5 text-xs font-semibold bg-primary text-white rounded-lg';
        if (releasesBtn) releasesBtn.className = 'px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg';
      });
    }
    if (releasesBtn) {
      releasesBtn.addEventListener('click', () => {
        Charts.renderReleasesChart(releasesData, 'commits-chart');
        releasesBtn.className = 'px-3 py-1.5 text-xs font-semibold bg-primary text-white rounded-lg';
        if (commitsBtn) commitsBtn.className = 'px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg';
      });
    }

    const loadMoreBtn = document.getElementById('load-more-activity');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        this._activityShown = Math.min((this._activityShown || 5) + 5, (db.recentActivity || []).length);
        this._renderActivity(this._activityShown);
      });
    }
  },

  _renderActivity(limit) {
    const db = this._dashboardData;
    const activityEl = document.getElementById('recent-activity');
    if (!activityEl || !db?.recentActivity?.length) return;
    const employees = db.employees || [];
    activityEl.innerHTML = db.recentActivity
      .slice(0, limit)
      .map((a) => {
          const emp = employees.find((e) => e.id === a.userId);
          const name = emp?.name || a.userId;
          const avatar = emp?.avatar || `https://ui-avatars.com/api/?name=${String(name).replace(/ /g, '+')}&background=135bec&color=fff`;
          let content = '';
          if (a.type === 'commit') content = `${name} ${i18n.t('activity.committed_to')} <span class="text-primary font-semibold">${a.repo || ''}</span>`;
          else if (a.type === 'review') content = `${name} ${i18n.t('activity.requested_review')}`;
          else if (a.type === 'merge') content = `${name} ${i18n.t('activity.merged_hotfix')}`;
          else if (a.type === 'deploy') content = `${name} ${i18n.t('activity.triggered_deploy')}`;
          else content = name + ' ' + (a.message || '');

          let sub = '';
          if (a.message) sub = `<p class="text-xs text-slate-500 dark:text-slate-400 mt-1 italic">"${a.message}"</p>`;
          else if (a.prNumber) sub = `<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">PR #${a.prNumber}: <span class="underline">${a.prTitle || ''}</span></p>`;
          else if (a.env) sub = `<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Environment: <span class="font-bold">${a.env}</span></p>`;
          else if (a.type === 'merge' && a.message) sub = `<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${a.message}</p>`;

          const actConfig = (typeof ICONS !== 'undefined' && ICONS?.activity?.[a.type]) || { icon: 'commit', color: 'emerald' };
          const iconName = a.icon || actConfig.icon;
          const iconColor = a.iconColor || actConfig.color;
          const iconBg = iconColor === 'primary' ? 'bg-primary' : `bg-${iconColor}-500`;
          return `
          <div class="flex gap-4">
            <div class="relative shrink-0">
              <div class="size-10 rounded-full bg-slate-200 dark:bg-slate-700 bg-cover" style="background-image: url('${avatar}')"></div>
              <div class="absolute -bottom-1 -right-1 size-5 ${iconBg} rounded-full border-2 border-white dark:border-slate-800 flex items-center justify-center">
                <span class="material-symbols-outlined text-[12px] text-white font-bold">${iconName}</span>
              </div>
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-slate-900 dark:text-white">${content}</p>
              ${sub}
              <p class="text-[10px] text-slate-400 mt-1">${a.timeAgo || ''}</p>
            </div>
          </div>
        `;
      })
      .join('');

    const loadMoreBtn = document.getElementById('load-more-activity');
    if (loadMoreBtn) {
      loadMoreBtn.style.display = limit >= db.recentActivity.length ? 'none' : 'block';
    }
  },

  async initProfile() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id') || (typeof Storage !== 'undefined' && Storage.getLastProfile()) || 'alex-rivers';
    if (typeof Storage !== 'undefined') Storage.setLastProfile(id);
    let emp;
    try {
      emp = await API.getEmployee(id);
    } catch {
      const employees = await API.getEmployees();
      emp = employees?.[0] || null;
    }
    if (!emp) return;

    this._setText('profile-name', emp.name);
    this._setText('profile-role', emp.role);
    this._setText('profile-title', emp.title);
    this._setText('profile-location', emp.location);
    this._setText('profile-email', emp.email);
    const avatarEl = document.getElementById('profile-avatar');
    if (avatarEl) avatarEl.style.backgroundImage = `url('${emp.avatar || ''}')`;
    this._setText('breadcrumb-current', emp.name);

    const m = emp.metrics || {};
    this._setText('stat-commits', (m.avgCommitsPerDay ?? 0).toFixed(1));
    this._setText('stat-commits-trend', m.commitsTrend || '');
    this._setText('stat-review', (m.codeReviewParticipation ?? 0) + '%');
    this._setText('stat-review-trend', m.codeReviewTrend || '');
    this._setText('stat-bugs', m.bugsResolved ?? '0');
    this._setText('stat-bugs-trend', m.bugsTrend || '');

    const stats = emp.activityStats || {
      productivity: 50, quality: 50, collaboration: 50,
      reliability: 50, initiative: 50, expertise: 50,
    };
    Charts.renderActivityStatsRadar(stats, 'activity-stats-radar');
    this._setText('stat-prod', (stats.productivity ?? 50) + '/100');
    this._setText('stat-quality', (stats.quality ?? 50) + '/100');
    this._setText('stat-collab', (stats.collaboration ?? 50) + '/100');
    this._setText('stat-reliab', (stats.reliability ?? 50) + '/100');
    this._setText('stat-init', (stats.initiative ?? 50) + '/100');
    this._setText('stat-expert', (stats.expertise ?? 50) + '/100');

    const summary = emp.activitySummary || {};
    const lastTitles = summary.lastCommitTitles || [];
    const commitsEl = document.getElementById('recent-commits');
    if (commitsEl) {
      if (lastTitles.length) {
        commitsEl.innerHTML = lastTitles
          .map(
            (msg) => `
          <div class="group flex items-center gap-4 p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg transition-colors border-b border-slate-100 dark:border-slate-800/50 last:border-0">
            <div class="size-2 rounded-full bg-primary mt-1"></div>
            <div class="flex-1 min-w-0">
              <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold truncate">${msg}</p>
            </div>
          </div>
        `
          )
          .join('');
      } else {
        commitsEl.innerHTML = `<p class="text-slate-500 dark:text-slate-400 text-sm p-4">${i18n.t('profile.no_activity')}</p>`;
      }
    }

    const recBtn = document.getElementById('recommendation-btn');
    const recResult = document.getElementById('recommendation-result');
    const recAction = document.getElementById('recommendation-action');
    const recReason = document.getElementById('recommendation-reason');
    if (recBtn && recResult && recAction && recReason) {
      recBtn.onclick = async () => {
        recBtn.disabled = true;
        recBtn.innerHTML = `<span class="material-symbols-outlined text-lg animate-spin">progress_activity</span> ${i18n.t('rec.analyzing')}`;
        try {
          const res = await API.getCareerRecommendation(id);
          recResult.classList.remove('hidden');
          const action = (res.action || 'keep').toLowerCase();
          const labels = { promote: i18n.t('rec.promote'), demote: i18n.t('rec.demote'), keep: i18n.t('rec.keep') };
          const colors = { promote: 'text-emerald-600 dark:text-emerald-400', demote: 'text-amber-600 dark:text-amber-400', keep: 'text-slate-600 dark:text-slate-400' };
          recAction.textContent = labels[action] || labels.keep;
          recAction.className = 'font-bold text-lg mb-2 ' + (colors[action] || colors.keep);
          recReason.textContent = res.reason || '';
        } catch (e) {
          console.error(e);
          recResult.classList.remove('hidden');
          recAction.textContent = i18n.t('rec.error');
          recAction.className = 'font-bold text-lg mb-2 text-red-500';
          recReason.textContent = i18n.t('rec.error_msg');
        }
        recBtn.disabled = false;
        recBtn.innerHTML = `<span class="material-symbols-outlined text-lg">psychology</span> <span>${i18n.t('profile.get_rec')}</span>`;
      };
    }

    const techEl = document.getElementById('tech-stack');
    if (techEl && emp.techStack?.length) {
      techEl.innerHTML = emp.techStack
        .map(
          (t) => `
        <span class="px-3 py-1 ${t === emp.primaryTech ? 'bg-primary/10 text-primary border border-primary/20' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700'} rounded-lg text-xs font-medium">${t}</span>
      `
        )
        .join('');
    }

    const collabEl = document.getElementById('collaborators');
    if (collabEl && emp.collaborators?.length) {
      let employees = [];
      try {
        employees = await API.getEmployees();
      } catch {}
      collabEl.innerHTML = emp.collaborators
        .map((c) => {
          const cEmp = employees.find((e) => e.id === c.id);
          const avatar = cEmp?.avatar || `https://ui-avatars.com/api/?name=${String(c.name || '').replace(/ /g, '+')}&background=135bec&color=fff`;
          return `
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="size-8 rounded-full bg-slate-200 dark:bg-slate-700 bg-center bg-cover" style="background-image: url('${avatar}')"></div>
              <a href="profile.html?id=${c.id}" class="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-primary">${c.name}</a>
            </div>
            <span class="text-[10px] font-bold text-slate-400">${c.reviews ?? 0} ${i18n.t('common.pr_reviews')}</span>
          </div>
        `;
        })
        .join('');
    }
  },

  async initComparison() {
    const params = new URLSearchParams(window.location.search);
    let id1 = params.get('id1');
    let id2 = params.get('id2');
    if ((!id1 || !id2) && typeof Storage !== 'undefined') {
      const mem = Storage.getComparison();
      if (!id1) id1 = mem.id1;
      if (!id2) id2 = mem.id2;
    }
    const employees = await API.getEmployees();
    if (!employees?.length) return;

    const emp1 = id1 ? employees.find((e) => e.id === id1) : null;
    const emp2 = id2 ? employees.find((e) => e.id === id2) : null;

    const selector1 = document.getElementById('compare-select-1');
    const selector2 = document.getElementById('compare-select-2');

    if (selector1) {
      selector1.innerHTML =
        `<option value="">${i18n.t('comparison.select')}</option>` +
        employees
          .map((e) => `<option value="${e.id}" ${e.id === id1 ? 'selected' : ''}>${e.name} — ${e.title || ''}</option>`)
          .join('');
      selector1.addEventListener('change', () => {
        if (typeof Storage !== 'undefined') Storage.setComparison(selector1.value, selector2?.value);
        this._updateComparisonUrl(selector1.value, selector2?.value);
      });
    }
    if (selector2) {
      selector2.innerHTML =
        `<option value="">${i18n.t('comparison.select')}</option>` +
        employees
          .map((e) => `<option value="${e.id}" ${e.id === id2 ? 'selected' : ''}>${e.name} — ${e.title || ''}</option>`)
          .join('');
      selector2.addEventListener('change', () => {
        if (typeof Storage !== 'undefined') Storage.setComparison(selector1?.value, selector2.value);
        this._updateComparisonUrl(selector1?.value, selector2.value);
      });
    }

    const compareArea = document.getElementById('comparison-content');
    if (!compareArea) return;

    if (!emp1 || !emp2) {
      if (typeof Storage !== 'undefined' && (id1 || id2)) Storage.setComparison(id1 || null, id2 || null);
      compareArea.innerHTML = `
        <div class="col-span-2 text-center py-12 text-slate-500 dark:text-slate-400">
          <span class="material-symbols-outlined text-5xl mb-4 block">compare_arrows</span>
          <p>${i18n.t('comparison.prompt')}</p>
        </div>
      `;
      return;
    }

    if (typeof Storage !== 'undefined') Storage.setComparison(emp1.id, emp2.id);
    const stats1 = emp1.activityStats || { productivity: 50, quality: 50, collaboration: 50, reliability: 50, initiative: 50, expertise: 50 };
    const stats2 = emp2.activityStats || { productivity: 50, quality: 50, collaboration: 50, reliability: 50, initiative: 50, expertise: 50 };

    const metrics = [
      { label: i18n.t('comparison.commits_30d'), key: 'commits', fmt: (v) => v ?? '-' },
      { label: i18n.t('comparison.avg_commits_day'), key: 'metrics.avgCommitsPerDay', fmt: (v) => v?.toFixed(1) ?? '-' },
      { label: i18n.t('comparison.active_prs'), key: 'prsActive', fmt: (v) => v ?? '-' },
      { label: i18n.t('comparison.impact_score'), key: 'impactScore', fmt: (v) => (v != null ? v + '%' : '-') },
      { label: i18n.t('comparison.code_review'), key: 'metrics.codeReviewParticipation', fmt: (v) => (v != null ? v + '%' : '-') },
      { label: i18n.t('comparison.bugs_resolved'), key: 'metrics.bugsResolved', fmt: (v) => v ?? '-' },
      { label: i18n.t('comparison.productivity_ai'), key: 'activityStats.productivity', fmt: (v) => (v != null ? v + '/100' : '-') },
      { label: i18n.t('comparison.quality_ai'), key: 'activityStats.quality', fmt: (v) => (v != null ? v + '/100' : '-') },
      { label: i18n.t('comparison.expertise_ai'), key: 'activityStats.expertise', fmt: (v) => (v != null ? v + '/100' : '-') },
    ];

    const getVal = (obj, path) => path.split('.').reduce((o, k) => o?.[k], obj);

    compareArea.innerHTML = `
      <div class="col-span-2 mb-8">
        <h3 class="text-slate-900 dark:text-slate-100 font-bold mb-4">${i18n.t('comparison.overlapping')}</h3>
        <div id="comparison-radar-inner" class="flex justify-center min-h-[280px]"></div>
      </div>
      <div class="col-span-2 grid grid-cols-3 gap-4 mb-8">
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 text-center">
          <div class="size-16 rounded-full mx-auto mb-2 bg-cover" style="background-image: url('${emp1.avatar || ''}')"></div>
          <h3 class="font-bold text-slate-900 dark:text-slate-100">${emp1.name}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">${emp1.title || ''}</p>
        </div>
        <div class="flex items-center justify-center">
          <span class="material-symbols-outlined text-4xl text-slate-400">compare_arrows</span>
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 text-center">
          <div class="size-16 rounded-full mx-auto mb-2 bg-cover" style="background-image: url('${emp2.avatar || ''}')"></div>
          <h3 class="font-bold text-slate-900 dark:text-slate-100">${emp2.name}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">${emp2.title || ''}</p>
        </div>
      </div>
      <div class="col-span-2 overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-slate-50 dark:bg-slate-800/80 text-xs uppercase text-slate-500 dark:text-slate-400 font-bold">
            <tr><th class="px-4 py-3">${i18n.t('comparison.th_metric')}</th><th class="px-4 py-3">${emp1.name}</th><th class="px-4 py-3">${emp2.name}</th><th class="px-4 py-3">${i18n.t('comparison.th_winner')}</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
            ${metrics
              .map((m) => {
                const v1 = getVal(emp1, m.key);
                const v2 = getVal(emp2, m.key);
                const s1 = m.fmt(v1);
                const s2 = m.fmt(v2);
                let winner = '-';
                if (typeof v1 === 'number' && typeof v2 === 'number') {
                  winner = v1 > v2 ? emp1.name : v2 > v1 ? emp2.name : i18n.t('comparison.tie');
                }
                return `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                  <td class="px-4 py-3 font-medium">${m.label}</td>
                  <td class="px-4 py-3">${s1}</td>
                  <td class="px-4 py-3">${s2}</td>
                  <td class="px-4 py-3 text-primary font-semibold">${winner}</td>
                </tr>
              `;
              })
              .join('')}
          </tbody>
        </table>
      </div>
    `;
    Charts.renderComparisonRadar(stats1, stats2, 'comparison-radar-inner', emp1.name, emp2.name);
  },

  _updateComparisonUrl(id1, id2) {
    const url = new URL(window.location.href);
    if (id1) url.searchParams.set('id1', id1);
    else url.searchParams.delete('id1');
    if (id2) url.searchParams.set('id2', id2);
    else url.searchParams.delete('id2');
    window.location.href = url.toString();
  },

  _setText(id, str) {
    const el = document.getElementById(id);
    if (el) el.textContent = str ?? '';
  },
};
