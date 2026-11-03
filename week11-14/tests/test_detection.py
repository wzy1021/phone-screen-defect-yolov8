# -*- coding: utf-8 -*-
"""真实模型检测测试：需要 models/best.pt。

运行：
    cd week11-14
    python -m unittest tests.test_detection -v
"""
from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

from app.detection import DefectDetector

BASE = Path(__file__).resolve().parent.parent
MODEL = BASE / 'models' / 'best.pt'
SAMPLE = BASE / 'datasets' / 'images' / 'test'


@unittest.skipUnless(MODEL.exists(), '还没有训练好的模型 models/best.pt')
class DetectorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.det = DefectDetector(str(MODEL))

    def test_detect_returns_boxes(self):
        sample = next(SAMPLE.glob('*.jpg'))
        out = self.det.detect(str(sample), conf=0.25)
        self.assertIn('defects', out)
        self.assertIn('annotated', out)
        self.assertGreater(out['cost_ms'], 0)
        img = out['annotated']
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, Image.open(sample).size)
        for d in out['defects']:
            self.assertGreaterEqual(d['conf'], 0.25)
            self.assertTrue(0 <= d['x'] <= 1 and 0 <= d['y'] <= 1)
            self.assertGreater(d['w'], 0)
            self.assertGreater(d['h'], 0)

    def test_confidence_threshold_effective(self):
        sample = next(SAMPLE.glob('*.jpg'))
        low = self.det.detect(str(sample), conf=0.05)
        high = self.det.detect(str(sample), conf=0.9)
        self.assertGreaterEqual(len(low['defects']), len(high['defects']))


if __name__ == '__main__':
    unittest.main()
