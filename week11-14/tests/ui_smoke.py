# -*- coding: utf-8 -*-
"""界面联调冒烟测试：真实浏览器走一遍 登录 -> 上传 -> 检测 -> 结果 -> 历史 -> 统计。

需要先启动系统（http://127.0.0.1:5000）和本机 Edge。
测试产生的记录会在最后删除，不影响演示数据。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5000'
ROOT = Path(__file__).resolve().parent.parent
IMAGES = [str(p) for p in sorted((ROOT / 'datasets' / 'images' / 'test').glob('*.jpg'))[:2]]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 950}, locale='zh-CN')
        page.goto(BASE + '/login', wait_until='networkidle')
        page.fill('#username', 'admin')
        page.fill('#password', '123456')
        page.click('button[type=submit]')
        page.wait_for_url('**/detect', timeout=15000)
        print('[1] 登录成功')

        page.set_input_files('#fileInput', IMAGES)
        page.wait_for_selector('.preview-item', timeout=5000)
        count = page.locator('.preview-item').count()
        assert count == 2, count
        print('[2] 已选择 2 张图片，缩略图正常')

        page.click('#detectBtn')
        page.wait_for_url('**/result/*', timeout=120000)
        page.wait_for_load_state('networkidle')
        title = page.locator('h1').first.inner_text()
        assert '检测结果' in title, title
        body = page.inner_text('body')
        assert '缺陷明细' in body
        print('[3] 检测完成并跳转结果页:', page.url)

        # 管理员保存默认阈值
        page.goto(BASE + '/detect', wait_until='networkidle')
        page.eval_on_selector('#confRange', "el => { el.value = 0.3; el.dispatchEvent(new Event('input', {bubbles: true})); }")
        page.click('#saveDefaultBtn')
        page.wait_for_selector('.toast-item', timeout=8000)
        saved = page.evaluate("() => App.api('/api/settings').then(s => s.conf_threshold)")
        assert abs(float(saved) - 0.3) < 1e-6, saved
        page.evaluate("() => App.api('/api/settings', {method: 'PUT', body: {conf_threshold: 0.25}})")
        print('[4] 阈值保存/恢复成功')

        # 历史与统计页面
        page.goto(BASE + '/history', wait_until='networkidle')
        page.wait_for_timeout(500)
        rows = page.locator('#recordBody tr').count()
        assert rows >= 2, rows
        page.goto(BASE + '/stats', wait_until='networkidle')
        page.wait_for_timeout(1200)
        total = page.locator('#statRecords').inner_text()
        assert int(total.replace(',', '')) >= 2, total
        print('[5] 历史列表和统计页正常，检测总数:', total)

        # 删除本次测试产生的记录（测试上传的图片都以 img_ 开头）
        resp = page.request.get(BASE + '/api/records?page=1&size=100')
        data = resp.json()
        removed = 0
        for item in data['data']['items']:
            if item['image_path'].startswith('uploads/img_'):
                page.request.delete(BASE + '/api/records/' + str(item['id']))
                removed += 1
        resp = page.request.get(BASE + '/api/records?page=1&size=1')
        left = resp.json()['data']['total']
        print(f'[6] 测试记录已清理 {removed} 条，剩余记录: {left}')

        browser.close()
    print('UI SMOKE OK')


if __name__ == '__main__':
    sys.exit(main())
