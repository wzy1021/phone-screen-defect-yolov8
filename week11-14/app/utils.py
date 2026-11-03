# -*- coding: utf-8 -*-
"""文件相关的工具函数：校验、保存上传图片、删除文件。"""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError


class ImageValidationError(ValueError):
    pass


def allowed_ext(filename: str) -> bool:
    return Path(filename or '').suffix.lower() in current_app.config['ALLOWED_EXT']


def unique_name(prefix: str = 'img', ext: str = '.jpg') -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{ts}_{secrets.token_hex(4)}{ext}'


_RESULT_HASH_CACHE: dict[str, tuple[float, int]] = {}


def _dhash(img: Image.Image) -> int:
    """64 位差值哈希，用来判断两张图是不是同一张（缩放/压缩不影响）。"""
    small = img.convert('L').resize((9, 8), Image.LANCZOS)
    px = list(small.getdata())
    bits = 0
    for y in range(8):
        row = y * 9
        for x in range(8):
            bits = (bits << 1) | (1 if px[row + x] > px[row + x + 1] else 0)
    return bits


def looks_like_result_image(img: Image.Image, max_distance: int = 3) -> bool:
    """判断上传的是不是系统自己生成的结果图（带框/文字），防止结果图回流。

    没有缺陷的检测结果图和原图几乎一样，这种情况不能拦；只有结果图
    和它的原图确实不同（说明画了框）时，才判定为“结果图回流”。
    """
    result_dir = Path(current_app.config['RESULT_DIR'])
    if not result_dir.is_dir():
        return False

    source_map = {}
    try:
        conn = sqlite3.connect(current_app.config['DB_PATH'])
        for rp, ip in conn.execute(
                'SELECT result_path, image_path FROM t_record '
                'WHERE result_path IS NOT NULL AND total > 0 ORDER BY id DESC LIMIT 300'):
            source_map[rp] = ip
        conn.close()
    except sqlite3.Error:
        pass

    target = _dhash(img)
    files = sorted(result_dir.glob('*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)[:300]
    for path in files:
        try:
            mtime = path.stat().st_mtime
            cached = _RESULT_HASH_CACHE.get(str(path))
            if cached is None or cached[0] != mtime:
                with Image.open(path) as rim:
                    h = _dhash(rim)
                _RESULT_HASH_CACHE[str(path)] = (mtime, h)
            else:
                h = cached[1]
            if bin(target ^ h).count('1') > max_distance:
                continue

            src_rel = source_map.get('results/' + path.name)
            if src_rel:
                src_abs = Path(current_app.static_folder) / src_rel
                if src_abs.is_file():
                    with Image.open(src_abs) as sim:
                        src_hash = _dhash(sim)
                    if bin(src_hash ^ h).count('1') <= max_distance:
                        # 结果图和原图一样，说明图上没有框，不算回流
                        continue
            return True
        except OSError:
            continue
    return False


def save_upload(file_storage) -> dict:
    """校验并保存上传的图片，统一转成 RGB JPEG，去掉 EXIF 方向信息。"""
    filename = file_storage.filename or ''
    if not allowed_ext(filename):
        raise ImageValidationError('图片格式不支持，请上传 jpg / png / bmp / webp')
    raw = file_storage.read()
    if not raw:
        raise ImageValidationError('图片是空的')
    if len(raw) > current_app.config['MAX_CONTENT_LENGTH']:
        raise ImageValidationError('图片超过 20MB')

    try:
        with Image.open(BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im)
            im = im.convert('RGB')
            width, height = im.size
            if width < 32 or height < 32:
                raise ImageValidationError('图片尺寸太小（至少 32×32）')
            if looks_like_result_image(im):
                raise ImageValidationError(
                    '这张图片是系统生成的结果图（已经画了检测框），请上传原始照片，不要上传结果图')
            # 太长的边缩到 3000 像素，避免超大图拖慢检测
            if max(width, height) > 3000:
                im.thumbnail((3000, 3000), Image.LANCZOS)
                width, height = im.size
            name = unique_name('img')
            upload_dir = Path(current_app.config['UPLOAD_DIR'])
            upload_dir.mkdir(parents=True, exist_ok=True)
            abs_path = upload_dir / name
            im.save(abs_path, 'JPEG', quality=94)
    except UnidentifiedImageError:
        raise ImageValidationError('这个文件不是有效的图片')
    except ImageValidationError:
        raise
    except OSError as exc:
        raise ImageValidationError(f'图片读取失败：{exc}')

    return {'filename': name, 'image_path': f'uploads/{name}',
            'abs_path': str(abs_path), 'width': width, 'height': height}


def save_avatar(file_storage, user_id: int) -> dict:
    """保存头像：限制 2MB、至少 64×64，居中裁成正方形并缩放到 200×200。"""
    filename = file_storage.filename or ''
    ext = Path(filename).suffix.lower()
    if ext not in current_app.config['ALLOWED_EXT']:
        raise ImageValidationError('头像只支持 jpg / png / bmp / webp')
    raw = file_storage.read()
    if not raw:
        raise ImageValidationError('头像文件是空的')
    if len(raw) > current_app.config['MAX_AVATAR_SIZE']:
        raise ImageValidationError('头像不能超过 2MB')
    try:
        with Image.open(BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im).convert('RGB')
            if min(im.size) < 64:
                raise ImageValidationError('头像尺寸太小，至少 64×64')
            size = current_app.config['AVATAR_SIZE']
            im = ImageOps.fit(im, (size, size), method=Image.LANCZOS,
                              centering=(0.5, 0.5))
            name = f'av_{user_id}_{secrets.token_hex(4)}.jpg'
            avatar_dir = Path(current_app.config['AVATAR_DIR'])
            avatar_dir.mkdir(parents=True, exist_ok=True)
            abs_path = avatar_dir / name
            im.save(abs_path, 'JPEG', quality=90)
    except UnidentifiedImageError:
        raise ImageValidationError('这个文件不是有效的图片')
    except ImageValidationError:
        raise
    except OSError as exc:
        raise ImageValidationError(f'头像读取失败：{exc}')
    return {'avatar_path': f'avatars/{name}', 'abs_path': str(abs_path)}


def static_abs(rel_path: str) -> str:
    """把数据库里的相对路径（uploads/xxx.jpg）换成绝对路径。"""
    return str(Path(current_app.static_folder) / rel_path)


def exists_in_static(rel_path: str) -> bool:
    if not rel_path:
        return False
    try:
        p = Path(static_abs(rel_path)).resolve()
        root = Path(current_app.static_folder).resolve()
        return root in p.parents and p.is_file()
    except (OSError, ValueError):
        return False


def delete_static_file(rel_path: str):
    """删除 static 下的文件，做了目录越界保护。"""
    if not rel_path:
        return
    try:
        root = Path(current_app.static_folder).resolve()
        path = (root / rel_path).resolve()
        if root in path.parents and path.is_file():
            os.remove(path)
    except OSError:
        pass
