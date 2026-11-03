# -*- coding: utf-8 -*-
"""页面路由。"""
from __future__ import annotations

from flask import (Blueprint, abort, current_app, g, redirect, render_template,
                   request, url_for)

from config import Config, class_map
from . import auth, db

bp = Blueprint('views', __name__)


@bp.app_context_processor
def inject_globals():
    return {
        'classes': Config.CLASSES,
        'current_user': getattr(g, 'user', None),
        'app_name': '屏幕缺陷检测',
    }


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if auth.get_current_user():
        return redirect(url_for('views.detect'))
    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user, token = auth.login_user(username, password)
        if not user:
            error = '用户名或密码错误，请重试'
        else:
            target = auth.safe_next(request.args.get('next') or request.form.get('next'))
            resp = redirect(target)
            return auth.set_login_cookie(resp, token)
    return render_template('login.html', error=error,
                           success='注册成功，请用新账号登录' if request.args.get('registered') else None,
                           next=request.args.get('next', ''))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if auth.get_current_user():
        return redirect(url_for('views.detect'))
    error = None
    form = {'username': ''}
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        confirm = request.form.get('confirm') or ''
        user, error = auth.register_user(username, password, confirm)
        if user:
            return redirect(url_for('views.login', registered=1))
        form['username'] = username
    return render_template('register.html', error=error, form=form)


@bp.get('/logout')
def logout():
    resp = redirect(url_for('views.login'))
    resp.delete_cookie(current_app.config['COOKIE_NAME'])
    return resp


@bp.get('/')
def index():
    return redirect(url_for('views.detect'))


@bp.get('/detect')
@auth.page_login_required
def detect():
    conf = db.get_setting('conf_threshold', str(Config.DEFAULT_CONF))
    iou = db.get_setting('iou_threshold', str(Config.DEFAULT_IOU))
    return render_template('detect.html', active='detect',
                           conf=float(conf), iou=float(iou))


@bp.get('/result/<int:rid>')
@auth.page_login_required
def result(rid):
    rec = db.get_record(rid, user_id=g.user['id'], is_admin=g.user['role'] == 'admin')
    if not rec:
        abort(404)
    cmap = class_map()
    counts = {}
    for d in rec['defects']:
        info = cmap.get(d['class_id'], {})
        d['class_cn'] = info.get('cn', d['class_name'])
        d['color'] = info.get('color', '#666666')
        counts[d['class_id']] = counts.get(d['class_id'], 0) + 1
    rec['class_counts'] = counts
    return render_template('result.html', active='history', record=rec)


@bp.get('/history')
@auth.page_login_required
def history():
    users = db.list_users() if g.user['role'] == 'admin' else []
    selected = request.args.get('user_id', type=int)
    return render_template('history.html', active='history', users=users,
                           selected_user=selected)


@bp.get('/profile')
@auth.page_login_required
def profile():
    summary = db.get_user_summary(g.user['id'])
    return render_template('profile.html', active='profile', summary=summary)


@bp.get('/admin/users')
@auth.page_admin_required
def admin_users():
    return render_template('admin_users.html', active='users')


@bp.get('/stats')
@auth.page_login_required
def stats():
    return render_template('stats.html', active='stats')
