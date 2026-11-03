# -*- coding: utf-8 -*-
"""用本机 Edge 无头浏览器给系统页面截图（用于详细设计文档和验收演示）。"""
from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get('APP_URL', 'http://127.0.0.1:5000')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'screenshots')


def shot(page, name, full=True):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=full)
    print('saved', path)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True,
                                    args=['--force-device-scale-factor=1.5'])
        ctx = browser.new_context(viewport={'width': 1440, 'height': 950},
                                  device_scale_factor=1.5, locale='zh-CN')
        page = ctx.new_page()
        page.goto(BASE + '/login', wait_until='networkidle')
        shot(page, '01_login.png')

        page.fill('#username', 'admin')
        page.fill('#password', '123456')
        page.click('button[type=submit]')
        page.wait_for_url('**/detect', timeout=15000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(800)
        shot(page, '03_detect.png')

        page.goto(BASE + '/history', wait_until='networkidle')
        page.wait_for_timeout(1200)
        shot(page, '05_history.png')

        page.goto(BASE + '/stats', wait_until='networkidle')
        page.wait_for_timeout(1600)
        shot(page, '06_stats.png')

        # 结果页：挑一条有缺陷的记录，截图更有代表性
        page.goto(BASE + '/api/records?page=1&size=10')
        text = page.inner_text('body')
        import json
        data = json.loads(text)
        items = data['data']['items']
        picked = next((x for x in items if x['total'] > 0), items[0] if items else None)
        if picked:
            rid = picked['id']
            page.goto(BASE + '/result/' + str(rid), wait_until='networkidle')
            page.wait_for_timeout(900)
            shot(page, '04_result.png')
        else:
            print('暂无记录，跳过结果页截图')

        # 小屏适配检查：不应出现横向溢出
        mobile = ctx.new_page()
        mobile.set_viewport_size({'width': 390, 'height': 844})
        mobile.goto(BASE + '/detect', wait_until='networkidle')
        mobile.wait_for_timeout(600)
        overflow = mobile.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        print('mobile overflow px =', overflow)
        mobile.screenshot(path=os.path.join(OUT, '07_mobile.png'), full_page=True)
        print('saved', os.path.join(OUT, '07_mobile.png'))

        browser.close()


if __name__ == '__main__':
    sys.exit(main())

