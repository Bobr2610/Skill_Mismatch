/**
 * Page-specific rendering - fetches data from API and binds to DOM
 */

// Map employee IDs → GitHub logins (FIIT team: Bobr2610/FIIT)
const GITHUB_ACCOUNT_MAP = {
  'belyanskiy-kirill': 'KirillBelianskiy',
  'salmanov-eldar': 'EldarSalmanow',
  'sedov-mikhail': 'Bobr2610',
};
const GITHUB_LOGIN_TO_EMPLOYEE = Object.fromEntries(
  Object.entries(GITHUB_ACCOUNT_MAP).map(([eid, login]) => [String(login).toLowerCase(), eid]),
);

const Pages = {
  _dashboardData: null,
  _activityShown: 5,
  _ghContributors: null,

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

    // Prefer GitHub activity when available (real commits)
    try {
      const ghActivity = await API.getGitHubActivity();
      if (ghActivity?.length) this._dashboardData.recentActivity = ghActivity;
    } catch {}

    const kpis = db.teamKPIs || {};
    const fmtNum = (v) => (v != null && v !== '' ? Number(v).toLocaleString() : '—');
    this._setText('kpi-commits', fmtNum(kpis.totalCommits));
    this._setText('kpi-commits-trend', kpis.totalCommitsTrend ?? '');
    this._setText('kpi-prs', fmtNum(kpis.activePRs));
    this._setText('kpi-prs-trend', kpis.activePRsTrend ?? '');
    this._setText('kpi-cycle', kpis.avgCycleTimeDays != null ? (kpis.avgCycleTimeDays + ' Days') : '—');
    this._setText('kpi-cycle-trend', kpis.avgCycleTimeTrend ?? '');
    this._setText('kpi-deploy', kpis.deploymentFreq != null ? (kpis.deploymentFreq + ' / day') : '—');
    this._setText('kpi-deploy-trend', kpis.deploymentFreqTrend ?? '');

    // Try loading the GitHub-style contributors chart; fall back to simple area chart
    let ghContributors = this._ghContributors;
    if (!ghContributors) {
      try {
        ghContributors = await API.getGitHubContributors();
        this._ghContributors = ghContributors || null;
      } catch {
        ghContributors = null;
      }
    }

    if (ghContributors?.length) {
      Charts.renderContributorsChart(ghContributors, 'commits-chart', 'chart-dates');
      const chartTitle = document.querySelector('[data-i18n="dashboard.commits_chart"]');
      const chartDesc = document.querySelector('[data-i18n="dashboard.chart_desc"]');
      if (chartTitle) chartTitle.textContent = i18n.t('dashboard.gh_activity');
      if (chartDesc) chartDesc.textContent = i18n.t('dashboard.gh_activity_desc');
    } else {
      Charts.renderCommitsChart(db.commitsOverTime || [], 'commits-chart');
    }

    const tbody = document.getElementById('contributors-tbody');
    if (tbody) {
      if (ghContributors?.length) {
        const topGh = ghContributors.slice(0, 6);
        const maxCommits = topGh[0]?.total || 1;
        tbody.innerHTML = topGh
          .map((c) => {
            const pct = Math.round(((c.total || 0) / maxCommits) * 100);
            return `
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <td class="px-6 py-4 flex items-center gap-3">
              <img src="${c.avatar || ''}" alt="${c.login}" class="size-8 rounded-full bg-slate-200 dark:bg-slate-700" onerror="this.style.display='none'">
              <a href="https://github.com/${c.login}" target="_blank" rel="noopener" class="font-semibold text-slate-900 dark:text-white hover:text-primary">${c.login}</a>
            </td>
            <td class="px-6 py-4">${(c.total ?? 0).toLocaleString()}</td>
            <td class="px-6 py-4">—</td>
            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <div class="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div class="bg-primary h-full" style="width: ${pct}%"></div>
                </div>
                <span class="text-xs font-medium">${pct}%</span>
              </div>
            </td>
          </tr>`;
          })
          .join('');
      } else if (db.employees?.length) {
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
          </tr>`
          )
          .join('');
      }
    }

    this._renderActivity(5);

    const commitsBtn = document.getElementById('chart-btn-commits');
    const releasesBtn = document.getElementById('chart-btn-releases');
    const commitsData = db.commitsOverTime || [];
    const releasesData = commitsData.map((v) => Math.max(0, Math.floor(v * 0.15) + (v % 3)));
    const activeBtn = 'px-3 py-1.5 text-xs font-semibold bg-primary text-white rounded-lg';
    const inactiveBtn = 'px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg';
    if (commitsBtn) {
      commitsBtn.addEventListener('click', () => {
        if (ghContributors?.length) {
          Charts.renderContributorsChart(ghContributors, 'commits-chart', 'chart-dates');
        } else {
          Charts.renderCommitsChart(commitsData, 'commits-chart');
        }
        commitsBtn.className = activeBtn;
        if (releasesBtn) releasesBtn.className = inactiveBtn;
      });
    }
    if (releasesBtn) {
      releasesBtn.addEventListener('click', () => {
        Charts.renderReleasesChart(releasesData, 'commits-chart');
        releasesBtn.className = activeBtn;
        if (commitsBtn) commitsBtn.className = inactiveBtn;
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
    const loadMoreBtn = document.getElementById('load-more-activity');
    if (!activityEl) return;
    if (!db?.recentActivity?.length) {
      activityEl.innerHTML = `<p class="text-slate-500 dark:text-slate-400 text-sm py-4">${i18n.t('dashboard.no_activity')}</p>`;
      if (loadMoreBtn) loadMoreBtn.style.display = 'none';
      return;
    }
    const employees = db.employees || [];
    activityEl.innerHTML = db.recentActivity
      .slice(0, limit)
      .map((a) => {
          const empById = employees.find((e) => e.id === a.userId);
          const empByLogin = a.userId && GITHUB_LOGIN_TO_EMPLOYEE[String(a.userId).toLowerCase()]
            ? employees.find((e) => e.id === GITHUB_LOGIN_TO_EMPLOYEE[a.userId.toLowerCase()])
            : null;
          const emp = empById || empByLogin;
          const name = emp?.name || a.userId;
          let avatar = emp?.avatar || `https://ui-avatars.com/api/?name=${String(name).replace(/ /g, '+')}&background=135bec&color=fff`;
          const gh = this._findGithubForEmployee(emp?.id || a.userId);
          if (gh?.avatar) avatar = gh.avatar;
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

    if (loadMoreBtn) {
      loadMoreBtn.style.display = limit >= db.recentActivity.length ? 'none' : 'block';
    }
  },

  async initProfile() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id') || (typeof Storage !== 'undefined' && Storage.getLastProfile()) || 'belyanskiy-kirill';
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
    // Prefer GitHub avatar when linked, but keep local name/title
    if (!this._ghContributors) {
      try {
        this._ghContributors = await API.getGitHubContributors();
      } catch {
        this._ghContributors = null;
      }
    }
    const avatarEl = document.getElementById('profile-avatar');
    const ghForEmp = this._findGithubForEmployee(emp.id);
    const avatarUrl = (ghForEmp && ghForEmp.avatar) || emp.avatar || '';
    if (avatarEl) avatarEl.style.backgroundImage = `url('${avatarUrl}')`;
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
    const pendingCommits = summary.pendingCommits || [];
    const commitsEl = document.getElementById('recent-commits');
    if (commitsEl) {
      if (lastTitles.length) {
        commitsEl.innerHTML = lastTitles
          .map(
            (msg) => {
              const isPending = pendingCommits.includes(msg);
              const badge = isPending
                ? `<span class="px-1.5 py-0.5 text-[9px] font-bold bg-blue-500/10 text-blue-500 rounded">${i18n.t('profile.commit_pending')}</span>`
                : `<span class="px-1.5 py-0.5 text-[9px] font-bold bg-emerald-500/10 text-emerald-500 rounded">✓</span>`;
              return `
          <div class="group flex items-center gap-4 p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg transition-colors border-b border-slate-100 dark:border-slate-800/50 last:border-0" data-commit-msg="${msg.replace(/"/g, '&quot;')}">
            <div class="size-2 rounded-full ${isPending ? 'bg-blue-500 animate-pulse' : 'bg-primary'} mt-1"></div>
            <div class="flex-1 min-w-0">
              <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold truncate">${msg}</p>
            </div>
            ${badge}
          </div>`;
            }
          )
          .join('');
      } else {
        commitsEl.innerHTML = `<p class="text-slate-500 dark:text-slate-400 text-sm p-4">${i18n.t('profile.no_activity')}</p>`;
      }
    }

    const coefficients = { Junior: 0.4, Mid: 0.5, Senior: 0.6, Staff: 0.7, Lead: 0.75 };
    try {
      const fetchedCoeffs = await API.getDecayCoefficients();
      Object.assign(coefficients, fetchedCoeffs);
    } catch {}
    const empRole = (emp.role || 'Mid').trim();
    const matchedRole = Object.keys(coefficients).find(k => empRole.toLowerCase().includes(k.toLowerCase())) || 'Mid';
    const K = coefficients[matchedRole] || 0.5;
    this._setText('green-coefficient', `K(${matchedRole}) = ${K}`);
    this._setText('decay-coefficient', `K(${matchedRole}) = ${K}`);
    if (emp.lastRecalculation) {
      this._setText('green-last-recalc', `${i18n.t('profile.last_recalc')}: ${emp.lastRecalculation}`);
    }

    this._initCommitContribution(id, K);
    this._initMonthlyDecay(id, K, matchedRole);

    const greenBtn = document.getElementById('green-recalc-btn');
    const greenResult = document.getElementById('green-result');
    const greenTitle = document.getElementById('green-result-title');
    const greenDetails = document.getElementById('green-result-details');
    if (greenBtn && greenResult && greenTitle && greenDetails) {
      greenBtn.onclick = async () => {
        greenBtn.disabled = true;
        greenBtn.innerHTML = `<span class="material-symbols-outlined text-lg animate-spin">progress_activity</span> ${i18n.t('profile.green_computing')}`;
        try {
          const res = await API.monthlyRecalculate(id);
          greenResult.classList.remove('hidden');
          greenTitle.textContent = `${i18n.t('profile.green_done')} (K=${res.coefficient})`;
          const statLabels = {
            productivity: i18n.t('stats.productivity'),
            quality: i18n.t('stats.quality'),
            collaboration: i18n.t('stats.collaboration'),
            reliability: i18n.t('stats.reliability'),
            initiative: i18n.t('stats.initiative'),
            expertise: i18n.t('stats.expertise'),
          };
          greenDetails.innerHTML = Object.keys(statLabels).map(k => {
            const before = res.statsBefore?.[k] ?? '?';
            const mv = res.monthlyValue?.[k] ?? '?';
            const after = res.activityStats?.[k] ?? '?';
            const diff = after - before;
            const diffColor = diff > 0 ? 'text-emerald-500' : diff < 0 ? 'text-red-500' : 'text-slate-400';
            const diffStr = diff > 0 ? `+${diff}` : `${diff}`;
            return `<div class="flex justify-between"><span>${statLabels[k]}</span><span>${before} × ${res.coefficient} + ${mv} = <span class="font-bold">${after}</span> <span class="${diffColor}">(${diffStr})</span></span></div>`;
          }).join('');

          Charts.renderActivityStatsRadar(res.activityStats, 'activity-stats-radar');
          for (const [k, elId] of [['productivity','stat-prod'],['quality','stat-quality'],['collaboration','stat-collab'],['reliability','stat-reliab'],['initiative','stat-init'],['expertise','stat-expert']]) {
            this._setText(elId, (res.activityStats[k] ?? 50) + '/100');
          }
          this._setText('green-last-recalc', `${i18n.t('profile.last_recalc')}: ${res.month}`);

          this._loadStatsHistory(id);
        } catch (e) {
          console.error(e);
          greenResult.classList.remove('hidden');
          greenTitle.textContent = i18n.t('rec.error');
          greenTitle.className = 'font-bold text-sm text-red-500 mb-2';
          greenDetails.textContent = e.message;
        }
        greenBtn.disabled = false;
        greenBtn.innerHTML = `<span class="material-symbols-outlined text-lg">autorenew</span> <span>${i18n.t('profile.green_recalc')}</span>`;
      };
    }

    this._loadStatsHistory(id);

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
          let avatar = cEmp?.avatar || `https://ui-avatars.com/api/?name=${String(c.name || '').replace(/ /g, '+')}&background=135bec&color=fff`;
          const gh = this._findGithubForEmployee(c.id);
          if (gh?.avatar) avatar = gh.avatar;
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

    if (pendingCommits.length) {
      this._autoAnalyzePending(id, pendingCommits);
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

    // Enrich with GitHub avatars and commits
    let ghContributors = this._ghContributors;
    if (!ghContributors) {
      try {
        ghContributors = await API.getGitHubContributors();
        this._ghContributors = ghContributors;
      } catch {
        ghContributors = [];
      }
    }
    const gh1 = this._findGithubForEmployee(emp1.id);
    const gh2 = this._findGithubForEmployee(emp2.id);
    const emp1Avatar = gh1?.avatar || emp1.avatar || '';
    const emp2Avatar = gh2?.avatar || emp2.avatar || '';
    const emp1WithGh = { ...emp1, avatar: emp1Avatar, commits: gh1?.total ?? emp1.commits };
    const emp2WithGh = { ...emp2, avatar: emp2Avatar, commits: gh2?.total ?? emp2.commits };

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
          <div class="size-16 rounded-full mx-auto mb-2 bg-cover" style="background-image: url('${emp1Avatar}')"></div>
          <h3 class="font-bold text-slate-900 dark:text-slate-100">${emp1.name}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">${emp1.title || ''}</p>
        </div>
        <div class="flex items-center justify-center">
          <span class="material-symbols-outlined text-4xl text-slate-400">compare_arrows</span>
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-800 text-center">
          <div class="size-16 rounded-full mx-auto mb-2 bg-cover" style="background-image: url('${emp2Avatar}')"></div>
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
                const v1 = getVal(emp1WithGh, m.key);
                const v2 = getVal(emp2WithGh, m.key);
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

  async _autoAnalyzePending(employeeId, pendingCommits) {
    const resultEl = document.getElementById('commit-result');
    const titleEl = document.getElementById('commit-result-title');
    const detailsEl = document.getElementById('commit-result-details');
    const btn = document.getElementById('commit-analyze-btn');
    if (!resultEl || !titleEl || !detailsEl) return;

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg animate-spin">progress_activity</span> ${i18n.t('profile.commit_auto')}`;
    }
    resultEl.classList.remove('hidden');
    titleEl.textContent = `${i18n.t('profile.commit_auto')} (${pendingCommits.length})...`;
    detailsEl.innerHTML = '';

    const statLabels = {
      productivity: i18n.t('stats.productivity'),
      quality: i18n.t('stats.quality'),
      collaboration: i18n.t('stats.collaboration'),
      reliability: i18n.t('stats.reliability'),
      initiative: i18n.t('stats.initiative'),
      expertise: i18n.t('stats.expertise'),
    };

    for (const msg of pendingCommits) {
      try {
        const res = await API.commitContribution(employeeId, msg);
        const incLines = Object.keys(statLabels)
          .filter(k => (res.increments?.[k] ?? 0) > 0)
          .map(k => `<span class="text-blue-500">+${res.increments[k]} ${statLabels[k]}</span>`)
          .join(', ') || '<span class="text-slate-400">+0</span>';
        detailsEl.innerHTML += `<div class="p-2 rounded bg-slate-50 dark:bg-slate-800/50 mb-1"><span class="font-semibold text-slate-700 dark:text-slate-300">${msg.substring(0, 50)}${msg.length > 50 ? '…' : ''}</span><br>${incLines}</div>`;

        Charts.renderActivityStatsRadar(res.activityStats, 'activity-stats-radar');
        for (const [k, elId] of [['productivity','stat-prod'],['quality','stat-quality'],['collaboration','stat-collab'],['reliability','stat-reliab'],['initiative','stat-init'],['expertise','stat-expert']]) {
          this._setText(elId, (res.activityStats[k] ?? 50) + '/100');
        }

        const commitEl = document.querySelector(`[data-commit-msg="${msg.replace(/"/g, '&quot;')}"]`);
        if (commitEl) {
          const dot = commitEl.querySelector('.animate-pulse');
          if (dot) { dot.classList.remove('animate-pulse', 'bg-blue-500'); dot.classList.add('bg-primary'); }
          const badge = commitEl.querySelector('.bg-blue-500\\/10');
          if (badge) { badge.className = 'px-1.5 py-0.5 text-[9px] font-bold bg-emerald-500/10 text-emerald-500 rounded'; badge.textContent = '✓'; }
        }
      } catch (e) {
        detailsEl.innerHTML += `<div class="p-2 rounded bg-red-50 dark:bg-red-900/20 mb-1 text-red-500">${msg.substring(0, 50)}: ${e.message}</div>`;
      }
    }

    titleEl.textContent = `${i18n.t('profile.commit_auto_done')} (${pendingCommits.length})`;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg">commit</span> <span>${i18n.t('profile.commit_analyze')}</span>`;
    }
  },

  _initCommitContribution(employeeId, K) {
    const btn = document.getElementById('commit-analyze-btn');
    const input = document.getElementById('commit-message-input');
    const result = document.getElementById('commit-result');
    const title = document.getElementById('commit-result-title');
    const details = document.getElementById('commit-result-details');
    if (!btn || !input) return;

    btn.onclick = async () => {
      const msg = input.value.trim();
      if (!msg) return;
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg animate-spin">progress_activity</span> ${i18n.t('profile.commit_analyzing')}`;
      try {
        const res = await API.commitContribution(employeeId, msg);
        result.classList.remove('hidden');
        title.textContent = i18n.t('profile.commit_done');
        const statLabels = {
          productivity: i18n.t('stats.productivity'),
          quality: i18n.t('stats.quality'),
          collaboration: i18n.t('stats.collaboration'),
          reliability: i18n.t('stats.reliability'),
          initiative: i18n.t('stats.initiative'),
          expertise: i18n.t('stats.expertise'),
        };
        details.innerHTML = Object.keys(statLabels).map(k => {
          const inc = res.increments?.[k] ?? 0;
          const before = res.statsBefore?.[k] ?? '?';
          const after = res.activityStats?.[k] ?? '?';
          if (inc === 0) return `<div class="flex justify-between"><span>${statLabels[k]}</span><span class="text-slate-400">+0</span></div>`;
          return `<div class="flex justify-between"><span>${statLabels[k]}</span><span class="text-blue-500 font-bold">${before} + ${inc} = ${after}</span></div>`;
        }).join('');

        Charts.renderActivityStatsRadar(res.activityStats, 'activity-stats-radar');
        for (const [k, elId] of [['productivity','stat-prod'],['quality','stat-quality'],['collaboration','stat-collab'],['reliability','stat-reliab'],['initiative','stat-init'],['expertise','stat-expert']]) {
          this._setText(elId, (res.activityStats[k] ?? 50) + '/100');
        }
        input.value = '';
      } catch (e) {
        console.error(e);
        result.classList.remove('hidden');
        title.textContent = i18n.t('rec.error');
        title.className = 'font-bold text-sm text-red-500 mb-2';
        details.textContent = e.message;
      }
      btn.disabled = false;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg">commit</span> <span>${i18n.t('profile.commit_analyze')}</span>`;
    };
  },

  _initMonthlyDecay(employeeId, K, matchedRole) {
    const btn = document.getElementById('decay-btn');
    const result = document.getElementById('decay-result');
    const title = document.getElementById('decay-result-title');
    const details = document.getElementById('decay-result-details');
    if (!btn) return;

    btn.onclick = async () => {
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg animate-spin">progress_activity</span> ${i18n.t('profile.decay_applying')}`;
      try {
        const res = await API.monthlyDecay(employeeId);
        result.classList.remove('hidden');
        title.textContent = `${i18n.t('profile.decay_done')} (K=${res.coefficient})`;
        const statLabels = {
          productivity: i18n.t('stats.productivity'),
          quality: i18n.t('stats.quality'),
          collaboration: i18n.t('stats.collaboration'),
          reliability: i18n.t('stats.reliability'),
          initiative: i18n.t('stats.initiative'),
          expertise: i18n.t('stats.expertise'),
        };
        details.innerHTML = Object.keys(statLabels).map(k => {
          const before = res.statsBefore?.[k] ?? '?';
          const after = res.activityStats?.[k] ?? '?';
          const diff = after - before;
          const diffColor = diff < 0 ? 'text-amber-500' : 'text-slate-400';
          const diffStr = diff < 0 ? `${diff}` : `${diff}`;
          return `<div class="flex justify-between"><span>${statLabels[k]}</span><span>${before} × ${res.coefficient} = <span class="font-bold">${after}</span> <span class="${diffColor}">(${diffStr})</span></span></div>`;
        }).join('');

        Charts.renderActivityStatsRadar(res.activityStats, 'activity-stats-radar');
        for (const [k, elId] of [['productivity','stat-prod'],['quality','stat-quality'],['collaboration','stat-collab'],['reliability','stat-reliab'],['initiative','stat-init'],['expertise','stat-expert']]) {
          this._setText(elId, (res.activityStats[k] ?? 50) + '/100');
        }
        this._setText('green-last-recalc', `${i18n.t('profile.last_recalc')}: ${res.month}`);
        this._loadStatsHistory(employeeId);
      } catch (e) {
        console.error(e);
        result.classList.remove('hidden');
        title.textContent = i18n.t('rec.error');
        title.className = 'font-bold text-sm text-red-500 mb-2';
        details.textContent = e.message;
      }
      btn.disabled = false;
      btn.innerHTML = `<span class="material-symbols-outlined text-lg">trending_down</span> <span>${i18n.t('profile.decay_apply')}</span>`;
    };
  },

  async _loadStatsHistory(employeeId) {
    const el = document.getElementById('stats-history');
    if (!el) return;
    try {
      const history = await API.getStatsHistory(employeeId);
      if (!history?.length) {
        el.innerHTML = `<p class="text-slate-500 dark:text-slate-400 text-xs">${i18n.t('profile.no_history')}</p>`;
        return;
      }
      el.innerHTML = history.map(h => {
        const after = h.statsAfter || {};
        const avg = Object.values(after).length
          ? Math.round(Object.values(after).reduce((a, b) => a + b, 0) / Object.values(after).length)
          : 0;
        return `
          <div class="p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
            <div class="flex justify-between items-center mb-1">
              <span class="text-xs font-bold text-slate-900 dark:text-slate-100">${h.month}</span>
              <span class="text-[10px] font-semibold text-primary">K=${h.decayCoefficient}</span>
            </div>
            <div class="flex justify-between text-[10px] text-slate-500 dark:text-slate-400">
              <span>${i18n.t('profile.avg_score')}: ${avg}/100</span>
              <span>${h.createdAt ? new Date(h.createdAt).toLocaleDateString() : ''}</span>
            </div>
          </div>
        `;
      }).join('');
    } catch {
      el.innerHTML = `<p class="text-slate-500 dark:text-slate-400 text-xs">${i18n.t('profile.no_history')}</p>`;
    }
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

  _findGithubForEmployee(id) {
    if (!id || !this._ghContributors?.length) return null;
    const preferred = GITHUB_ACCOUNT_MAP[id];
    const candidates = [];
    if (preferred) candidates.push(String(preferred).toLowerCase());
    candidates.push(String(id).toLowerCase());
    return this._ghContributors.find(
      (c) => candidates.includes(String(c.login || '').toLowerCase()),
    ) || null;
  },
};
