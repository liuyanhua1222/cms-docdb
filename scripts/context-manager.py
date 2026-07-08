#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import os
import datetime

# 上下文文件存储路径
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), ".context")
os.makedirs(CONTEXT_DIR, exist_ok=True)

def get_context_file(user_id="default"):
    """获取上下文文件路径"""
    return os.path.join(CONTEXT_DIR, f"{user_id}.json")

def load_context(user_id="default"):
    """加载上下文"""
    context_file = get_context_file(user_id)
    if os.path.exists(context_file):
        try:
            with open(context_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"history": [], "current_folder": None, "last_file": None, "current_project": None}

def save_context(context, user_id="default"):
    """保存上下文"""
    context_file = get_context_file(user_id)
    with open(context_file, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

def update_context(user_input, action, result, user_id="default"):
    """更新上下文"""
    context = load_context(user_id)
    
    # 添加新的对话记录
    context["history"].append({
        "user_input": user_input,
        "action": action,
        "result": result,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # 只保留最近10条历史
    context["history"] = context["history"][-10:]
    
    save_context(context, user_id)
    return context

def set_current_folder(folder_id, folder_name=None, user_id="default"):
    """设置当前目录"""
    context = load_context(user_id)
    context["current_folder"] = {"id": folder_id, "name": folder_name}
    save_context(context, user_id)
    return context

def set_last_file(file_id, file_name=None, user_id="default"):
    """设置最后访问的文件"""
    context = load_context(user_id)
    context["last_file"] = {"id": file_id, "name": file_name}
    save_context(context, user_id)
    return context

def set_current_project(project_id, project_name=None, user_id="default"):
    """设置当前项目"""
    context = load_context(user_id)
    context["current_project"] = {"id": project_id, "name": project_name}
    save_context(context, user_id)
    return context

def clear_context(user_id="default"):
    """清空上下文"""
    context = {"history": [], "current_folder": None, "last_file": None, "current_project": None}
    save_context(context, user_id)
    return context

def get_context(user_id="default"):
    """获取当前上下文"""
    return load_context(user_id)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="上下文管理和状态维护")
    parser.add_argument("cmd", type=str, nargs='?', help="命令：get/update/set_folder/set_file/set_project/clear")
    parser.add_argument("--cmd", type=str, dest="cmd_opt", help="命令（命名参数）")
    parser.add_argument("--user-id", type=str, default="default", help="用户 ID（可选）")
    parser.add_argument("--user-input", type=str, help="用户输入（update 命令）")
    parser.add_argument("--action", type=str, help="动作（update 命令）")
    parser.add_argument("--result", type=str, default="", help="结果（update 命令）")
    parser.add_argument("--folder-id", type=str, help="文件夹 ID（set_folder 命令）")
    parser.add_argument("--folder-name", type=str, help="文件夹名称（set_folder 命令）")
    parser.add_argument("--file-id", type=str, help="文件 ID（set_file 命令）")
    parser.add_argument("--file-name", type=str, help="文件名称（set_file 命令）")
    parser.add_argument("--project-id", type=str, help="项目 ID（set_project 命令）")
    parser.add_argument("--project-name", type=str, help="项目名称（set_project 命令）")
    args = parser.parse_args()
    
    cmd = args.cmd or args.cmd_opt
    if cmd is None:
        print(json.dumps({
            "resultCode": -1, 
            "resultMsg": "缺少命令参数"
        }, ensure_ascii=False))
        sys.exit(1)
    
    user_id = args.user_id
    result = {"resultCode": 0, "resultMsg": "success", "data": {}}
    
    try:
        if cmd == "get":
            result["data"] = get_context(user_id)
        
        elif cmd == "update":
            if args.user_input and args.action:
                context = update_context(args.user_input, args.action, args.result, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 --user-input, --action, --result"}
        
        elif cmd == "set_folder":
            if args.folder_id:
                context = set_current_folder(args.folder_id, args.folder_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 --folder-id [--folder-name]"}
        
        elif cmd == "set_file":
            if args.file_id:
                context = set_last_file(args.file_id, args.file_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 --file-id [--file-name]"}
        
        elif cmd == "set_project":
            if args.project_id:
                context = set_current_project(args.project_id, args.project_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 --project-id [--project-name]"}

        elif cmd == "clear":
            context = clear_context(user_id)
            result["data"] = context
        
        else:
            result = {"resultCode": -1, "resultMsg": f"未知命令: {cmd}"}
    
    except Exception as e:
        result = {"resultCode": -1, "resultMsg": f"执行失败: {str(e)}"}
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
