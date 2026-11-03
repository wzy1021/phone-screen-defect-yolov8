# -*- coding: utf-8 -*-
"""登录认证：密码哈希、签名 token、登录校验装饰器。"""
from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
from functools import wraps
from urllib.parse import urlparse

from flask import (current_app, g, jsonify, redirect, request, url_for)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from . import db


# ------------------------------------------------------------------ 密码
def hash_password(password: str, salt: str | None = None) -> str:
    """PBKDF2-SHA256 加盐哈希，格式：pbkdf2_sha256$迭代次数$盐$摘要。"""
    salt = salt or secrets.token_hex(16)
    iterations = 120000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                 salt.encode('utf-8'), iterations)
    return f'pbkdf2_sha256${iterations}${salt}${digest.hex()}'


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, expected = stored.split('$')
        if algo != 'pbkdf2_sha256':
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                     salt.encode('utf-8'), int(iterations))
        return secrets.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------------ token
def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='ps-login')


def issue_token(user: dict) -> str:
    return _serializer().dumps({'uid': user['id'], 'username': user['username'],
                                'role': user['role']})


def read_token(token: str):
    if not token:
        return None
    try:
        return _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE'])
    except (SignatureExpired, BadSignature):
        return None


def get_current_user():
    """依次从 X-Token、Authorization、Cookie 中取 token，再查用户。"""
    token = request.headers.get('X-Token', '') or ''
    if not token:
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:].strip()
    if not token:
        token = request.cookies.get(current_app.config['COOKIE_NAME'], '')
    payload = read_token(token)
    if not payload:
        return None
    user = db.get_user_by_id(int(payload.get('uid', 0)))
    if not user or user['username'] != payload.get('username'):
        return None
    return user


def set_login_cookie(response, token: str):
    response.set_cookie(current_app.config['COOKIE_NAME'], token,
                        max_age=current_app.config['TOKEN_MAX_AGE'],
                        httponly=True, samesite='Lax')
    return response


def login_user(username: str, password: str):
    """校验用户名密码，成功返回 (user, token)，失败返回 (None, None)。"""
    user = db.get_user_by_name(username)
    if not user or not verify_password(password, user['password']):
        return None, None
    return user, issue_token(user)


USERNAME_RE = re.compile(r'^[A-Za-z0-9_\u4e00-\u9fa5]{2,20}$')
NICKNAME_RE = re.compile(r'^[A-Za-z0-9_\u4e00-\u9fa5· ]{2,16}$')


def normalize_nickname(nickname: str):
    """昵称校验：2–16 位，支持中文/字母/数字/下划线/点/空格，返回 (值, 错误)。"""
    nickname = ' '.join((nickname or '').split())
    if not NICKNAME_RE.match(nickname):
        return None, '昵称需为 2–16 位中文、字母、数字、下划线或空格'
    return nickname, None


def register_user(username: str, password: str, confirm: str | None = None):
    """注册新用户，返回 (user, error)。只允许注册普通用户，管理员仍由初始化脚本创建。"""
    username = (username or '').strip()
    password = password or ''
    if not USERNAME_RE.match(username):
        return None, '用户名需为 2–20 位中文、字母、数字或下划线'
    if len(password) < 6:
        return None, '密码至少 6 位'
    if len(password) > 64:
        return None, '密码不能超过 64 位'
    if confirm is not None and password != confirm:
        return None, '两次输入的密码不一致'
    if db.get_user_by_name(username):
        return None, '用户名已被注册，请换一个'
    try:
        uid = db.create_user(username, hash_password(password), 'user')
    except sqlite3.IntegrityError:
        return None, '用户名已被注册，请换一个'
    return db.get_user_by_id(uid), None


# ------------------------------------------------------------------ 装饰器
def api_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify(code=401, message='请先登录', data=None), 401
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def api_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify(code=401, message='请先登录', data=None), 401
        if user['role'] != 'admin':
            return jsonify(code=403, message='需要管理员权限', data=None), 403
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def page_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('views.login', next=request.path))
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def page_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('views.login', next=request.path))
        if user['role'] != 'admin':
            from flask import abort
            abort(403)
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def safe_next(target: str | None, default: str = '/detect') -> str:
    """只允许跳回站内地址，防止 ?next= 被拿来做跳转攻击。"""
    if not target:
        return default
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith('/'):
        return default
    return target
