#!/usr/bin/env python3
"""中文缺参提示的 ArgumentParser（Agent 可读 stderr 后补齐参数重试）。"""

from __future__ import annotations

import argparse
import sys


class DocdbArgumentParser(argparse.ArgumentParser):
    """
    缺参/非法参数时打印中文 hint，exit 2。
    hint：多行说明（缺什么、怎么传、单行绝对路径示例）。
    """

    def __init__(self, *args, hint: str = "", **kwargs):
        self._hint = (hint or "").strip()
        kwargs.setdefault("add_help", True)
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:  # type: ignore[override]
        parts = [f"错误: 缺少或无效的参数（{message}）。"]
        if self._hint:
            parts.append(self._hint)
        print("\n".join(parts), file=sys.stderr)
        sys.exit(2)
