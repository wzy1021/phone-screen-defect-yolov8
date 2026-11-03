/* 管理员用户列表 */
(function () {
  const body = document.getElementById('userBody');
  const search = document.getElementById('userSearch');
  const summary = document.getElementById('userSummary');
  const count = document.getElementById('userCount');
  let all = [];

  function avatarHtml(u) {
    if (u.avatar_url) {
      return `<img class="mini-avatar" src="${u.avatar_url}" alt="">`;
    }
    const ch = (u.nickname || u.username || '?').trim().charAt(0).toUpperCase();
    return `<span class="mini-avatar mini-avatar-letter">${App.escapeHtml(ch)}</span>`;
  }

  function render() {
    const q = (search.value || '').trim().toLowerCase();
    const rows = all.filter(u => !q ||
      (u.username || '').toLowerCase().includes(q) ||
      (u.nickname || '').toLowerCase().includes(q));
    count.textContent = all.length + ' 人';
    const admins = all.filter(u => u.role === 'admin').length;
    summary.textContent = `共 ${all.length} 人：管理员 ${admins}，普通用户 ${all.length - admins}`;

    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="7"><div class="empty-mini">没有匹配的用户</div></td></tr>';
      return;
    }
    body.innerHTML = rows.map(u => `
      <tr>
        <td>
          <div class="user-cell">
            ${avatarHtml(u)}
            <div>
              <div class="user-cell-name">${App.escapeHtml(u.nickname || u.username)}</div>
              <div class="user-cell-sub">@${App.escapeHtml(u.username)}</div>
            </div>
          </div>
        </td>
        <td><span class="badge-soft ${u.role === 'admin' ? 'badge-blue' : ''}">${u.role === 'admin' ? '管理员' : '普通用户'}</span></td>
        <td>${App.fmtFull(u.created_at)}</td>
        <td>${u.records}</td>
        <td>${u.defects}</td>
        <td>${u.last_at ? App.fmtFull(u.last_at) : '—'}</td>
        <td><a class="link-btn" href="/history?user_id=${u.id}">查看记录</a></td>
      </tr>`).join('');
  }

  async function load() {
    try {
      all = await App.api('/api/users');
      render();
    } catch (err) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-mini">${App.escapeHtml(err.message)}</div></td></tr>`;
    }
  }

  search.addEventListener('input', render);
  load();
})();
