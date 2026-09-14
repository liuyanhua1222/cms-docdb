#!/usr/bin/env python3
"""
outsend / status 占位脚本

后台有外发（OutSend）能力，但 OpenAPI 尚未开放。
本脚本固定返回 blocked 状态并以 exit 2 退出，防止 Agent 伪造成功。

见 references/outsend/README.md
"""

import json
import sys

PAYLOAD = {
    "resultCode": 0,
    "resultMsg": "OutSend OpenAPI 未开放，待产品确认范围",
    "data": {"status": "blocked_pending_product"},
}


def main():
    print(json.dumps(PAYLOAD, ensure_ascii=False))
    sys.exit(2)


if __name__ == "__main__":
    main()
