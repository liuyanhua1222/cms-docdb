#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用通道路由：用户话术 → appCode / product_label

映射以 t_doc_app 为准：
  法务文档 / 打开法务…     → fw_doc
  资料库 / 康哲资料库 / 德镁资料库 / 文档数据库 → kz_doc
  康哲知识库 / 德镁知识库  → kz_knowledge_base
  玄关知识库              → kz_doc
  裸「知识库」            → app_code=null（须与企业 listAll 求交后再定）

冲突处理：
  - 「法务」「资料库」不作裸子串抢通道（避免「知识库里搜合同法务」误进 fw_doc）
  - 品牌「xx知识库」优先于句中出现的「资料库」目录名等
"""

import json
import re
import sys

# (priority, pattern, app_code, product_label)
# lower priority number = higher precedence
_RULES = [
    # —— 明确产品名 ——
    (5, r"法务\s*文档", "fw_doc", "法务文档"),
    (10, r"康哲\s*资料库|德镁\s*资料库|文档数据库", "kz_doc", "资料库/文档数据库"),
    # 产品语境下的「打开/上传到法务」（不要裸匹配「法务」）
    (
        15,
        r"(?:打开|浏览|进入|上传到|保存到|存到|归档到|放到)\s*法务(?:\s*文档)?(?=\s|$|[里中的，,。])",
        "fw_doc",
        "法务文档",
    ),
    # —— 品牌知识库（须压过句中的「搜索资料库」等）——
    (20, r"玄关\s*知识库", "kz_doc", "玄关知识库"),
    (21, r"康哲\s*知识库", "kz_knowledge_base", "康哲知识库"),
    (22, r"德镁\s*知识库", "kz_knowledge_base", "德镁知识库"),
    # 产品语境「打开/在资料库」（放在品牌知识库之后，避免「xx知识库…资料库」误伤）
    (
        30,
        r"(?:打开|浏览|进入|上传到|保存到|存到|归档到|放到)\s*资料库",
        "kz_doc",
        "资料库",
    ),
    (31, r"(?:在|从)\s*资料库(?:里|中|内)", "kz_doc", "资料库"),
    (
        32,
        r"(?:搜索|查询|查找|检索)\s*资料库",
        "kz_doc",
        "资料库",
    ),
    # 裸「资料库」
    (40, r"资料库", "kz_doc", "资料库"),
    # 裸「知识库」→ 交给企业 listAll
    (50, r"知识库", None, "知识库"),
]


def route_app_code(user_input: str) -> dict:
    """
    从用户话术解析应用通道。

    返回：
      app_code: str|None
      product_label: str|None
      confidence: "high"|"medium"|"low"|"none"
      needs_corp_filter: bool  — True 表示必须与企业 listAll 求交/追问
    """
    text = (user_input or "").strip()
    if not text:
        return {
            "app_code": None,
            "product_label": None,
            "confidence": "none",
            "needs_corp_filter": True,
        }

    best = None
    for priority, pattern, app_code, label in _RULES:
        if re.search(pattern, text):
            if best is None or priority < best[0]:
                best = (priority, app_code, label)

    if best is None:
        return {
            "app_code": None,
            "product_label": None,
            "confidence": "none",
            "needs_corp_filter": True,
        }

    _, app_code, label = best
    if app_code is None:
        return {
            "app_code": None,
            "product_label": label,
            "confidence": "low",
            "needs_corp_filter": True,
        }

    return {
        "app_code": app_code,
        "product_label": label,
        "confidence": "high",
        "needs_corp_filter": True,
    }


def intersect_with_apps(route: dict, apps: list) -> dict:
    """
    将路由结果与企业可用应用 listAll 求交。

    apps: [{ "name": "...", "appCode": "..." }, ...]
    """
    apps = apps or []
    out = dict(route)
    out["matched_apps"] = []
    out["unique"] = False
    out["ask_user"] = False
    out["resolved_app_code"] = None
    out["resolved_name"] = None
    out["hint"] = None

    if not apps:
        out["ask_user"] = True
        out["hint"] = "当前企业下暂无可用的知识库应用，请确认账号权限"
        return out

    target = route.get("app_code")
    label = (route.get("product_label") or "").strip()

    if target:
        matched = [a for a in apps if a.get("appCode") == target]
        out["matched_apps"] = matched
        if len(matched) == 1:
            out["unique"] = True
            out["resolved_app_code"] = matched[0].get("appCode")
            out["resolved_name"] = matched[0].get("name")
        elif len(matched) > 1:
            out["ask_user"] = True
            out["hint"] = "找到多个同通道应用，请选择：" + " / ".join(
                f"{a.get('name')}({a.get('appCode')})" for a in matched
            )
        else:
            out["ask_user"] = True
            out["matched_apps"] = apps
            names = " / ".join(f"{a.get('name')}({a.get('appCode')})" for a in apps)
            out["hint"] = (
                f"你提到的「{label or target}」不在当前企业可用列表中。"
                f"可选：{names}"
            )
        return out

    keyword = label or "知识库"
    if not target and keyword == "知识库" and len(apps) > 1:
        matched = list(apps)
    else:
        matched = [a for a in apps if keyword in (a.get("name") or "")]
        if not matched and keyword == "知识库":
            matched = [
                a for a in apps
                if any(k in (a.get("name") or "") for k in ("知识库", "资料库", "法务", "文档数据库"))
            ]
        if not matched:
            matched = list(apps)

    out["matched_apps"] = matched
    if len(matched) == 1:
        out["unique"] = True
        out["resolved_app_code"] = matched[0].get("appCode")
        out["resolved_name"] = matched[0].get("name")
        out["app_code"] = out["resolved_app_code"]
        out["confidence"] = "medium"
    else:
        out["ask_user"] = True
        names = " / ".join(f"{a.get('name')}({a.get('appCode')})" for a in matched)
        out["hint"] = f"请选择要使用的应用：{names}"
    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="应用通道路由（话术→appCode）")
    parser.add_argument("user_input", nargs="?", help="用户输入")
    parser.add_argument("--user-input", dest="user_input_opt")
    parser.add_argument(
        "--apps",
        type=str,
        help='企业 listAll JSON，如 \'[{"name":"康哲资料库","appCode":"kz_doc"}]\'',
    )
    args = parser.parse_args()
    user_input = args.user_input or args.user_input_opt
    if user_input is None:
        print(json.dumps({
            "resultCode": -1,
            "resultMsg": "缺少输入参数",
            "data": {},
        }, ensure_ascii=False))
        sys.exit(1)

    route = route_app_code(user_input)
    apps = None
    if args.apps:
        try:
            apps = json.loads(args.apps)
        except Exception:
            apps = None
        if isinstance(apps, dict) and "data" in apps:
            apps = apps.get("data")

    data = intersect_with_apps(route, apps) if apps is not None else route
    print(json.dumps({
        "resultCode": 0,
        "resultMsg": "success",
        "data": data,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
