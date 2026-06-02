#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import re

def extract_parameters(user_input, context=None):
    """
    从用户输入中提取参数，支持上下文补全
    """
    params = {}
    
    # 1. 提取关键词（文件名、搜索词）
    keyword_patterns = [
        # 匹配 "搜索xxx" 格式
        r"(查询|搜索|查找|检索|读取|查看|总结)\s*[“”\"'\s]*([^“”\"'\s，,。.]+)",
        # 匹配引号内内容
        r"“([^”]+)”",
        r'"([^"]+)"',
        r"'([^']+)'",
        # 匹配括号内内容
        r"[（(]([^）)]+)[）)]",
        # 匹配 "xxx文件" 格式
        r"([\u4e00-\u9fa5a-zA-Z0-9_\-\s]+?)\s*(文件|资料|政策|文档|报告)"
    ]
    
    keywords = []
    for pattern in keyword_patterns:
        matches = re.findall(pattern, user_input)
        for match in matches:
            if isinstance(match, tuple):
                keywords.append(match[-1].strip())
            else:
                keywords.append(match.strip())
    
    # 去重并过滤空字符串
    keywords = list(filter(None, list(dict.fromkeys(keywords))))
    
    if keywords:
        params["keywords"] = keywords
    
    # 2. 提取路径（如 "产品资料-慷彼申"）
    path_pattern = r"([\u4e00-\u9fa5a-zA-Z0-9]+[-/][\u4e00-\u9fa5a-zA-Z0-9]+)"
    match = re.search(path_pattern, user_input)
    if match:
        params["path"] = match.group(1)
    
    # 3. 处理指代（"这个文件"、"它"等）
    refer_patterns = ["这个文件", "该文件", "这个文档", "它", "这个"]
    if any(pattern in user_input for pattern in refer_patterns):
        if context and context.get("last_file"):
            params["file_id"] = context["last_file"].get("id")
            params["file_name"] = context["last_file"].get("name")
        else:
            params["needs_file"] = True
    
    # 4. 处理相对路径（"上一级"、"当前目录"等）
    if "上一级" in user_input or "上级目录" in user_input:
        params["parent_folder"] = True
    elif "当前目录" in user_input or "这个文件夹" in user_input:
        if context and context.get("current_folder"):
            params["folder_id"] = context["current_folder"].get("id")
            params["folder_name"] = context["current_folder"].get("name")
        else:
            params["needs_folder"] = True
    
    # 5. 提取数字参数（如版本号）
    num_pattern = r"(\d+)\s*(版本|页|号)"
    match = re.search(num_pattern, user_input)
    if match:
        params[match.group(2)] = match.group(1)

    # 5.1 提取员工 ID（empId），用于分享授权
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
    
    # 6. 提取项目相关信息
    project_patterns = [
        r"(项目|空间)\s*[：:]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)",
        r"(项目|空间)\s*([\u4e00-\u9fa5a-zA-Z0-9]+)"
    ]
    for pattern in project_patterns:
        match = re.search(pattern, user_input)
        if match:
            params["project_name"] = match.group(2)
            break
    
    # 7. 如果没有明确指定项目，使用上下文
    if "project_name" not in params and context and context.get("current_project"):
        params["project_id"] = context["current_project"].get("id")
        params["project_name"] = context["current_project"].get("name")
    
    return params

def generate_missing_params_hint(params):
    """生成缺失参数的提示"""
    hints = []
    
    if params.get("needs_file"):
        hints.append("请问你想操作哪个文件？")
    
    if params.get("needs_folder"):
        hints.append("请问你想在哪个目录下操作？")
    
    if "keywords" not in params and "path" not in params and "file_id" not in params:
        hints.append("请提供要搜索或操作的文件名、关键词或路径")
    
    if not params.get("project_id") and not params.get("project_name"):
        hints.append("请指定要操作的项目或空间")
    
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
        except:
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