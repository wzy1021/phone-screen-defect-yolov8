# -*- coding: utf-8 -*-
"""Flask 应用工厂。"""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from config import BASE_DIR, Config


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / 'templates'),
        static_folder=str(BASE_DIR / 'static'),
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # 目录准备好，避免第一次上传时找不到文件夹
    for key in ('UPLOAD_DIR', 'RESULT_DIR', 'AVATAR_DIR'):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)
    Path(app.config['DB_PATH']).parent.mkdir(parents=True, exist_ok=True)

    app.json.ensure_ascii = False
    app.extensions['detector'] = None

    from .db import init_app as init_db_app
    init_db_app(app)

    from .views import bp as views_bp
    from .api import bp as api_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify(code=403, message='需要管理员权限', data=None), 403
        return render_template('404.html', code=403, message='没有权限访问这个页面'), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify(code=404, message='接口或记录不存在', data=None), 404
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def too_large(e):
        msg = '图片超过 20MB，请压缩后再上传'
        if request.path.startswith('/api/'):
            return jsonify(code=413, message=msg, data=None), 413
        return msg, 413

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api/'):
            return jsonify(code=500, message='服务器出错，请稍后再试', data=None), 500
        return render_template('404.html', message='服务器开小差了，请稍后再试'), 500

    return app
