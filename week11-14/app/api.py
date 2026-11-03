# -*- coding: utf-8 -*-
"""后台接口（REST API）。

返回格式统一为：
    {"code": 200, "message": "ok", "data": {...}}
出错时 HTTP 状态码和 code 一致。
"""
from __future__ import annotations

import csv
import io
import os
import re
import time
import traceback

from flask import Blueprint, Response, current_app, g, jsonify, request

from config import Config, class_map
from . import auth, db
from .detection import ModelNotFoundError, get_detector
from .utils import (ImageValidationError, delete_static_file, exists_in_static,
                    save_avatar, save_upload, static_abs)

bp = Blueprint('api', __name__)

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def ok(data=None, message='ok'):
    return jsonify(code=200, message=message, data=data)


def err(code: int, message: str):
    return jsonify(code=code, message=message, data=None), code


def _parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value):
    if value and DATE_RE.match(value):
        return value
    return None


def _visible_user(user):
    """管理员能看所有人的记录，普通用户只看自己的。"""
    return None if user['role'] == 'admin' else user['id']


def _decorate(rec: dict) -> dict:
    cmap = class_map()
    for d in rec.get('defects', []):
        info = cmap.get(d['class_id'], {})
        d['class_cn'] = info.get('cn', d['class_name'])
        d['color'] = info.get('color', '#666666')
    if rec.get('image_path'):
        rec['image_url'] = f"/static/{rec['image_path']}"
    if rec.get('result_path'):
        rec['result_url'] = f"/static/{rec['result_path']}"
    return rec


def _settings_payload() -> dict:
    s = db.get_settings()
    det = current_app.extensions.get('detector')
    return {
        'conf_threshold': _parse_float(s.get('conf_threshold'), Config.DEFAULT_CONF),
        'iou_threshold': _parse_float(s.get('iou_threshold'), Config.DEFAULT_IOU),
        'model_name': s.get('model_name', 'best.pt'),
        'model_loaded': bool(det and det.loaded),
        'classes': Config.CLASSES,
    }


# ------------------------------------------------------------------ 登录
@bp.post('/login')
def login():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return err(400, '请输入用户名和密码')
    user, token = auth.login_user(username, password)
    if not user:
        return err(400, '用户名或密码错误')
    resp = ok({'token': token, 'username': user['username'],
               'role': user['role'], 'user_id': user['id']})
    return auth.set_login_cookie(resp, token)


@bp.post('/logout')
def logout():
    resp = ok(None, '已退出登录')
    resp.delete_cookie(current_app.config['COOKIE_NAME'])
    return resp


@bp.post('/register')
def register():
    data = request.get_json(silent=True) or request.form
    user, error = auth.register_user(
        data.get('username') or '',
        data.get('password') or '',
        data.get('confirm') if data.get('confirm') is not None else None,
    )
    if error:
        return err(400, error)
    return ok({'id': user['id'], 'username': user['username'], 'role': user['role']},
              '注册成功，请登录')


@bp.get('/me')
@auth.api_login_required
def me():
    u = g.user
    return ok({'id': u['id'], 'username': u['username'],
               'nickname': u.get('nickname') or u['username'],
               'role': u['role']})


@bp.get('/profile')
@auth.api_login_required
def get_profile():
    u = g.user
    summary = db.get_user_summary(u['id'])
    return ok({
        'id': u['id'],
        'username': u['username'],
        'nickname': u.get('nickname') or u['username'],
        'role': u['role'],
        'created_at': u['created_at'],
        'avatar_url': f"/static/{u['avatar']}" if u.get('avatar') else None,
        'records': summary['records'],
        'defects': summary['defects'],
        'last_at': summary['last_at'],
    })


@bp.put('/profile')
@auth.api_login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    nickname, error = auth.normalize_nickname(data.get('nickname'))
    if error:
        return err(400, error)
    db.update_user_profile(g.user['id'], nickname=nickname)
    return ok({'nickname': nickname}, '昵称已保存')


@bp.post('/profile/avatar')
@auth.api_login_required
def update_avatar():
    if 'file' not in request.files:
        return err(400, '没有收到头像文件')
    try:
        info = save_avatar(request.files['file'], g.user['id'])
    except ImageValidationError as exc:
        return err(400, str(exc))
    old = g.user.get('avatar')
    db.update_user_profile(g.user['id'], avatar=info['avatar_path'])
    if old and old != info['avatar_path']:
        delete_static_file(old)
    return ok({'avatar_url': f"/static/{info['avatar_path']}"}, '头像已更新')


@bp.delete('/profile/avatar')
@auth.api_login_required
def delete_avatar():
    old = g.user.get('avatar')
    if old:
        delete_static_file(old)
        db.update_user_profile(g.user['id'], avatar=None)
    return ok({'avatar_url': None}, '已恢复默认头像')


@bp.get('/users')
@auth.api_admin_required
def users():
    rows = db.list_users()
    for u in rows:
        u['avatar_url'] = f"/static/{u['avatar']}" if u.get('avatar') else None
    return ok(rows)


# ------------------------------------------------------------------ 上传 / 检测
@bp.post('/upload')
@auth.api_login_required
def upload():
    if 'file' not in request.files:
        return err(400, '没有收到文件，请用 file 字段上传')
    try:
        info = save_upload(request.files['file'])
    except ImageValidationError as exc:
        return err(400, str(exc))
    return ok({'image_path': info['image_path'], 'url': f"/static/{info['image_path']}",
               'width': info['width'], 'height': info['height']})


@bp.post('/detect')
@auth.api_login_required
def detect():
    user = g.user
    payload = request.get_json(silent=True) or {}
    conf = _parse_float(request.form.get('conf') or payload.get('conf'), None)
    use_roi = str(request.form.get('roi', payload.get('roi', '1'))).lower() not in ('0', 'false', 'off')
    image_path = None
    keep_file = False

    if 'file' in request.files and request.files['file'].filename:
        try:
            up = save_upload(request.files['file'])
        except ImageValidationError as exc:
            return err(400, str(exc))
        image_path = up['image_path']
        keep_file = True
    else:
        rel = (payload.get('image_path') or request.form.get('image_path') or '').strip()
        if not rel:
            return err(400, '请上传图片或提供 image_path')
        if not rel.startswith('uploads/') or not exists_in_static(rel):
            return err(400, '图片路径无效')
        image_path = rel

    if conf is None:
        conf = _parse_float(db.get_setting('conf_threshold'), Config.DEFAULT_CONF)
    if conf is None or not (0.01 <= conf <= 0.99):
        return err(400, '置信度阈值必须在 0.01 到 0.99 之间')
    iou = _parse_float(db.get_setting('iou_threshold'), Config.DEFAULT_IOU)

    abs_path = static_abs(image_path)
    t0 = time.perf_counter()
    try:
        det = get_detector()
        result = det.detect(abs_path, conf=conf, iou=iou, use_roi=use_roi)
    except ModelNotFoundError as exc:
        return err(503, str(exc))
    except Exception as exc:           # 模型或图片异常，记录失败原因但仍返回友好提示
        traceback.print_exc()
        cost = int((time.perf_counter() - t0) * 1000)
        rid = db.create_record(user['id'], image_path, None, 0, 'failed', conf, cost, [])
        return err(500, f'检测失败（记录 #{rid}）：{exc}')

    # 保存画好框的结果图
    stem = os.path.splitext(os.path.basename(image_path))[0]
    result_rel = f'results/res_{stem}.jpg'
    result_abs = os.path.join(current_app.config['RESULT_DIR'], f'res_{stem}.jpg')
    os.makedirs(os.path.dirname(result_abs), exist_ok=True)
    result['annotated'].save(result_abs, 'JPEG', quality=92)

    defects = result['defects']
    rid = db.create_record(user['id'], image_path, result_rel, len(defects),
                           'done', conf, result['cost_ms'], defects)
    record = db.get_record(rid, user_id=user['id'], is_admin=True)
    _decorate(record)
    data = {
        'record_id': rid,
        'total': len(defects),
        'image_path': image_path,
        'result_image': result_rel,
        'result_url': f'/static/{result_rel}',
        'conf': conf,
        'cost_ms': result['cost_ms'],
        'width': result['width'],
        'height': result['height'],
        'defects': record['defects'],
    }
    return ok(data, '检测完成')


# ------------------------------------------------------------------ 记录
@bp.get('/records')
@auth.api_login_required
def records():
    page = int(_parse_float(request.args.get('page'), 1))
    size = int(_parse_float(request.args.get('size'), 10))
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))
    has_defect = request.args.get('has_defect')
    has_defect = int(has_defect) if has_defect in ('0', '1') else None

    target = _visible_user(g.user)
    if g.user['role'] == 'admin' and request.args.get('user_id', '').isdigit():
        target = int(request.args['user_id'])
    data = db.list_records(target, page, size, start, end, has_defect)
    for item in data['items']:
        item['image_url'] = f"/static/{item['image_path']}"
        if item.get('result_path'):
            item['result_url'] = f"/static/{item['result_path']}"
    data['pages'] = max(1, (data['total'] + data['size'] - 1) // data['size'])
    return ok(data)


@bp.get('/records/<int:rid>')
@auth.api_login_required
def record_detail(rid):
    rec = db.get_record(rid, user_id=g.user['id'], is_admin=g.user['role'] == 'admin')
    if not rec:
        return err(404, '记录不存在')
    return ok(_decorate(rec))


@bp.delete('/records/<int:rid>')
@auth.api_login_required
def record_delete(rid):
    rec = db.delete_record(rid, user_id=g.user['id'], is_admin=g.user['role'] == 'admin')
    if not rec:
        return err(404, '记录不存在')
    delete_static_file(rec['image_path'])
    delete_static_file(rec['result_path'])
    return ok({'deleted': rid}, '已删除')


@bp.get('/records/<int:rid>/csv')
@auth.api_login_required
def record_csv(rid):
    rec = db.get_record(rid, user_id=g.user['id'], is_admin=g.user['role'] == 'admin')
    if not rec:
        return err(404, '记录不存在')
    rec = _decorate(rec)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['检测编号', rid])
    writer.writerow(['检测时间', rec['created_at']])
    writer.writerow(['检测人', rec['username']])
    writer.writerow(['置信度阈值', rec['conf']])
    writer.writerow(['缺陷总数', rec['total']])
    writer.writerow([])
    writer.writerow(['序号', '类别', '中文名', '置信度', '中心x', '中心y', '宽', '高'])
    for i, d in enumerate(rec['defects'], 1):
        writer.writerow([i, d['class_name'], d['class_cn'], d['conf'],
                         d['x'], d['y'], d['w'], d['h']])
    body = '\ufeff' + buf.getvalue()      # BOM，让 Excel 正确显示中文
    resp = Response(body, mimetype='text/csv; charset=utf-8')
    resp.headers['Content-Disposition'] = f'attachment; filename=record_{rid}.csv'
    return resp


# ------------------------------------------------------------------ 统计 / 参数
@bp.get('/stats')
@auth.api_login_required
def stats():
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))
    return ok(db.get_stats(_visible_user(g.user), start, end))


@bp.get('/settings')
@auth.api_login_required
def get_settings():
    return ok(_settings_payload())


@bp.put('/settings')
@auth.api_admin_required
def update_settings():
    data = request.get_json(silent=True) or {}
    conf = _parse_float(data.get('conf_threshold'), None)
    iou = _parse_float(data.get('iou_threshold'), None)
    if conf is not None and not (0.01 <= conf <= 0.99):
        return err(400, '置信度阈值必须在 0.01 到 0.99 之间')
    if iou is not None and not (0.05 <= iou <= 0.95):
        return err(400, 'IOU 阈值必须在 0.05 到 0.95 之间')
    if conf is None and iou is None:
        return err(400, '没有要修改的参数')
    if conf is not None:
        db.set_setting('conf_threshold', round(conf, 4))
    if iou is not None:
        db.set_setting('iou_threshold', round(iou, 4))
    return ok(_settings_payload(), '参数已保存')


@bp.get('/health')
def health():
    model_path = current_app.config['MODEL_PATH']
    return ok({'status': 'ok',
               'model_exists': os.path.exists(model_path),
               'model_loaded': bool(current_app.extensions.get('detector') and
                                    current_app.extensions['detector'].loaded),
               'database': os.path.basename(current_app.config['DB_PATH']),
               'version': '1.0'})
