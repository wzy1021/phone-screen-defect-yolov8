/* 静态演示：读取 assets/demo.json，回放真实系统预生成的检测结果 */
(function () {
  const COLORS = {
    scratch: '#ff7a45', crack: '#ff4d4f', bright_spot: '#52c41a',
    dark_spot: '#722ed1', stain: '#faad14', edge_chip: '#13c2c2'
  };
  const sampleList = document.getElementById('sampleList');
  const stageImg = document.getElementById('stageImg');
  const stageEmpty = document.getElementById('stageEmpty');
  const detectBtn = document.getElementById('detectBtn');
  const resetBtn = document.getElementById('resetBtn');
  const viewToggle = document.getElementById('viewToggle');
  const resultArea = document.getElementById('resultArea');
  const progressBox = document.getElementById('progressBox');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const scanOverlay = document.getElementById('scanOverlay');

  let samples = [];
  let current = null;
  let view = 'original';
  let busy = false;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function setView(v) {
    view = v;
    if (!current) return;
    stageImg.src = v === 'result' ? current.result : current.original;
    viewToggle.querySelectorAll('button').forEach(b => {
      b.classList.toggle('active', b.dataset.view === v);
    });
  }

  function selectSample(s) {
    if (busy) return;
    current = s;
    resultArea.hidden = true;
    progressBox.hidden = true;
    scanOverlay.hidden = true;
    viewToggle.hidden = true;
    stageEmpty.hidden = true;
    stageImg.hidden = false;
    stageImg.src = s.original;
    detectBtn.disabled = false;
    resetBtn.disabled = false;
    sampleList.querySelectorAll('.sample').forEach(el => {
      el.classList.toggle('active', Number(el.dataset.id) === s.id);
    });
  }

  function renderSamples() {
    sampleList.innerHTML = samples.map(s => `
      <button class="sample" data-id="${s.id}">
        <img src="${s.original}" alt="${esc(s.name)}" loading="lazy">
        <span>${esc(s.name)}</span>
      </button>`).join('');
    sampleList.querySelectorAll('.sample').forEach(el => {
      el.addEventListener('click', () => {
        const s = samples.find(x => x.id === Number(el.dataset.id));
        if (s) selectSample(s);
      });
    });
  }

  function renderResult() {
    const s = current;
    document.getElementById('dTotal').innerHTML = `${s.total}<small> 处</small>`;
    document.getElementById('dCost').innerHTML = `${s.cost_ms}<small> ms</small>`;
    document.getElementById('dConf').textContent = Number(s.conf).toFixed(2);
    document.getElementById('dStatus').textContent = '完成';
    const list = document.getElementById('defectList');
    if (!s.defects.length) {
      list.innerHTML = '<div class="empty-mini">未发现缺陷</div>';
      return;
    }
    list.innerHTML = s.defects.map(d => {
      const color = COLORS[d.class_name] || '#2f6bff';
      return `<div class="defect-row">
        <i style="background:${color}"></i>
        <b>${esc(d.class_cn)}</b>
        <span>中心 (${(d.x * 100).toFixed(1)}%, ${(d.y * 100).toFixed(1)}%) · ${(d.w * 100).toFixed(1)}% × ${(d.h * 100).toFixed(1)}%</span>
        <span class="conf" style="color:${color}">${(d.conf * 100).toFixed(1)}%</span>
      </div>`;
    }).join('');
  }

  function detect() {
    if (!current || busy) return;
    busy = true;
    detectBtn.disabled = true;
    resetBtn.disabled = true;
    resultArea.hidden = true;
    viewToggle.hidden = true;
    progressBox.hidden = false;
    progressBar.style.width = '0%';
    progressText.textContent = '正在检测：' + current.name;
    scanOverlay.hidden = false;
    let p = 0;
    const timer = setInterval(() => {
      p = Math.min(100, p + 12 + Math.random() * 14);
      progressBar.style.width = p + '%';
      if (p >= 100) {
        clearInterval(timer);
        setTimeout(() => {
          scanOverlay.hidden = true;
          progressBox.hidden = true;
          stageImg.src = current.result;
          view = 'result';
          viewToggle.hidden = false;
          viewToggle.querySelectorAll('button').forEach(b => {
            b.classList.toggle('active', b.dataset.view === 'result');
          });
          renderResult();
          resultArea.hidden = false;
          busy = false;
          detectBtn.disabled = false;
          resetBtn.disabled = false;
        }, 220);
      }
    }, 90);
  }

  function reset() {
    if (!current || busy) return;
    setView('original');
    resultArea.hidden = true;
    viewToggle.hidden = true;
    progressBox.hidden = true;
    scanOverlay.hidden = true;
    stageImg.src = current.original;
  }

  detectBtn.addEventListener('click', detect);
  resetBtn.addEventListener('click', reset);
  viewToggle.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => setView(btn.dataset.view));
  });

  fetch('assets/demo.json')
    .then(r => { if (!r.ok) throw new Error('demo.json 加载失败'); return r.json(); })
    .then(data => {
      samples = data;
      if (!samples.length) throw new Error('没有样张');
      renderSamples();
      selectSample(samples[0]);
    })
    .catch(err => {
      sampleList.innerHTML = '<div class="empty-mini">演示数据加载失败<br>请通过 GitHub Pages 或本地 HTTP 服务打开</div>';
      console.error(err);
    });
})();
