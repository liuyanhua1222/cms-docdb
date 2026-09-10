#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
folder-navigator.py - 智能目录导航器

用途：
  根据用户输入的目录名称，在指定空间内智能查找匹配的目录
  --folder-path：走 OpenAPI resolvePath 精确解析（禁止模糊）
  --folder-name：模糊发现；多命中/非精确须用户确认，不得直接当 upload parent

使用方式：
  python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申"

  # 方式1: 在指定空间查找目录（可能多命中，须确认）
    --project-id 10001 --folder-name "产品资料"
  # 方式2: 精确路径（推荐写入前定位）
    --project-id 10001 --folder-path "产品资料/慷彼申"
返回格式见 stdout JSON；路径解析失败或需确认时见 needs_user_confirm。
"""

import sys
import json
import os
import urllib.parse
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

RESOLVE_PATH_API = "/document-database/file/resolvePath"
PROJECT_LIST_PATH = "/document-database/project/list"


def normalize_relative_path(path):
    """与 browse/resolve-path 对齐：反斜杠→/，去首尾空白与 /。"""
    return (path or "").replace("\\", "/").strip().strip("/")


def lookup_project_name(project_id, app_code=None):
    """Best-effort：从 project/list 取空间名；失败返回空串。"""
    params = []
    if app_code:
        params.append(("appCode", app_code))
    url = PROJECT_LIST_PATH
    if params:
        url = f"{PROJECT_LIST_PATH}?{urllib.parse.urlencode(params)}"
    try:
        result = request_open_api(url, method="GET")
    except Exception as ex:
        print(f"警告: 查询空间名失败 — {ex}", file=sys.stderr)
        return ""
    if not isinstance(result, dict) or result.get("resultCode") != 1:
        print("警告: 查询空间名失败（project/list）", file=sys.stderr)
        return ""
    data = result.get("data") or []
    if not isinstance(data, list):
        return ""
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("id") == project_id or str(item.get("id")) == str(project_id):
            return item.get("name") or item.get("projectName") or ""
    return ""


def resolve_path_exact(project_id, folder_path, root_file_id=0):
    """调用 OpenAPI resolvePath；精确分段匹配，不回退模糊。"""
    path = normalize_relative_path(folder_path)
    if not path:
        raise ValueError("folder-path 不能为空")
    params = [
        ("projectId", str(project_id)),
        ("rootFileId", str(root_file_id)),
        ("path", path),
    ]
    url = f"{RESOLVE_PATH_API}?{urllib.parse.urlencode(params)}"
    raw = request_open_api(url, method="GET")
    if not isinstance(raw, dict) or raw.get("resultCode") != 1:
        msg = raw.get("resultMsg") if isinstance(raw, dict) else str(raw)
        raise RuntimeError(f"resolvePath 失败: {msg}")
    data = raw.get("data") or {}
    return path, data


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
写入前定位请优先 --folder-path（走 resolvePath 精确解析）或 browse/resolve-path.py。
--folder-name 仅用于发现；多命中/非精确时 needs_user_confirm=true，禁止直接当上传父目录。
示例: python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申"
""",
    )
    parser.add_argument("--project-id", type=int, help="项目空间 ID")
    parser.add_argument("--project-ids", type=str, help="多个项目空间 ID（逗号分隔）")
    parser.add_argument("--folder-name", type=str, help="目录名称（单层匹配）")
    parser.add_argument("--folder-path", type=str, help="目录路径（多层导航，如 '产品资料/慷彼申'）")
    parser.add_argument("--max-depth", type=int, default=3, help="最大搜索深度（默认3层）")
    parser.add_argument("--app-code", type=str, default="", help="可选：查空间名时传入 appCode（仅 --folder-path）")
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
        
        # 场景1: 路径导航 — 必须走 resolvePath 精确解析
        if args.folder_path:
            if len(project_ids) > 1:
                raise ValueError("路径导航仅支持单个项目空间；请用 --project-id")

            project_id = project_ids[0]
            path, resolved = resolve_path_exact(project_id, args.folder_path)
            exists = bool(resolved.get("exists"))
            file_id = resolved.get("fileId")
            file_type = resolved.get("type")
            project_name = lookup_project_name(project_id, args.app_code or None)

            if not exists or file_id is None:
                print(json.dumps({
                    "resultCode": -1,
                    "resultMsg": f"路径不存在: projectId={project_id} path={path}",
                    "data": {
                        "matched_folders": [],
                        "match_count": 0,
                        "match_type": "none",
                        "projectName": project_name,
                        "project_id": project_id,
                        "projectId": project_id,
                        "path": path,
                        "fileId": file_id,
                        "needs_user_confirm": False,
                        "resolve": resolved,
                    },
                }, ensure_ascii=False))
                sys.exit(1)

            leaf_name = path.split("/")[-1] if path else ""
            target_folder = {
                "id": file_id,
                "name": leaf_name,
                "type": file_type,
                "project_id": project_id,
                "path": path,
                "match_score": 100,
                "match_reason": "resolvePath精确匹配",
            }
            resolve_block = {
                "exists": True,
                "projectName": project_name,
                "projectId": project_id,
                "path": path,
                "fileId": file_id,
                "type": file_type,
            }
            if not project_name:
                resolve_block["projectNameWarning"] = (
                    "未能解析空间名；请核对 projectId / --app-code"
                )
            result = {
                "resultCode": 0,
                "resultMsg": "success",
                "data": {
                    "matched_folders": [target_folder],
                    "match_count": 1,
                    "match_type": "exact",
                    "projectName": project_name,
                    "project_id": project_id,
                    "projectId": project_id,
                    "path": path,
                    "fileId": file_id,
                    "needs_user_confirm": False,
                    "resolve": resolve_block,
                },
            }

        # 场景2: 名称搜索（多空间时允许部分成功；非精确须确认）
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
                        "needs_user_confirm": False,
                    },
                }, ensure_ascii=False))
                sys.exit(1)

            all_matched.sort(key=lambda x: (-x['match_score'], x['depth']))
            match_type = determine_match_type(all_matched)
            needs_confirm = match_type in ("multiple", "fuzzy", "best_match")

            data = {
                "matched_folders": all_matched,
                "match_count": len(all_matched),
                "match_type": match_type,
                "searched_projects": searched_projects,
                "needs_user_confirm": needs_confirm,
            }
            if needs_confirm:
                data["confirm_hint"] = (
                    "多命中或非精确匹配：禁止直接用作上传父目录；"
                    "请用户确认空间与路径，或改用 --folder-path / resolve-path.py"
                )
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
