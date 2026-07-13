#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
folder-navigator.py - 智能目录导航器

用途：
  根据用户输入的目录名称，在指定空间内智能查找匹配的目录
  支持模糊匹配、路径导航、权限检查

使用方式：
  # 方式1: 在指定空间查找目录
  python3 scripts/folder-navigator.py \
    --project-id 10001 \
    --folder-name "产品资料"
  
  # 方式2: 在多个空间查找目录
  python3 scripts/folder-navigator.py \
    --project-ids "10001,10002" \
    --folder-name "AI生成"
  
  # 方式3: 路径导航（支持层级）
  python3 scripts/folder-navigator.py \
    --project-id 10001 \
    --folder-path "产品资料/慷彼申"

返回格式：
  {
    "resultCode": 0,
    "resultMsg": "success",
    "data": {
      "matched_folders": [...],   # 匹配到的目录列表
      "match_count": 1,            # 匹配数量
      "match_type": "exact|fuzzy|multiple|none",  # 匹配类型
      "navigation_path": [...]     # 导航路径（如果提供）
    }
  }
"""

import sys
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import ssl
from difflib import SequenceMatcher

# 强制标准输出使用 UTF-8 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    """自定义重定向处理器"""
    def http_error_307(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    def http_error_308(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)


def build_opener(ctx):
    """构建支持重定向的 opener"""
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


def build_headers():
    """构造请求头"""
    app_key = os.environ.get("appkey")
    if not app_key:
        print("错误: 未找到 appkey", file=sys.stderr)
        sys.exit(1)
    return {
        "Content-Type": "application/json",
        "appKey": app_key
    }


def get_level1_folders(project_id):
    """获取项目根目录下的所有文件夹"""
    url = f"https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getLevel1Folders?projectId={project_id}"
    headers = build_headers()
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = build_opener(ctx)
    
    try:
        with opener.open(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get('resultCode') == 1:
                folders = result.get('data', {}).get('folders', [])
                return folders
            return []
    except Exception as e:
        print(f"警告: 获取项目 {project_id} 根目录失败: {e}", file=sys.stderr)
        return []


def get_child_folders(parent_id):
    """获取指定目录下的子文件夹"""
    url = f"https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getChildFiles?parentId={parent_id}&type=1"
    headers = build_headers()
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = build_opener(ctx)
    
    try:
        with opener.open(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get('resultCode') == 1:
                folders = result.get('data', {}).get('folders', [])
                return folders
            return []
    except Exception as e:
        print(f"警告: 获取目录 {parent_id} 的子文件夹失败: {e}", file=sys.stderr)
        return []


def normalize_name(name):
    """规范化名称"""
    if not name:
        return ""
    import re
    return re.sub(r'\s+', '', name.lower())


def calculate_similarity(str1, str2):
    """计算相似度"""
    return SequenceMatcher(None, str1, str2).ratio()


def match_folder_in_list(folder_name, folders):
    """在文件夹列表中匹配目标文件夹"""
    if not folder_name or not folders:
        return []
    
    matched = []
    normalized_target = normalize_name(folder_name)
    
    for folder in folders:
        name = folder.get('name', '')
        if not name:
            continue
        
        normalized_name = normalize_name(name)
        score = 0
        reason = ""
        
        # 精确匹配
        if normalized_target == normalized_name:
            score = 100
            reason = "精确匹配"
        # 包含匹配
        elif normalized_target in normalized_name:
            score = 80 + (len(normalized_target) / len(normalized_name)) * 15
            reason = "目录名包含"
        elif normalized_name in normalized_target:
            score = 70
            reason = "输入包含目录名"
        # 模糊匹配
        else:
            similarity = calculate_similarity(normalized_target, normalized_name)
            if similarity > 0.6:
                score = similarity * 60
                reason = f"模糊匹配(相似度{similarity:.2f})"
        
        if score >= 60:
            matched.append({
                **folder,
                'match_score': score,
                'match_reason': reason
            })
    
    # 按分数降序排序
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    return matched


def navigate_by_path(project_id, folder_path):
    """按路径导航（支持多级路径，如 "产品资料/慷彼申"）"""
    if not folder_path:
        return None, []
    
    # 分割路径
    path_parts = [p.strip() for p in folder_path.replace('\\', '/').split('/') if p.strip()]
    
    if not path_parts:
        return None, []
    
    navigation = []
    current_folders = get_level1_folders(project_id)
    current_parent_id = 0
    
    for i, part in enumerate(path_parts):
        # 在当前层级匹配
        matched = match_folder_in_list(part, current_folders)
        
        if not matched:
            # 未找到匹配
            return None, navigation
        
        # 选择最佳匹配
        best_match = matched[0]
        navigation.append({
            'level': i + 1,
            'name': best_match['name'],
            'id': best_match['id'],
            'match_score': best_match['match_score'],
            'match_reason': best_match['match_reason']
        })
        
        # 如果不是最后一层，继续向下
        if i < len(path_parts) - 1:
            current_parent_id = best_match['id']
            current_folders = get_child_folders(current_parent_id)
        else:
            # 最后一层，返回结果
            return best_match, navigation
    
    return None, navigation


def search_folder_in_project(project_id, folder_name, max_depth=3):
    """
    在项目空间内递归搜索目录（深度优先）
    max_depth: 最大搜索深度，避免过深递归
    """
    matched_folders = []
    visited = set()
    
    def dfs_search(parent_id, current_depth, path):
        if current_depth > max_depth:
            return
        
        if parent_id in visited:
            return
        visited.add(parent_id)
        
        # 获取当前层级的文件夹
        if parent_id == 0:
            folders = get_level1_folders(project_id)
        else:
            folders = get_child_folders(parent_id)
        
        # 匹配当前层级
        matched = match_folder_in_list(folder_name, folders)
        for m in matched:
            m['path'] = path
            m['depth'] = current_depth
            matched_folders.append(m)
        
        # 递归搜索子目录（即使当前层有匹配，也继续搜索，可能有同名目录）
        for folder in folders:
            folder_id = folder.get('id')
            folder_name_str = folder.get('name', '')
            if folder_id and folder.get('hasChild'):
                new_path = f"{path}/{folder_name_str}" if path else folder_name_str
                dfs_search(folder_id, current_depth + 1, new_path)
    
    dfs_search(0, 1, "")
    
    # 按匹配分数和深度排序（分数高优先，深度浅优先）
    matched_folders.sort(key=lambda x: (-x['match_score'], x['depth']))
    
    return matched_folders


def determine_match_type(matched_folders):
    """判断匹配类型"""
    count = len(matched_folders)
    if count == 0:
        return "none"
    elif count == 1:
        score = matched_folders[0].get('match_score', 0)
        if score >= 95:
            return "exact"
        else:
            return "fuzzy"
    else:
        # 检查是否有明显的最佳匹配
        if len(matched_folders) >= 2:
            top_score = matched_folders[0].get('match_score', 0)
            second_score = matched_folders[1].get('match_score', 0)
            if top_score - second_score >= 20:
                return "best_match"
        return "multiple"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="智能目录导航器")
    parser.add_argument("--project-id", type=int, help="项目空间 ID")
    parser.add_argument("--project-ids", type=str, help="多个项目空间 ID（逗号分隔）")
    parser.add_argument("--folder-name", type=str, help="目录名称（单层匹配）")
    parser.add_argument("--folder-path", type=str, help="目录路径（多层导航，如 '产品资料/慷彼申'）")
    parser.add_argument("--max-depth", type=int, default=3, help="最大搜索深度（默认3层）")
    args = parser.parse_args()
    
    try:
        # 解析项目 ID
        project_ids = []
        if args.project_id:
            project_ids.append(args.project_id)
        if args.project_ids:
            project_ids.extend([int(pid.strip()) for pid in args.project_ids.split(',') if pid.strip()])
        
        if not project_ids:
            raise ValueError("必须提供 --project-id 或 --project-ids")
        
        # 场景1: 路径导航
        if args.folder_path:
            if len(project_ids) > 1:
                raise ValueError("路径导航仅支持单个项目空间")
            
            project_id = project_ids[0]
            target_folder, navigation = navigate_by_path(project_id, args.folder_path)
            
            if target_folder:
                result = {
                    "resultCode": 0,
                    "resultMsg": "success",
                    "data": {
                        "matched_folders": [target_folder],
                        "match_count": 1,
                        "match_type": "exact",
                        "navigation_path": navigation,
                        "project_id": project_id
                    }
                }
            else:
                result = {
                    "resultCode": 0,
                    "resultMsg": "success",
                    "data": {
                        "matched_folders": [],
                        "match_count": 0,
                        "match_type": "none",
                        "navigation_path": navigation,
                        "project_id": project_id,
                        "error": f"路径导航失败，已导航到第 {len(navigation)} 层"
                    }
                }
        
        # 场景2: 名称搜索
        elif args.folder_name:
            all_matched = []
            
            for project_id in project_ids:
                matched = search_folder_in_project(project_id, args.folder_name, args.max_depth)
                for m in matched:
                    m['project_id'] = project_id
                all_matched.extend(matched)
            
            # 跨项目排序
            all_matched.sort(key=lambda x: (-x['match_score'], x['depth']))
            
            match_type = determine_match_type(all_matched)
            
            result = {
                "resultCode": 0,
                "resultMsg": "success",
                "data": {
                    "matched_folders": all_matched,
                    "match_count": len(all_matched),
                    "match_type": match_type,
                    "searched_projects": project_ids
                }
            }
        
        else:
            raise ValueError("必须提供 --folder-name 或 --folder-path")
        
        print(json.dumps(result, ensure_ascii=False))
    
    except Exception as e:
        print(json.dumps({
            "resultCode": -1,
            "resultMsg": f"导航失败: {str(e)}",
            "data": {}
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
