# -*- coding: utf-8 -*-
"""系统启动入口。

用法：
    python run.py                 # http://127.0.0.1:5000
    python run.py --port 5001
    python run.py --no-warmup     # 启动时不预加载模型（更快，但第一张图会慢一点）
"""
from __future__ import annotations

import argparse
import os
import sys


def preflight() -> bool:
    """启动前检查当前解释器有没有 Flask / ultralytics / torch。"""
    try:
        import flask  # noqa: F401
    except ImportError:
        print('启动失败：当前 Python 环境没有安装 Flask。')
        print('当前解释器：', sys.executable)
        print('请用 启动系统.bat，或执行 pip install -r requirements.txt')
        return False

    try:
        import ultralytics
        import torch
    except ImportError as exc:
        print('启动失败：当前 Python 环境缺少检测依赖。')
        print('缺失模块：', getattr(exc, 'name', exc))
        print('当前解释器：', sys.executable)
        print()
        print('请用下面任意一种方式启动：')
        print('  1) 双击 启动系统.bat')
        print(r'  2) C:\Users\wzy06\.conda\envs\diffusion-course\python.exe run.py')
        print('  3) 先激活 conda 环境：conda activate diffusion-course，再 python run.py')
        return False

    device = 'CUDA 可用' if getattr(torch, 'cuda', None) and torch.cuda.is_available() else 'CPU'
    print(f'环境检查通过：Python {sys.version.split()[0]} / ultralytics {ultralytics.__version__} / '
          f'torch {torch.__version__} / {device}')
    return True


def main():
    ap = argparse.ArgumentParser(description='手机屏幕外观缺陷智能检测系统')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=5000)
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--no-warmup', action='store_true', help='启动时不预加载模型')
    args = ap.parse_args()

    if not preflight():
        sys.exit(1)

    from app import create_app
    app = create_app()

    with app.app_context():
        print('数据库：', app.config['DB_PATH'])
        print('模型：  ', app.config['MODEL_PATH'])
        if not os.path.exists(app.config['MODEL_PATH']):
            print('提示：还没有 models/best.pt，检测接口会返回 503。'
                  '请先运行 train/train.py 训练模型。')
        elif not args.no_warmup:
            from app.detection import get_detector
            try:
                print('正在加载模型……', end='', flush=True)
                get_detector()._ensure_model()
                print('完成')
            except Exception as exc:
                print(f'失败：{exc}')

    print(f'\n打开浏览器访问：http://{args.host}:{args.port}\n')
    app.run(host=args.host, port=args.port, debug=args.debug,
            use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
