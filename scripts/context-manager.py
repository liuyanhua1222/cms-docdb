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
    if len(sys.argv) < 2:
        print(json.dumps({
            "resultCode": -1, 
            "resultMsg": "缺少命令参数"
        }, ensure_ascii=False))
        sys.exit(1)
    
    cmd = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "default"
    result = {"resultCode": 0, "resultMsg": "success", "data": {}}
    
    try:
        if cmd == "get":
            result["data"] = get_context(user_id)
        
        elif cmd == "update":
            if len(sys.argv) >= 5:
                user_input = sys.argv[3]
                action = sys.argv[4]
                result_data = sys.argv[5] if len(sys.argv) > 5 else ""
                context = update_context(user_input, action, result_data, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 user_input, action, result"}
        
        elif cmd == "set_folder":
            if len(sys.argv) >= 4:
                folder_id = sys.argv[3]
                folder_name = sys.argv[4] if len(sys.argv) > 4 else None
                context = set_current_folder(folder_id, folder_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 folder_id [folder_name]"}
        
        elif cmd == "set_file":
            if len(sys.argv) >= 4:
                file_id = sys.argv[3]
                file_name = sys.argv[4] if len(sys.argv) > 4 else None
                context = set_last_file(file_id, file_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 file_id [file_name]"}
        
        elif cmd == "set_project":
            if len(sys.argv) >= 4:
                project_id = sys.argv[3]
                project_name = sys.argv[4] if len(sys.argv) > 4 else None
                context = set_current_project(project_id, project_name, user_id)
                result["data"] = context
            else:
                result = {"resultCode": -1, "resultMsg": "参数不足：需要 project_id [project_name]"}
        
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