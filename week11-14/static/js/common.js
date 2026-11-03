/* 公共脚本：请求封装、提示、日期格式化、侧边栏交互 */
(function () {
  const CLASS_COLORS = {
    scratch: '#ff7a45', crack: '#ff4d4f', bright_spot: '#52c41a',
    dark_spot: '#722ed1', stain: '#faad14', edge_chip: '#13c2c2'
  };

  async function api(path, options = {}) {
    const opts = Object.assign({ credentials: 'same-origin' }, options);
    opts.headers = Object.assign({}, options.headers || {});
    if (opts.body && !(opts.body instanceof FormData) && typeof opts.body === 'object') {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, opts);
    let payload = null;
    try { payload = await res.json(); } catch (e) { /* 非 JSON 响应 */ }
    if (res.status === 401) {
      const next = encodeURIComponent(location.pathname + location.search);
      location.href = '/login?next=' + next;
      throw new Error('请先登录');
    }
    if (!res.ok || !payload || payload.code !== 200) {
      throw new Error((payload && payload.message) || ('请求失败（' + res.status + '）'));
    }
    return payload.data;
  }

  function toast(message, type = 'success', timeout = 3200) {
    const wrap = document.getElementById('toastWrap');
    if (!wrap) return;
    const el = document.createElement('div');
    el.className = 'toast-item toast-' + type;
    const icons = { success: '✓', error: '!', info: 'i' };
    el.innerHTML = '<span class="toast-icon">' + (icons[type] || 'i') + '</span><span>' + escapeHtml(message) + '</span>';
    wrap.appendChild(el);
    requestAnimationFrame(() => el.classList.add('show'));
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 260);
    }, timeout);
  }

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fmtDate(value, withTime = true) {
    if (!value) return '—';
    const s = String(value).replace('T', ' ');
    return withTime ? s.slice(5, 16) : s.slice(0, 10);
  }

  function fmtFull(value) {
    return value ? String(value).slice(0, 16) : '—';
  }

  function num(n) {
    return Number(n || 0).toLocaleString('zh-CN');
  }

  function classColor(name) {
    return CLASS_COLORS[name] || '#2f6bff';
  }

  function todayStr() {
    const d = new Date();
    const p = v => String(v).padStart(2, '0');
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }

  // 侧边栏（小屏幕）
  document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('menuBtn');
    const sidebar = document.getElementById('sidebar');
    if (menuBtn && sidebar) {
      menuBtn.addEventListener('click', () => document.body.classList.toggle('sidebar-open'));
      sidebar.addEventListener('click', e => {
        if (e.target.closest('.nav-item')) document.body.classList.remove('sidebar-open');
      });
    }
    const todayText = document.getElementById('todayText');
    if (todayText) {
      const d = new Date();
      const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
      todayText.textContent = d.getFullYear() + ' 年 ' + (d.getMonth() + 1) + ' 月 ' + d.getDate() + ' 日 周' + week;
    }
    const status = document.getElementById('engineStatus');
    if (status) {
      api('/api/health').then(h => {
        status.classList.add(h.model_exists ? 'ok' : 'warn');
        status.querySelector('span').textContent = h.model_exists ? '检测引擎就绪' : '模型未加载';
        const device = document.getElementById('deviceValue');
        if (device) device.textContent = h.model_loaded ? '已加载' : '按需加载';
      }).catch(() => {
        status.classList.add('warn');
        status.querySelector('span').textContent = '服务连接失败';
      });
    }
  });

  window.App = { api, toast, escapeHtml, fmtDate, fmtFull, num, classColor, todayStr };
})();
