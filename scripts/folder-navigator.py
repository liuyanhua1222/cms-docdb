#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
folder-navigator.py - 智能目录导航器

用途：
  根据用户输入的目录名称，在指定空间内智能查找匹配的目录
  支持模糊匹配、路径导航、权限检查

使用方式：
  # 方式1: 在指定空间查找目录
    --project-id 10001 \
    --folder-name "产品资料"
  
  # 方式2: 在多个空间查找目录
    --project-ids "10001,10002" \
    --folder-name "AI生成"
  
  # 方式3: 路径导航（支持层级）
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
from difflib import SequenceMatcher

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser

# 强制标准输出使用 UTF-8 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


def _is_folder_item(item):
    """FileVO: type=1 为文件夹；兼容 isFolder 字段。"""
    if not isinstance(item, dict):
        return False
    if item.get('type') == 1:
        return True
    return bool(item.get('isFolder'))


def extract_folders_from_result(result, context=""):
    """
    从 getLevel1Folders / getChildFiles 响应中提取文件夹列表。

    Open API 契约：data 为 List[FileVO]（文件与文件夹混排）。
    兜底：若 data 为 dict，再读 folders / files（非正式契约）。
    接口失败或结构异常时抛错，禁止伪装成空列表。
    """
    label = context or "目录接口"
    if not isinstance(result, dict):
        raise RuntimeError(f"{label} 响应不是对象: {type(result).__name__}")
    if result.get('resultCode') != 1:
        raise RuntimeError(
            f"{label} 失败: resultCode={result.get('resultCode')}, "
            f"resultMsg={result.get('resultMsg')}"
        )
    data = result.get('data')
    if data is None:
        return []
    if isinstance(data, list):
        return [x for x in data if _is_folder_item(x)]
    if isinstance(data, dict):
        folders = data.get('folders')
        if isinstance(folders, list):
            return [x for x in folders if _is_folder_item(x) or 'type' not in x]
        files = data.get('files')
        if isinstance(files, list):
            return [x for x in files if _is_folder_item(x)]
        raise RuntimeError(f"{label} data 为对象但无 folders/files 列表")
    raise RuntimeError(f"{label} data 类型不支持: {type(data).__name__}")


def get_level1_folders(project_id):
    """获取项目根目录下的所有文件夹；失败抛错，不返回伪装空列表。"""
    url = f"/document-database/file/getLevel1Folders?projectId={project_id}"
    result = request_open_api(url, method="GET")
    return extract_folders_from_result(result, context=f"getLevel1Folders(projectId={project_id})")


def get_child_folders(parent_id):
    """获取指定目录下的子文件夹；失败抛错，不返回伪装空列表。"""
    url = f"/document-database/file/getChildFiles?parentId={parent_id}&type=1"
    result = request_open_api(url, method="GET")
    return extract_folders_from_result(result, context=f"getChildFiles(parentId={parent_id})")

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
        
        # 递归搜索子目录（已筛为文件夹；不依赖 hasChild，避免漏搜深层）
        for folder in folders:
            folder_id = folder.get('id')
            folder_name_str = folder.get('name', '')
            if folder_id:
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
    parser = DocdbArgumentParser(
        description="智能目录导航器",
        hint="""folder-navigator.py 须提供 --project-id（或 --project-ids）以及 --folder-name 或 --folder-path。
示例: python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料"；缺参补齐后用同一 python 命令重试
""",
    )
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
        
        # 场景2: 名称搜索（多空间时允许部分成功）
        elif args.folder_name:
            all_matched = []
            project_errors = []
            searched_projects = []

            for project_id in project_ids:
                try:
                    matched = search_folder_in_project(
                        project_id, args.folder_name, args.max_depth
                    )
                    for m in matched:
                        m['project_id'] = project_id
                    all_matched.extend(matched)
                    searched_projects.append(project_id)
                except Exception as e:
                    project_errors.append({
                        "project_id": project_id,
                        "message": str(e),
                    })

            # 全部空间都失败 → 整次失败（不伪装成「没匹配到」）
            if not searched_projects:
                err_summary = "; ".join(
                    f"{e['project_id']}: {e['message']}" for e in project_errors
                )
                print(json.dumps({
                    "resultCode": -1,
                    "resultMsg": f"导航失败: 所有空间均查询失败 — {err_summary}",
                    "data": {
                        "matched_folders": [],
                        "match_count": 0,
                        "match_type": "none",
                        "searched_projects": [],
                        "errors": project_errors,
                    },
                }, ensure_ascii=False))
                sys.exit(1)

            all_matched.sort(key=lambda x: (-x['match_score'], x['depth']))
            match_type = determine_match_type(all_matched)

            data = {
                "matched_folders": all_matched,
                "match_count": len(all_matched),
                "match_type": match_type,
                "searched_projects": searched_projects,
            }
            if project_errors:
                data["errors"] = project_errors
                data["failed_projects"] = [e["project_id"] for e in project_errors]

            result = {
                "resultCode": 0,
                "resultMsg": (
                    "partial_success" if project_errors else "success"
                ),
                "data": data,
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
