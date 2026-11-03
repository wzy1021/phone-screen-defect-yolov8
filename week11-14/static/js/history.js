/* 历史记录页：筛选、分页、查看、删除 */
(function () {
  const state = { page: 1, size: 8, total: 0, pages: 1 };
  const body = document.getElementById('recordBody');
  const pager = document.getElementById('pager');
  const totalCount = document.getElementById('totalCount');
  const pageInfo = document.getElementById('pageInfo');
  const startDate = document.getElementById('startDate');
  const endDate = document.getElementById('endDate');
  const hasDefect = document.getElementById('hasDefect');
  const userFilter = document.getElementById('userFilter');
  const filterSummary = document.getElementById('filterSummary');

  function filters() {
    const p = new URLSearchParams({ page: state.page, size: state.size });
    if (startDate.value) p.set('start', startDate.value);
    if (endDate.value) p.set('end', endDate.value);
    if (hasDefect.value !== '') p.set('has_defect', hasDefect.value);
    if (userFilter && userFilter.value) p.set('user_id', userFilter.value);
    return p;
  }

  function renderRows(items) {
    if (!items.length) {
      body.innerHTML = '<tr><td colspan="7"><div class="empty-mini">没有符合条件的记录</div></td></tr>';
      return;
    }
    body.innerHTML = items.map(r => `
      <tr>
        <td class="mono">#${r.id}</td>
        <td><img class="thumb" src="${r.image_url}" alt="" loading="lazy"></td>
        <td>
          <div class="cell-main">${App.fmtFull(r.created_at)}</div>
          <div class="cell-sub">${App.escapeHtml(r.username)}</div>
        </td>
        <td><span class="badge-soft ${r.total ? 'badge-red' : 'badge-green'}">${r.total} 处</span></td>
        <td>${r.cost_ms} ms</td>
        <td>${Number(r.conf).toFixed(2)}</td>
        <td>
          <a class="link-btn" href="/result/${r.id}">查看</a>
          <button class="link-btn danger" data-del="${r.id}">删除</button>
        </td>
      </tr>`).join('');
    body.querySelectorAll('[data-del]').forEach(btn => {
      btn.addEventListener('click', () => removeRecord(Number(btn.dataset.del)));
    });
  }

  function renderPager() {
    const pages = state.pages;
    if (pages <= 1) { pager.innerHTML = ''; return; }
    let nums = [];
    const cur = state.page;
    let from = Math.max(1, cur - 2);
    let to = Math.min(pages, from + 4);
    from = Math.max(1, to - 4);
    for (let i = from; i <= to; i++) nums.push(i);
    pager.innerHTML = `
      <button class="page-btn" data-page="${cur - 1}" ${cur <= 1 ? 'disabled' : ''}>上一页</button>
      ${from > 1 ? '<span class="page-dots">…</span>' : ''}
      ${nums.map(n => `<button class="page-btn ${n === cur ? 'active' : ''}" data-page="${n}">${n}</button>`).join('')}
      ${to < pages ? '<span class="page-dots">…</span>' : ''}
      <button class="page-btn" data-page="${cur + 1}" ${cur >= pages ? 'disabled' : ''}>下一页</button>
      <span class="page-total">共 ${pages} 页</span>`;
    pager.querySelectorAll('[data-page]').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = Number(btn.dataset.page);
        if (p >= 1 && p <= state.pages && p !== state.page) { state.page = p; load(); }
      });
    });
  }

  function renderSummary(total, items) {
    totalCount.textContent = App.num(total);
    pageInfo.textContent = `第 ${state.page} / ${state.pages} 页`;
    const parts = [];
    if (startDate.value) parts.push(startDate.value);
    if (endDate.value) parts.push(endDate.value);
    if (hasDefect.value === '1') parts.push('只看有缺陷');
    if (hasDefect.value === '0') parts.push('只看无缺陷');
    if (userFilter && userFilter.value) parts.push('用户：' + userFilter.options[userFilter.selectedIndex].text);
    filterSummary.textContent = parts.length ? '筛选：' + parts.join(' ~ ') : '';
  }

  async function load() {
    body.innerHTML = '<tr><td colspan="7"><div class="empty-mini">正在加载…</div></td></tr>';
    try {
      const data = await App.api('/api/records?' + filters().toString());
      state.total = data.total;
      state.pages = data.pages;
      if (state.page > data.pages) { state.page = data.pages; return load(); }
      renderRows(data.items);
      renderPager();
      renderSummary(data.total, data.items);
    } catch (err) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-mini">${App.escapeHtml(err.message)}</div></td></tr>`;
    }
  }

  async function removeRecord(id) {
    if (!confirm(`确定删除记录 #${id} 吗？\n原图和结果图也会一起删除，且无法恢复。`)) return;
    try {
      await App.api('/api/records/' + id, { method: 'DELETE' });
      App.toast('记录 #' + id + ' 已删除');
      if (state.page > 1 && body.querySelectorAll('tr').length === 1) state.page -= 1;
      load();
    } catch (err) { App.toast(err.message, 'error'); }
  }

  document.getElementById('searchBtn').addEventListener('click', () => { state.page = 1; load(); });
  document.getElementById('resetBtn').addEventListener('click', () => {
    startDate.value = ''; endDate.value = ''; hasDefect.value = '';
    if (userFilter) userFilter.value = '';
    state.page = 1; load();
  });

  load();
})();
