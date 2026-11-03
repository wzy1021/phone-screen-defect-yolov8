# -*- coding: utf-8 -*-
"""运行全部自动化测试，并把干净的测试输出写到 docs/test_output.txt。"""
from __future__ import annotations

import io
import re
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(str(BASE / 'tests'), pattern='test_*.py', top_level_dir=str(BASE))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    text = stream.getvalue()
    # 去掉 ResourceWarning 之类的杂音和用例后面的模块路径，保留可读的用例名
    lines = []
    for line in text.splitlines():
        if line.startswith('ResourceWarning') or line.startswith('  self.'):
            continue
        line = re.sub(r'\s*\([\w.]+\)', '', line).rstrip()
        lines.append(line)
    clean = '\n'.join(lines).strip() + '\n'
    out = BASE / 'docs' / 'test_output.txt'
    out.write_text(clean, encoding='utf-8')
    print(clean)
    print('written:', out)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
