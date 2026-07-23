#!/usr/bin/env python3
"""
高危写入脚本的确认门禁与 dry-run。

执行顺序（强制）：parse_args → enforce_or_dry_run →（仅真实调用）再取 appkey / 发请求。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional


def add_safety_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印拟发请求 JSON，不发起 HTTP",
    )
    parser.add_argument(
        "--confirm",
        type=str,
        default=None,
        metavar="TOKEN",
        help="真实调用必填：YES；若同时使用 --physical 则必须为 PHYSICAL",
    )


def enforce_or_dry_run(
    args: argparse.Namespace,
    *,
    method: str,
    url: str,
    body: Optional[Dict[str, Any]] = None,
    require_physical_confirm: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    - --dry-run：stdout 输出 JSON 后 exit 0（不读 appkey）
    - 真实调用：校验 --confirm；失败 exit 2
    - extra：合并进 dry-run JSON（如 projectIdResolved=false）
    """
    if getattr(args, "dry_run", False):
        payload = {
            "dryRun": True,
            "method": method,
            "url": url,
            "body": body if body is not None else None,
        }
        if extra:
            payload.update(extra)
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(0)

    confirm = getattr(args, "confirm", None)
    expected = "PHYSICAL" if require_physical_confirm else "YES"
    if confirm != expected:
        if require_physical_confirm:
            msg = (
                "错误: 物理删除等高危操作必须显式传入 --confirm PHYSICAL"
                "（逻辑删除请用 --confirm YES；预览请求用 --dry-run）"
            )
        else:
            msg = (
                "错误: 写入类操作必须显式传入 --confirm YES"
                "（预览请求用 --dry-run；物理删除用 --confirm PHYSICAL）"
            )
        print(msg, file=sys.stderr)
        sys.exit(2)
