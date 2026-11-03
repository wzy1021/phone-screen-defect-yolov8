/* 数据统计页：数字卡片 + 柱状图 + 饼图 + 趋势图 */
(function () {
  const startDate = document.getElementById('startDate');
  const endDate = document.getElementById('endDate');
  const barEl = document.getElementById('barChart');
  const pieEl = document.getElementById('pieChart');
  const trendEl = document.getElementById('trendChart');
  const charts = [];

  function initChart(el) {
    if (!el || !window.echarts) return null;
    const c = echarts.init(el);
    charts.push(c);
    return c;
  }

  function countUp(el, target, suffix = '') {
    const start = performance.now();
    const from = 0;
    const dur = 600;
    function step(now) {
      const t = Math.min(1, (now - start) / dur);
      const value = Math.round(from + (target - from) * (1 - Math.pow(1 - t, 3)));
      el.textContent = value.toLocaleString('zh-CN') + (t >= 1 ? suffix : '');
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const bar = initChart(barEl);
  const pie = initChart(pieEl);
  const trend = initChart(trendEl);

  const commonText = {
    color: '#5b6b84',
    fontFamily: '"Microsoft YaHei", "PingFang SC", system-ui, sans-serif'
  };

  function renderBar(data) {
    if (!bar) return;
    const items = data.per_class;
    bar.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 18, top: 26, bottom: 8, containLabel: true },
      xAxis: {
        type: 'category',
        data: items.map(c => c.cn),
        axisLine: { lineStyle: { color: '#dfe6f1' } },
        axisTick: { show: false },
        axisLabel: { ...commonText, fontSize: 12 }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: '#eef2f8' } },
        axisLabel: { ...commonText, fontSize: 12 }
      },
      series: [{
        type: 'bar',
        data: items.map(c => ({
          value: c.count,
          itemStyle: { color: c.color, borderRadius: [6, 6, 0, 0] }
        })),
        barWidth: 28,
        label: { show: true, position: 'top', ...commonText, fontSize: 12 }
      }]
    });
  }

  function renderPie(data) {
    if (!pie) return;
    const items = data.per_class.filter(c => c.count > 0);
    if (!items.length) {
      pie.clear();
      pie.setOption({
        title: {
          text: '暂无缺陷数据', left: 'center', top: 'middle',
          textStyle: { color: '#9aa8bd', fontSize: 14, fontWeight: 'normal' }
        }
      });
      return;
    }
    pie.clear();
    pie.setOption({
      tooltip: { trigger: 'item', formatter: '{b}：{c}（{d}%）' },
      legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: commonText },
      series: [{
        type: 'pie',
        radius: ['46%', '70%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold', formatter: '{b}\n{d}%' }
        },
        data: items.map(c => ({ name: c.cn, value: c.count, itemStyle: { color: c.color } }))
      }]
    });
  }

  function renderTrend(data) {
    if (!trend) return;
    const days = data.trend;
    if (!days.length) {
      trend.clear();
      trend.setOption({
        title: {
          text: '暂无检测记录', left: 'center', top: 'middle',
          textStyle: { color: '#9aa8bd', fontSize: 14, fontWeight: 'normal' }
        }
      });
      return;
    }
    trend.clear();
    trend.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, right: 0, icon: 'roundRect', itemWidth: 12, itemHeight: 4, textStyle: commonText },
      grid: { left: 10, right: 16, top: 34, bottom: 6, containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: days.map(d => d.day.slice(5)),
        axisLine: { lineStyle: { color: '#dfe6f1' } },
        axisTick: { show: false },
        axisLabel: { ...commonText, fontSize: 12 }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: '#eef2f8' } },
        axisLabel: { ...commonText, fontSize: 12 }
      },
      series: [
        {
          name: '检测数', type: 'line', smooth: true, symbolSize: 7,
          data: days.map(d => d.c),
          itemStyle: { color: '#2f6bff' },
          lineStyle: { width: 3, color: '#2f6bff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(47,107,255,0.28)' },
              { offset: 1, color: 'rgba(47,107,255,0.02)' }
            ])
          }
        },
        {
          name: '缺陷数', type: 'line', smooth: true, symbolSize: 7,
          data: days.map(d => d.d),
          itemStyle: { color: '#ff7a45' },
          lineStyle: { width: 3, color: '#ff7a45' }
        }
      ]
    });
  }

  function params() {
    const p = new URLSearchParams();
    if (startDate.value) p.set('start', startDate.value);
    if (endDate.value) p.set('end', endDate.value);
    return p.toString();
  }

  async function load() {
    try {
      const data = await App.api('/api/stats?' + params());
      countUp(document.getElementById('statRecords'), data.total_records);
      countUp(document.getElementById('statDefects'), data.total_defects);
      countUp(document.getElementById('statToday'), data.today_records);
      document.getElementById('statCost').textContent = Number(data.avg_cost_ms).toFixed(1);
      renderBar(data);
      renderPie(data);
      renderTrend(data);
    } catch (err) {
      App.toast(err.message, 'error');
    }
  }

  document.getElementById('applyBtn').addEventListener('click', load);
  document.getElementById('resetBtn').addEventListener('click', () => {
    startDate.value = ''; endDate.value = ''; load();
  });
  document.querySelectorAll('.quick-range button').forEach(btn => {
    btn.addEventListener('click', () => {
      const days = Number(btn.dataset.days);
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - days + 1);
      const fmt = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
      startDate.value = fmt(start);
      endDate.value = fmt(end);
      load();
    });
  });

  window.addEventListener('resize', () => charts.forEach(c => c.resize()));
  load();
})();
