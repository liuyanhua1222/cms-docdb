#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import re
import os

# 允许从 common 导入 app_code_router
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "common"))
try:
    from app_code_router import route_app_code
except ImportError:
    route_app_code = None


def extract_parameters(user_input, context=None):
    """
    从用户输入中提取参数，支持上下文补全

    优化策略：
    1. 先识别空间名称候选词与 appCode
    2. 标记需要先调用 get-app-list / get-project-list
    3. 在实际空间列表中进行模糊匹配，避免分词错误
    """
    params = {}

    # 0. 应用通道路由（t_doc_app）
    if route_app_code:
        route = route_app_code(user_input)
        if route.get("app_code"):
            params["app_code"] = route["app_code"]
        if route.get("product_label"):
            params["product_label"] = route["product_label"]
        params["app_code_confidence"] = route.get("confidence")
        params["needs_corp_filter"] = bool(route.get("needs_corp_filter", True))
        # 无论置信度高低，均建议与企业 listAll 求交（高置信校验权限，低置信先筛再问）
        params["needs_app_list"] = True
    else:
        params["needs_app_list"] = True
        params["needs_corp_filter"] = True

    # 从上下文复用 app_code（用户未点名新产品时）
    if "app_code" not in params and context and context.get("current_app_code"):
        params["app_code"] = context["current_app_code"]
        params["app_code_from_context"] = True
        params["needs_app_list"] = False

    # 1. 提取项目/空间名称（优先级最高）
    project_patterns = [
        # 资料库 / 法务（优先整词）
        r"(康哲资料库|德镁资料库|法务文档|文档数据库)",
        r"(康哲|德镁)\s*资料库",
        r"法务\s*文档?",
        r"资料库",
        # 知识库：拆开玄关 vs 康哲/德镁（appCode 不同）
        r"(玄关知识库)",
        r"(康哲知识库|德镁知识库)",
        r"(康哲|玄关|德镁)\s*知识库",
        r"(康哲|玄关|德镁)",
        # "保存到/上传到 + 空间名" 格式
        r"(?:保存到|上传到|归档到|存到)([^，,。.的里中之文件]+?)(?:知识库|资料库|文档数据库|空间|项目|的|里|中)",
        r"(?:搜索|查询|查找|检索)([^，,。.的里中之文件]+?)(?:知识库|资料库|文档数据库|空间|项目|的|里|中)",
        r"(?:打开|浏览)([^，,。.的里中之文件]+?)(?:知识库|资料库|文档数据库|空间|项目)?",
        r"(?:在|从)([^，,。.的里中之文件]+?)(?:知识库|资料库|文档数据库|空间|项目)",
    ]

    project_name_candidates = []
    for pattern in project_patterns:
        matches = re.findall(pattern, user_input, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and match.strip():
                candidate = match.strip()
                # 短词停用；整词产品名保留
                if candidate not in ['文件', '资料', '文档', '内容', '这个', '那个', '法务']:
                    project_name_candidates.append(candidate)
                elif candidate == '法务' and '法务' in user_input:
                    project_name_candidates.append('法务文档')

    # 去重并去掉过短误切分（如「法」「玄」）
    project_name_candidates = [
        c for c in list(dict.fromkeys(project_name_candidates))
        if len(c) >= 2
    ]

    if project_name_candidates:
        params["project_name_candidates"] = project_name_candidates
        params["needs_project_list"] = True

    # 2. 提取关键词（文件名、搜索词）
    keyword_patterns = [
        r"(?:查询|搜索|查找|检索|读取|查看|总结)\s*([^，,。.知识库资料库空间项目]+)",
        r"[\u201c\u201d]([^\u201c\u201d]+)[\u201c\u201d]",
        r'"([^"]+)"',
        r"'([^']+)'",
        r"[（(]([^）)]+)[）)]",
        r"([\u4e00-\u9fa5a-zA-Z0-9_\-\s]+?)\s*(文件|资料|政策|文档|报告)"
    ]

    keywords = []
    product_stop = {
        '知识库', '资料库', '文档数据库', '法务文档', '空间', '项目',
        '康哲', '玄关', '德镁', '法务',
        '康哲知识库', '玄关知识库', '德镁知识库', '康哲资料库', '德镁资料库',
    }
    for pattern in keyword_patterns:
        matches = re.findall(pattern, user_input)
        for match in matches:
            if isinstance(match, tuple):
                keyword = match[-1].strip() if len(match) > 1 else match[0].strip()
            else:
                keyword = match.strip()
            if (keyword and
                keyword not in project_name_candidates and
                keyword not in product_stop):
                # 避免「法务文档」被拆成关键词「文档」
                if keyword in ('文件', '资料', '政策', '文档', '报告') and any(
                    p in user_input for p in ('法务文档', '康哲资料库', '德镁资料库', '文档数据库')
                ):
                    continue
                keywords.append(keyword)

    keywords = list(filter(None, list(dict.fromkeys(keywords))))
    if keywords:
        params["keywords"] = keywords

    # 3. 提取路径和目录名称
    space_folder_pattern = r"(?:知识库|资料库|文档数据库|空间|项目)的([一-龥a-zA-Z0-9]+)(?:目录|文件夹)"
    match = re.search(space_folder_pattern, user_input)
    if match:
        folder_name = match.group(1)
        params["folder_name_candidates"] = [folder_name]
        params["needs_folder_navigation"] = True
    elif "/" in user_input:
        path_pattern = r"(?:上传到|保存到|放到|存到|归档到)?\s*([\u4e00-\u9fa5a-zA-Z0-9]+/[\u4e00-\u9fa5a-zA-Z0-9/]+)"
        match = re.search(path_pattern, user_input)
        if match:
            path = match.group(1)
            params["folder_path"] = path
            params["needs_folder_navigation"] = True
    else:
        folder_pattern = r"(?:到|在)\s*([一-龥a-zA-Z0-9]{2,10})\s*(?:目录|文件夹)"
        match = re.search(folder_pattern, user_input)
        if match:
            folder_name = match.group(1)
            if (folder_name not in product_stop and
                not any(folder_name in p for p in project_name_candidates)):
                params["folder_name_candidates"] = [folder_name]
                params["needs_folder_navigation"] = True

    # 4. 指代
    refer_patterns = ["这个文件", "该文件", "这个文档", "它", "这个"]
    if any(pattern in user_input for pattern in refer_patterns):
        if context and context.get("last_file"):
            params["file_id"] = context["last_file"].get("id")
            params["file_name"] = context["last_file"].get("name")
        else:
            params["needs_file"] = True

    # 5. 相对路径
    if "上一级" in user_input or "上级目录" in user_input:
        params["parent_folder"] = True
    elif "当前目录" in user_input or "这个文件夹" in user_input:
        if context and context.get("current_folder"):
            params["folder_id"] = context["current_folder"].get("id")
            params["folder_name"] = context["current_folder"].get("name")
        else:
            params["needs_folder"] = True

    # 6. 数字参数
    num_pattern = r"(\d+)\s*(版本|页|号)"
    match = re.search(num_pattern, user_input)
    if match:
        params[match.group(2)] = match.group(1)

    # 7. 员工 ID
    emp_id_patterns = [
        r"(empId|EMPID|员工id|员工ID|员工Id)\s*[：:\s]*\s*(\d+)",
        r".*分享给\s*(\d+)\s*$",
        r".*授权给\s*(\d+)\s*$",
    ]
    for pattern in emp_id_patterns:
        match = re.search(pattern, user_input)
        if match:
            emp_id = match.group(match.lastindex)
            params["emp_id"] = int(emp_id)
            break

    # 8. 上下文项目
    if "project_name_candidates" not in params and context and context.get("current_project"):
        params["project_id"] = context["current_project"].get("id")
        params["project_name"] = context["current_project"].get("name")

    return params


def generate_missing_params_hint(params):
    hints = []

    if params.get("needs_file"):
        hints.append("请问你想操作哪个文件？")

    if params.get("needs_folder"):
        hints.append("请问你想在哪个目录下操作？")

    if params.get("needs_app_list"):
        app = params.get("app_code")
        label = params.get("product_label") or ""
        if app:
            hints.append(
                f"识别到产品通道：{label or app}（appCode={app}），"
                f"请先 get-app-list.py 与企业可用应用求交，再 get-project-list.py --app-code {app}"
            )
        else:
            hints.append(
                "产品通道不明确：请先 get-app-list.py 按企业收敛可选应用；"
                "唯一匹配可直用，多个则列选项追问用户"
            )

    if params.get("needs_project_list"):
        candidates = ', '.join(params.get('project_name_candidates', []))
        app = params.get("app_code")
        extra = f"（务必带 --app-code {app}）" if app else "（先确定 appCode 再拉列表）"
        hints.append(f"识别到空间名称：{candidates}，需要先获取你有权限的空间列表进行匹配{extra}")

    if params.get("needs_folder_navigation"):
        if params.get("folder_path"):
            hints.append(f"识别到目录路径：{params['folder_path']}，需要在空间内导航")
        elif params.get("folder_name_candidates"):
            candidates = ', '.join(params['folder_name_candidates'])
            hints.append(f"识别到目录名称：{candidates}，需要在空间内查找匹配的目录")

    if ("keywords" not in params and
        "folder_path" not in params and
        "folder_name_candidates" not in params and
        "file_id" not in params and
        "project_name_candidates" not in params and
        not params.get("needs_app_list")):
        hints.append("请提供要搜索或操作的文件名、关键词或路径")

    return "\n".join(hints) if hints else None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="参数提取和缺失提示生成")
    parser.add_argument("user_input", type=str, nargs='?', help="用户输入（位置参数）")
    parser.add_argument("--user-input", type=str, dest="user_input_opt", help="用户输入（命名参数）")
    parser.add_argument("--context", type=str, help="上下文 JSON（可选）")
    args = parser.parse_args()

    user_input = args.user_input or args.user_input_opt
    if user_input is None:
        print(json.dumps({
            "resultCode": -1,
            "resultMsg": "缺少输入参数",
            "data": {}
        }, ensure_ascii=False))
        sys.exit(1)

    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except Exception:
            pass

    params = extract_parameters(user_input, context)
    missing_hint = generate_missing_params_hint(params)

    result = {
        "resultCode": 0,
        "resultMsg": "success",
        "data": {
            "parameters": params,
            "missing_hint": missing_hint
        }
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
