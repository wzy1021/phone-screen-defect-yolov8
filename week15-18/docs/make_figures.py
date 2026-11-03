# -*- coding: utf-8 -*-
"""生成 week15-18 文档与 PPT 用的统计图。

用法（在项目根目录）：python week15-18/docs/make_figures.py
依赖 matplotlib，用本机 conda 环境 diffusion-course 运行。
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
W1114 = ROOT / 'week11-14'
OUT = HERE / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

INK = '#101a2e'
MUTED = '#6f7f99'
BLUE = '#2f6bff'
BLUE2 = '#1b4ed8'
GREEN = '#1f9d55'
ORANGE = '#f5a623'
RED = '#e5484d'
GRID = '#e4ebf6'
BG = '#ffffff'

ABL = json.loads((W1114 / 'docs' / 'ablation.json').read_text(encoding='utf-8-sig'))
PERF = json.loads((W1114 / 'docs' / 'perf.json').read_text(encoding='utf-8'))
METRICS = json.loads((W1114 / 'models' / 'metrics.json').read_text(encoding='utf-8'))
METRICS_MIX = json.loads((W1114 / 'models' / 'metrics_mix.json').read_text(encoding='utf-8'))


def clean(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#c9d5e8')
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis='y', color=GRID, linewidth=0.9)
    ax.set_axisbelow(True)


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print('OK:', path)


# ------------------------------------------------------------ 1 测试用例分布
def fig_test_modules():
    modules = ['认证与注册', '上传与检测', '记录与导出', '参数与权限',
               '个人资料', '数据集', '模型']
    cases = [7, 4, 4, 3, 2, 4, 2]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bars = ax.barh(modules[::-1], cases[::-1], color=BLUE, height=0.56, zorder=3)
    for b, v in zip(bars, cases[::-1]):
        ax.text(b.get_width() + 0.12, b.get_y() + b.get_height() / 2, f'{v} 个',
                va='center', fontsize=9.5, color=INK)
    for i, b in enumerate(bars):
        b.set_color(BLUE if i % 2 else BLUE2)
    ax.set_xlim(0, 8.2)
    ax.set_xlabel('自动化用例数', fontsize=9.5, color=MUTED)
    ax.set_title('26 个自动化用例的模块分布（全部通过）', fontsize=12, color=INK, pad=10)
    clean(ax)
    ax.text(7.9, 0.15, '通过率 100%', ha='right', fontsize=10, color=GREEN, fontweight='bold')
    save(fig, 'fig_test_modules.png')


# ------------------------------------------------------------ 2 性能
def fig_perf():
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8),
                             gridspec_kw={'width_ratios': [1.15, 1]})
    ax = axes[0]
    labels = ['预处理', '推理', '后处理', '上传/画框/写库']
    vals = [METRICS_MIX['speed_ms']['preprocess'], METRICS_MIX['speed_ms']['inference'],
            METRICS_MIX['speed_ms']['postprocess'],
            max(PERF['api_ms'] - sum(METRICS_MIX['speed_ms'][k] for k in
                                     ('preprocess', 'inference', 'postprocess')), 0)]
    colors = ['#8fb3ff', BLUE, '#5b8def', '#c9d9ff']
    bars = ax.bar(labels, vals, color=colors, width=0.58, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}', ha='center',
                fontsize=9, color=INK)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel('毫秒', fontsize=9.5, color=MUTED)
    ax.set_title(f'检测接口耗时构成（合计 {PERF["api_ms"]:.0f} ms）',
                 fontsize=11, color=INK, pad=10)
    clean(ax)
    ax.tick_params(axis='x', labelsize=8.5)

    ax = axes[1]
    names = ['模型加载', '单张检测接口', '页面响应', '数据库查询']
    vals2 = [PERF['model_load_s'] * 1000, PERF['api_ms'], PERF['page_ms'], PERF['query_ms']]
    bars = ax.barh(names[::-1], vals2[::-1], color=['#c9d9ff', '#8fb3ff', '#5b8def', BLUE],
                   height=0.52, zorder=3)
    ax.set_xscale('log')
    for b, v in zip(bars, vals2[::-1]):
        txt = f'{v/1000:.2f} s' if v >= 1000 else f'{v:.2f} ms'
        ax.text(b.get_width() * 1.15, b.get_y() + b.get_height() / 2, txt,
                va='center', fontsize=9, color=INK)
    ax.set_xlim(1, 30000)
    ax.set_xlabel('毫秒（对数坐标）', fontsize=9, color=MUTED)
    ax.set_title('首次加载与常规请求的耗时量级', fontsize=11, color=INK, pad=10)
    clean(ax)
    save(fig, 'fig_perf.png')


# ------------------------------------------------------------ 3 版本对比
def fig_metrics_compare():
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9),
                             gridspec_kw={'width_ratios': [1.55, 1]})
    ax = axes[0]
    names = ['v1 基线', 'v2 仅困难数据', 'mix 混合训练']
    orig = [ABL['v1']['v1_map50'], ABL['v2']['v1_map50'], ABL['mix']['v1_map50']]
    hard = [ABL['v1']['hard_map50'], ABL['v2']['hard_map50'], ABL['mix']['hard_map50']]
    x = range(len(names))
    w = 0.34
    b1 = ax.bar([i - w / 2 for i in x], orig, width=w, color=BLUE, label='原测试集 mAP50', zorder=3)
    b2 = ax.bar([i + w / 2 for i in x], hard, width=w, color=ORANGE, label='困难测试集 mAP50', zorder=3)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02, f'{b.get_height():.3f}',
                    ha='center', fontsize=8.8, color=INK)
    ax.set_xticks(list(x)); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel('mAP50', fontsize=9.5, color=MUTED)
    ax.set_title('三个版本的精度权衡', fontsize=11.5, color=INK, pad=10)
    ax.legend(frameon=False, fontsize=8.5, loc='upper center',
              bbox_to_anchor=(0.5, -0.16), ncol=2)
    clean(ax)

    ax = axes[1]
    boxes = [ABL['v1']['real_boxes'], ABL['v2']['real_boxes'], ABL['mix']['real_boxes']]
    bars = ax.bar(names, boxes, color=[RED, '#f08a5d', GREEN], width=0.5, zorder=3)
    for b, v in zip(bars, boxes):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.7, f'{v}', ha='center',
                fontsize=11, color=INK, fontweight='bold')
    ax.set_ylim(0, 31)
    ax.set_ylabel('真实碎屏图检出框数', fontsize=9.5, color=MUTED)
    ax.set_title('真实图误检（越少越好）', fontsize=11.5, color=INK, pad=10)
    ax.tick_params(axis='x', labelsize=8.2)
    clean(ax)
    save(fig, 'fig_metrics_compare.png')


# ------------------------------------------------------------ 4 分类指标
def fig_per_class():
    order = ['scratch', 'crack', 'bright_spot', 'dark_spot', 'stain', 'edge_chip']
    cn = {'scratch': '划痕', 'crack': '裂纹', 'bright_spot': '亮点',
          'dark_spot': '暗点', 'stain': '污渍', 'edge_chip': '边缘崩缺'}
    pc = {c['class_name']: c for c in METRICS_MIX['per_class']}
    p = [pc[k]['precision'] for k in order]
    r = [pc[k]['recall'] for k in order]
    m = [pc[k]['map50'] for k in order]
    x = range(len(order))
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    w = 0.26
    for off, vals, color, label in [(-w, p, BLUE, 'Precision'), (0, r, GREEN, 'Recall'),
                                    (w, m, ORANGE, 'mAP50')]:
        bars = ax.bar([i + off for i in x], vals, width=w, color=color, label=label, zorder=3)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.012, f'{b.get_height():.2f}',
                    ha='center', fontsize=7.6, color=INK, rotation=90)
    ax.set_xticks(list(x)); ax.set_xticklabels([cn[k] for k in order], fontsize=9.5)
    ax.set_ylim(0.7, 1.06)
    ax.set_ylabel('指标值', fontsize=9.5, color=MUTED)
    ax.set_title('混合模型在混合测试集上的分类别指标', fontsize=11.5, color=INK, pad=10)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc='lower right')
    clean(ax)
    save(fig, 'fig_per_class.png')


# ------------------------------------------------------------ 5 进度甘特图
def fig_timeline():
    tasks = [
        ('选题与调研', 3, 2, '#9db8ff'),
        ('需求分析 / 可行性', 5, 2, '#8fb3ff'),
        ('概要设计', 7, 4, '#5b8def'),
        ('数据集构建', 11, 1.5, '#7bc89a'),
        ('模型训练与调优', 12, 2, '#3fae6e'),
        ('后端与检测模块', 13, 1.5, '#f0b45a'),
        ('前端与联调', 14, 1.5, '#f5a623'),
        ('测试与缺陷修复', 15, 2, '#e58a8d'),
        ('文档整合 / 答辩', 17, 2, '#e5484d'),
    ]
    fig, ax = plt.subplots(figsize=(9.4, 4.0))
    for i, (name, start, dur, color) in enumerate(tasks):
        y = len(tasks) - i - 1
        ax.barh(y, dur, left=start, height=0.52, color=color, zorder=3)
        ax.text(start + dur + 0.15, y, f'第 {start:g}–{start+dur-0.5:g} 周',
                va='center', fontsize=8, color=MUTED)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t[0] for t in tasks][::-1], fontsize=9)
    ax.set_xlim(2, 20)
    ax.set_xticks(range(2, 21, 2))
    ax.set_xlabel('课程周次', fontsize=9.5, color=MUTED)
    ax.set_title('课程设计 18 周进度与实际执行情况', fontsize=12, color=INK, pad=10)
    for xline, label in [(14.5, '实现阶段结束'), (18.5, '验收结束')]:
        ax.axvline(xline, color='#b9c7de', linestyle='--', linewidth=0.9, zorder=1)
        ax.text(xline - 0.1, len(tasks) - 0.2, label, ha='right', va='top',
                fontsize=8, color=MUTED)
    clean(ax)
    ax.grid(axis='x', color=GRID, linewidth=0.9)
    ax.grid(axis='y', visible=False)
    save(fig, 'fig_timeline.png')


# ------------------------------------------------------------ 6 数据构成
def fig_data_mix():
    labels = ['原数据 train', '原数据 val', '原数据 test',
              '困难数据 train', '困难数据 val', '困难数据 test']
    vals = [1000, 160, 160, 600, 100, 100]
    colors = [BLUE, '#6f9bff', '#a9c2ff', ORANGE, '#f7c46c', '#fbe0b0']
    fig, ax = plt.subplots(figsize=(8.2, 3.3))
    bars = ax.bar(labels, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 15, str(v), ha='center',
                fontsize=9.5, color=INK)
    ax.set_ylim(0, 1120)
    ax.set_ylabel('图片数量', fontsize=9.5, color=MUTED)
    ax.set_title('原数据与困难数据的划分（混合后训练集 1600 张）',
                 fontsize=11.5, color=INK, pad=10)
    ax.tick_params(axis='x', labelsize=8.2)
    clean(ax)
    save(fig, 'fig_data_mix.png')


if __name__ == '__main__':
    fig_test_modules()
    fig_perf()
    fig_metrics_compare()
    fig_per_class()
    fig_timeline()
    fig_data_mix()
