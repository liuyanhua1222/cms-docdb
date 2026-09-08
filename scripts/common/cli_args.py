#!/usr/bin/env python3
"""中文缺参提示的 ArgumentParser（Agent 可读 stderr 后补齐参数重试）。"""

from __future__ import annotations

import argparse
import sys


APP_KEY_HELP = "当前用户的企业知识库 AppKey（可选）；未传时由脚本自行获取"


def add_compatible_app_key_argument(parser: argparse.ArgumentParser) -> None:
    """注册非必填 --app-key（兼容 --app_key / --appKey）。可重复调用。"""
    if "--app-key" in getattr(parser, "_option_string_actions", {}):
        return
    parser.add_argument(
        "--app-key",
        "--app_key",
        "--appKey",
        dest="app_key",
        default=None,
        metavar="APP_KEY",
        help=APP_KEY_HELP,
    )


def _stash_cli_app_key(namespace: argparse.Namespace) -> None:
    from docdb_open_api import stash_cli_app_key

    stash_cli_app_key(getattr(namespace, "app_key", None))


class DocdbArgumentParser(argparse.ArgumentParser):
    """
    缺参/非法参数时打印中文 hint，exit 2。
    hint：多行说明（缺什么、怎么传、业务参数示例）。
    自动注册可选 --app-key；解析时只暂存，不选源、不发请求。
    """

    def __init__(self, *args, hint: str = "", **kwargs):
        self._hint = (hint or "").strip()
        kwargs.setdefault("add_help", True)
        super().__init__(*args, **kwargs)
        add_compatible_app_key_argument(self)

    def error(self, message: str) -> None:  # type: ignore[override]
        parts = [f"错误: 缺少或无效的参数（{message}）。"]
        if self._hint:
            parts.append(self._hint)
        print("\n".join(parts), file=sys.stderr)
        sys.exit(2)

    def parse_known_args(self, args=None, namespace=None):  # type: ignore[override]
        ns, unknown = super().parse_known_args(args, namespace)
        _stash_cli_app_key(ns)
        return ns, unknown
