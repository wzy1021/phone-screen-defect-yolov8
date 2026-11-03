# -*- coding: utf-8 -*-
"""接口与页面测试（用假检测器，不依赖真实模型）。

运行：
    cd week11-14
    python -m unittest tests.test_api -v
"""
from __future__ import annotations

import io
import os
import tempfile
import unittest
import uuid
from pathlib import Path

from PIL import Image

from app import create_app
from app import db as dbm

BASE = Path(__file__).resolve().parent.parent


class FakeDetector:
    """固定返回两个缺陷，避免测试依赖 best.pt。"""
    loaded = True

    def detect(self, image_path, conf=None, iou=None, **kwargs):
        with Image.open(image_path) as im:
            img = im.convert('RGB')
        w, h = img.size
        return {
            'defects': [
                {'class_id': 0, 'class_name': 'scratch', 'class_cn': '划痕', 'color': '#ff7a45',
                 'conf': 0.91, 'x': 0.30, 'y': 0.40, 'w': 0.20, 'h': 0.10},
                {'class_id': 2, 'class_name': 'bright_spot', 'class_cn': '亮点', 'color': '#52c41a',
                 'conf': 0.76, 'x': 0.62, 'y': 0.55, 'w': 0.05, 'h': 0.05},
            ],
            'width': w, 'height': h, 'cost_ms': 12,
            'conf': 0.25 if conf is None else conf, 'iou': 0.45 if iou is None else iou,
            'annotated': img.copy(),
        }


def png_bytes(size=(200, 160), color=(30, 30, 40)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, 'PNG')
    buf.seek(0)
    return buf


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='ps_test_')
        cls.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret',
            'DB_PATH': os.path.join(cls.tmp, 'test.db'),
            'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
            'TOKEN_MAX_AGE': 3600,
        })
        cls.app.extensions['detector'] = FakeDetector()
        cls.client = cls.app.test_client()

    def setUp(self):
        self.client = self.app.test_client()      # 每个用例用新的 cookie，互不影响
        with self.app.app_context():
            db = dbm.get_db()
            db.execute('DELETE FROM t_defect')
            db.execute('DELETE FROM t_record')
            db.commit()
        self.clean_files()

    def tearDown(self):
        self.clean_files()

    @staticmethod
    def clean_files():
        # 只清测试自己产生的文件（img_ / res_img_ 开头），不要动演示数据
        for folder in (BASE / 'static' / 'uploads', BASE / 'static' / 'results'):
            if folder.exists():
                for f in folder.iterdir():
                    if f.is_file() and (f.name.startswith('img_') or f.name.startswith('res_img_')):
                        try:
                            f.unlink()
                        except OSError:
                            pass

    def login(self, username='admin', password='123456'):
        r = self.client.post('/api/login', json={'username': username, 'password': password})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        return r.get_json()['data']['token']

    def auth(self, token):
        return {'X-Token': token}

    # -------------------------------------------------------------- 登录
    def test_login_success_and_me(self):
        token = self.login()
        r = self.client.get('/api/me', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['data']['role'], 'admin')

    def test_login_wrong_password(self):
        r = self.client.post('/api/login', json={'username': 'admin', 'password': 'bad'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['code'], 400)

    def test_register_success_and_login(self):
        name = 'tester_' + uuid.uuid4().hex[:6]
        r = self.client.post('/api/register', json={
            'username': name, 'password': 'abc12345', 'confirm': 'abc12345'})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertEqual(r.get_json()['data']['role'], 'user')

        r = self.client.post('/api/login', json={'username': name, 'password': 'abc12345'})
        self.assertEqual(r.status_code, 200)
        token = r.get_json()['data']['token']
        r = self.client.get('/api/me', headers={'X-Token': token})
        self.assertEqual(r.get_json()['data']['username'], name)

    def test_register_validation(self):
        name = 'tester_' + uuid.uuid4().hex[:6]
        r = self.client.post('/api/register', json={
            'username': name, 'password': 'abc12345', 'confirm': 'abc12345'})
        self.assertEqual(r.status_code, 200)
        # 重复用户名
        r = self.client.post('/api/register', json={
            'username': name, 'password': 'abc12345', 'confirm': 'abc12345'})
        self.assertEqual(r.status_code, 400)
        # 密码太短
        r = self.client.post('/api/register', json={
            'username': 'short_' + uuid.uuid4().hex[:4], 'password': '123', 'confirm': '123'})
        self.assertEqual(r.status_code, 400)
        # 两次密码不一致
        r = self.client.post('/api/register', json={
            'username': 'diff_' + uuid.uuid4().hex[:4],
            'password': 'abc12345', 'confirm': 'abc12346'})
        self.assertEqual(r.status_code, 400)
        # 用户名不合法
        r = self.client.post('/api/register', json={
            'username': 'a', 'password': 'abc12345', 'confirm': 'abc12345'})
        self.assertEqual(r.status_code, 400)

    def test_register_page(self):
        r = self.client.get('/register')
        self.assertEqual(r.status_code, 200)
        self.assertIn('创建账号', r.get_data(as_text=True))

    def test_api_requires_login(self):
        r = self.client.get('/api/records')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()['code'], 401)

    def test_page_redirects_to_login(self):
        r = self.client.get('/detect')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers['Location'])

    # -------------------------------------------------------------- 个人资料 / 用户管理
    def _new_user(self):
        name = 'member_' + uuid.uuid4().hex[:6]
        r = self.client.post('/api/register', json={
            'username': name, 'password': 'abc12345', 'confirm': 'abc12345'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/api/login', json={'username': name, 'password': 'abc12345'})
        return name, r.get_json()['data']['token']

    def test_profile_nickname(self):
        name, token = self._new_user()
        r = self.client.get('/api/profile', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['data']['nickname'], name)

        r = self.client.put('/api/profile', json={'nickname': '质检小王'},
                            headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/api/profile', headers=self.auth(token))
        self.assertEqual(r.get_json()['data']['nickname'], '质检小王')

        r = self.client.put('/api/profile', json={'nickname': 'a'},
                            headers=self.auth(token))
        self.assertEqual(r.status_code, 400)

    def test_avatar_upload_and_reset(self):
        name, token = self._new_user()
        r = self.client.post('/api/profile/avatar',
                             data={'file': (png_bytes((200, 160)), 'avatar.png')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        url = r.get_json()['data']['avatar_url']
        self.assertTrue(url.startswith('/static/avatars/'))
        path = BASE / url.lstrip('/')
        self.assertTrue(path.exists())

        r = self.client.get('/api/profile', headers=self.auth(token))
        self.assertEqual(r.get_json()['data']['avatar_url'], url)

        r = self.client.delete('/api/profile/avatar', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(path.exists())

    def test_admin_user_list_permission(self):
        admin = self.login('admin')
        r = self.client.get('/api/users', headers=self.auth(admin))
        self.assertEqual(r.status_code, 200)
        rows = r.get_json()['data']
        names = {u['username'] for u in rows}
        self.assertIn('admin', names)
        self.assertIn('user', names)
        self.assertTrue(all('records' in u and 'defects' in u for u in rows))

        _, user_token = self._new_user()
        r = self.client.get('/api/users', headers=self.auth(user_token))
        self.assertEqual(r.status_code, 403)

    # -------------------------------------------------------------- 上传
    def test_upload_and_reject_bad_file(self):
        token = self.login()
        r = self.client.post('/api/upload',
                             data={'file': (png_bytes(), 'screen.png')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        path = r.get_json()['data']['image_path']
        self.assertTrue(path.startswith('uploads/'))
        self.assertTrue((BASE / 'static' / path).exists())

        r = self.client.post('/api/upload',
                             data={'file': (io.BytesIO(b'not an image'), 'a.txt')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    # -------------------------------------------------------------- 检测
    def test_detect_creates_record_and_result(self):
        token = self.login()
        r = self.client.post('/api/detect',
                             data={'file': (png_bytes(), 'screen.png'), 'conf': '0.3'},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()['data']
        self.assertEqual(data['total'], 2)
        self.assertAlmostEqual(data['conf'], 0.3)
        self.assertTrue((BASE / 'static' / data['result_image']).exists())
        rid = data['record_id']

        r = self.client.get(f'/api/records/{rid}', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        rec = r.get_json()['data']
        self.assertEqual(len(rec['defects']), 2)
        self.assertEqual(rec['defects'][0]['class_cn'], '划痕')

        r = self.client.get('/api/stats', headers=self.auth(token))
        stats = r.get_json()['data']
        self.assertEqual(stats['total_records'], 1)
        self.assertEqual(stats['total_defects'], 2)
        counts = {c['class_name']: c['count'] for c in stats['per_class']}
        self.assertEqual(counts['scratch'], 1)
        self.assertEqual(counts['bright_spot'], 1)

    def test_invalid_conf(self):
        token = self.login()
        r = self.client.post('/api/detect',
                             data={'file': (png_bytes(), 's.png'), 'conf': '1.5'},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    def test_csv_export(self):
        token = self.login()
        r = self.client.post('/api/detect',
                             data={'file': (png_bytes(), 's.png')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        rid = r.get_json()['data']['record_id']
        r = self.client.get(f'/api/records/{rid}/csv', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn('缺陷总数', body)
        self.assertIn('划痕', body)

    # -------------------------------------------------------------- 权限 / 删除
    def test_user_cannot_read_admin_record(self):
        admin_token = self.login('admin')
        r = self.client.post('/api/detect',
                             data={'file': (png_bytes(), 's.png')},
                             headers=self.auth(admin_token),
                             content_type='multipart/form-data')
        rid = r.get_json()['data']['record_id']
        user_token = self.login('user')
        r = self.client.get(f'/api/records/{rid}', headers=self.auth(user_token))
        self.assertEqual(r.status_code, 404)

        # 管理员能看到
        r = self.client.get(f'/api/records/{rid}', headers=self.auth(admin_token))
        self.assertEqual(r.status_code, 200)

    def test_delete_record_removes_files(self):
        token = self.login()
        r = self.client.post('/api/detect',
                             data={'file': (png_bytes(), 's.png')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        data = r.get_json()['data']
        rid = data['record_id']
        img = BASE / 'static' / data['image_path']
        res = BASE / 'static' / data['result_image']
        self.assertTrue(img.exists() and res.exists())

        r = self.client.delete(f'/api/records/{rid}', headers=self.auth(token))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(img.exists())
        self.assertFalse(res.exists())
        r = self.client.get(f'/api/records/{rid}', headers=self.auth(token))
        self.assertEqual(r.status_code, 404)

    def test_settings_permission_and_validation(self):
        user_token = self.login('user')
        r = self.client.put('/api/settings', json={'conf_threshold': 0.4},
                            headers=self.auth(user_token))
        self.assertEqual(r.status_code, 403)

        admin_token = self.login('admin')
        r = self.client.put('/api/settings', json={'conf_threshold': 0.4},
                            headers=self.auth(admin_token))
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.get_json()['data']['conf_threshold'], 0.4)

        r = self.client.put('/api/settings', json={'conf_threshold': 1.5},
                            headers=self.auth(admin_token))
        self.assertEqual(r.status_code, 400)

        # 恢复默认，避免影响其他测试
        self.client.put('/api/settings', json={'conf_threshold': 0.25},
                        headers=self.auth(admin_token))

    def test_pagination(self):
        token = self.login()
        for _ in range(3):
            self.client.post('/api/detect',
                             data={'file': (png_bytes(), 's.png')},
                             headers=self.auth(token),
                             content_type='multipart/form-data')
        r = self.client.get('/api/records?page=1&size=2', headers=self.auth(token))
        data = r.get_json()['data']
        self.assertEqual(data['total'], 3)
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(data['pages'], 2)
        self.assertEqual(data['items'][0]['id'] > data['items'][1]['id'], True)


if __name__ == '__main__':
    unittest.main()

