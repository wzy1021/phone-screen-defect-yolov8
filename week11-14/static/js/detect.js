/* 检测页交互：选择/拖拽图片、预览、逐张检测 */
(function () {
  const ALLOWED = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp'];
  const MAX_SIZE = 20 * 1024 * 1024;

  const dz = document.getElementById('dropzone');
  const input = document.getElementById('fileInput');
  const previewList = document.getElementById('previewList');
  const detectBtn = document.getElementById('detectBtn');
  const confRange = document.getElementById('confRange');
  const confValue = document.getElementById('confValue');
  const progressBox = document.getElementById('progressBox');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const recentList = document.getElementById('recentList');

  let files = [];
  let busy = false;

  function addFiles(list) {
    Array.from(list).forEach(file => {
      if (!ALLOWED.includes(file.type)) {
        App.toast(file.name + '：格式不支持，请使用 JPG/PNG/BMP/WEBP', 'error');
        return;
      }
      if (file.size > MAX_SIZE) {
        App.toast(file.name + '：超过 20MB', 'error');
        return;
      }
      if (files.some(f => f.file.name === file.name && f.file.size === file.size)) return;
      files.push({ file, url: URL.createObjectURL(file) });
    });
    render();
  }

  function render() {
    previewList.innerHTML = files.map((f, i) => `
      <div class="preview-item">
        <img src="${f.url}" alt="">
        <button type="button" class="preview-remove" data-index="${i}" title="移除">×</button>
        <div class="preview-name">${App.escapeHtml(f.file.name)}</div>
      </div>`).join('');
    detectBtn.disabled = files.length === 0 || busy;
    previewList.querySelectorAll('.preview-remove').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const i = Number(btn.dataset.index);
        URL.revokeObjectURL(files[i].url);
        files.splice(i, 1);
        render();
      });
    });
  }

  dz.addEventListener('click', () => input.click());
  dz.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
  });
  input.addEventListener('change', () => { addFiles(input.files); input.value = ''; });

  ['dragenter', 'dragover'].forEach(evt => dz.addEventListener(evt, e => {
    e.preventDefault(); dz.classList.add('dragover');
  }));
  ['dragleave', 'drop'].forEach(evt => dz.addEventListener(evt, e => {
    e.preventDefault(); dz.classList.remove('dragover');
  }));
  dz.addEventListener('drop', e => {
    if (e.dataTransfer && e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  });

  confRange.addEventListener('input', () => {
    confValue.textContent = Number(confRange.value).toFixed(2);
  });

  async function detectAll() {
    if (!files.length || busy) return;
    busy = true;
    detectBtn.disabled = true;
    progressBox.hidden = false;
    const conf = Number(confRange.value);
    const ids = [];
    let failed = 0;

    for (let i = 0; i < files.length; i++) {
      progressText.textContent = `正在检测第 ${i + 1} / ${files.length} 张：${files[i].file.name}`;
      progressBar.style.width = Math.round((i / files.length) * 100) + '%';
      const fd = new FormData();
      fd.append('file', files[i].file);
      fd.append('conf', conf);
      const roi = document.getElementById('roiToggle');
      if (roi) fd.append('roi', roi.checked ? '1' : '0');
      try {
        const data = await App.api('/api/detect', { method: 'POST', body: fd });
        ids.push(data.record_id);
      } catch (err) {
        failed += 1;
        App.toast(files[i].file.name + '：' + err.message, 'error', 5000);
      }
    }

    progressBar.style.width = '100%';
    progressText.textContent = '检测完成';
    busy = false;
    detectBtn.disabled = false;

    if (ids.length) {
      App.toast(failed ? `完成 ${ids.length} 张，失败 ${failed} 张` : `已完成 ${ids.length} 张检测`, 'success');
      setTimeout(() => { location.href = '/result/' + ids[0]; }, 500);
    } else {
      progressBox.hidden = true;
      App.toast('全部检测失败，请检查模型是否已训练', 'error', 5000);
    }
  }

  detectBtn.addEventListener('click', detectAll);

  const saveBtn = document.getElementById('saveDefaultBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      try {
        await App.api('/api/settings', { method: 'PUT', body: { conf_threshold: Number(confRange.value) } });
        App.toast('已保存为默认置信度阈值');
      } catch (err) { App.toast(err.message, 'error'); }
    });
  }

  async function loadRecent() {
    try {
      const data = await App.api('/api/records?page=1&size=4');
      if (!data.items.length) {
        recentList.innerHTML = '<div class="empty-mini">还没有检测记录，先上传一张试试</div>';
        return;
      }
      recentList.innerHTML = data.items.map(r => `
        <a class="recent-item" href="/result/${r.id}">
          <img src="${r.image_url}" alt="">
          <div class="recent-main">
            <div class="recent-title">#${r.id} · ${r.total} 处缺陷</div>
            <div class="recent-meta">${App.fmtDate(r.created_at)} · ${r.cost_ms} ms</div>
          </div>
          <span class="badge-soft ${r.total ? 'badge-red' : 'badge-green'}">${r.total ? '有缺陷' : '正常'}</span>
        </a>`).join('');
    } catch (err) {
      recentList.innerHTML = '<div class="empty-mini">' + App.escapeHtml(err.message) + '</div>';
    }
  }

  loadRecent();
})();
