# -*- coding: utf-8 -*-
"""系统配置。"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # 演示用固定密钥；正式部署应通过环境变量 SECRET_KEY 覆盖
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'phonescreen-yolov8-course-design-2026'
    DB_PATH = str(BASE_DIR / 'data.db')
    UPLOAD_DIR = str(BASE_DIR / 'static' / 'uploads')
    RESULT_DIR = str(BASE_DIR / 'static' / 'results')
    AVATAR_DIR = str(BASE_DIR / 'static' / 'avatars')
    MODEL_PATH = str(BASE_DIR / 'models' / 'best.pt')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024      # 单张图片最大 20MB
    MAX_AVATAR_SIZE = 2 * 1024 * 1024           # 头像最大 2MB
    AVATAR_SIZE = 200                           # 头像统一裁成 200×200
    ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/bmp', 'image/webp'}
    DEFAULT_CONF = 0.25
    DEFAULT_IOU = 0.45
    USE_ROI = True                             # 先找手机区域再检测，减少背景误检
    MAX_SPOT_SIZE = 0.025                      # 亮点/暗点最大边长（占图片比例），过滤水珠/反光
    IMG_SIZE = 640
    TOKEN_MAX_AGE = 12 * 3600                  # 登录有效期 12 小时
    COOKIE_NAME = 'ps_token'
    CLASSES = [
        {'id': 0, 'name': 'scratch', 'cn': '划痕', 'color': '#ff7a45'},
        {'id': 1, 'name': 'crack', 'cn': '裂纹', 'color': '#ff4d4f'},
        {'id': 2, 'name': 'bright_spot', 'cn': '亮点', 'color': '#52c41a'},
        {'id': 3, 'name': 'dark_spot', 'cn': '暗点', 'color': '#722ed1'},
        {'id': 4, 'name': 'stain', 'cn': '污渍', 'color': '#faad14'},
        {'id': 5, 'name': 'edge_chip', 'cn': '边缘崩缺', 'color': '#13c2c2'},
    ]
    DEMO_USERS = [
        {'username': 'admin', 'password': '123456', 'role': 'admin'},
        {'username': 'user', 'password': '123456', 'role': 'user'},
    ]


def class_map():
    return {c['id']: c for c in Config.CLASSES}
