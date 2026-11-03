# -*- coding: utf-8 -*-
"""数据集完整性测试：图片与标签一一对应、坐标合法、类别齐全。

运行：
    cd week11-14
    python -m unittest tests.test_dataset -v
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / 'datasets'
STATS = DATA / 'dataset_stats.json'


@unittest.skipUnless(STATS.exists(), '还没有生成数据集，先运行 datasets/gen_dataset.py')
class DatasetTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stats = json.loads(STATS.read_text(encoding='utf-8'))
        cls.classes = [c[0] for c in cls.stats['classes']]

    def test_split_counts(self):
        for split in ('train', 'val', 'test'):
            images = list((DATA / 'images' / split).glob('*.jpg'))
            labels = list((DATA / 'labels' / split).glob('*.txt'))
            self.assertEqual(len(images), self.stats[split]['images'], split)
            self.assertEqual(len(labels), len(images), split)

    def test_label_files_valid(self):
        total = 0
        for split in ('train', 'val', 'test'):
            for lbl in (DATA / 'labels' / split).glob('*.txt'):
                for lineno, line in enumerate(lbl.read_text(encoding='utf-8').splitlines(), 1):
                    parts = line.split()
                    self.assertEqual(len(parts), 5, f'{lbl}:{lineno}')
                    cid = int(parts[0])
                    self.assertIn(cid, range(len(self.classes)), f'{lbl}:{lineno}')
                    cx, cy, w, h = map(float, parts[1:])
                    for v in (cx, cy, w, h):
                        self.assertGreaterEqual(v, 0.0, f'{lbl}:{lineno}')
                        self.assertLessEqual(v, 1.0, f'{lbl}:{lineno}')
                    self.assertGreater(w, 0.005, f'{lbl}:{lineno}')
                    self.assertGreater(h, 0.005, f'{lbl}:{lineno}')
                    total += 1
        self.assertGreater(total, 1000)

    def test_every_image_has_label(self):
        for split in ('train', 'val', 'test'):
            for img in (DATA / 'images' / split).glob('*.jpg'):
                lbl = DATA / 'labels' / split / (img.stem + '.txt')
                self.assertTrue(lbl.exists(), f'缺少标签：{lbl}')

    def test_all_classes_have_enough_samples(self):
        for split in ('train', 'val', 'test'):
            for name in self.classes:
                self.assertGreaterEqual(self.stats[split]['classes'][name], 20,
                                        f'{split} 中 {name} 样本不足')

    def test_image_size(self):
        samples = list((DATA / 'images' / 'train').glob('*.jpg'))[:8]
        self.assertTrue(samples)
        for p in samples:
            with Image.open(p) as im:
                self.assertEqual(im.size, (640, 640), p.name)

    def test_data_yaml(self):
        text = (DATA / 'data.yaml').read_text(encoding='utf-8')
        self.assertIn('nc: 6', text)
        for name in self.classes:
            self.assertIn(name, text)
        for split in ('images/train', 'images/val', 'images/test'):
            self.assertIn(split, text)


if __name__ == '__main__':
    unittest.main()
