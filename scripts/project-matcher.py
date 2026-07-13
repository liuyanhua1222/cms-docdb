#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project-matcher.py - 智能空间名称匹配器

用途：
  在用户可访问的空间列表中，根据用户输入的空间名称候选词进行模糊匹配
  避免因分词错误导致的匹配失败

使用方式：
  python3 scripts/project-matcher.py --candidates "康哲,知识库" --project-list '[{"id":123,"name":"康哲知识库"},...]'
  
返回格式：
  {
    "resultCode": 0,
    "resultMsg": "success",
    "data": {
      "matched_projects": [...],  # 匹配到的空间列表
      "match_count": 1,            # 匹配数量
      "match_type": "exact|fuzzy|multiple|none"  # 匹配类型
    }
  }
"""

import sys
import json
import re
from difflib import SequenceMatcher

# 强制标准输出使用 UTF-8 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


def normalize_name(name):
    """规范化名称：去除空格、转小写"""
    if not name:
        return ""
    return re.sub(r'\s+', '', name.lower())


def calculate_similarity(str1, str2):
    """计算两个字符串的相似度（0-1之间）"""
    return SequenceMatcher(None, str1, str2).ratio()


def match_projects(candidates, project_list):
    """
    在项目列表中匹配候选词
    
    匹配策略：
    1. 精确匹配：候选词完全匹配项目名称
    2. 包含匹配：项目名称包含候选词，或候选词包含项目名称
    3. 模糊匹配：相似度 > 0.6
    4. 组合匹配：多个候选词组合后匹配
    """
    if not candidates or not project_list:
        return []
    
    matched_projects = []
    match_scores = []  # 记录匹配分数，用于排序
    
    # 规范化候选词
    normalized_candidates = [normalize_name(c) for c in candidates]
    combined_candidate = ''.join(normalized_candidates)  # 组合候选词
    
    for project in project_list:
        project_name = project.get('name', '')
        project_id = project.get('id')
        
        if not project_name:
            continue
        
        normalized_project_name = normalize_name(project_name)
        max_score = 0
        match_reason = ""
        
        # 策略1：精确匹配
        for i, candidate in enumerate(normalized_candidates):
            if candidate == normalized_project_name:
                max_score = 100
                match_reason = f"精确匹配：'{candidates[i]}'"
                break
        
        # 策略2：包含匹配
        if max_score < 100:
            for i, candidate in enumerate(normalized_candidates):
                if candidate in normalized_project_name:
                    score = 80 + (len(candidate) / len(normalized_project_name)) * 10
                    if score > max_score:
                        max_score = score
                        match_reason = f"项目名包含：'{candidates[i]}'"
                elif normalized_project_name in candidate:
                    score = 75
                    if score > max_score:
                        max_score = score
                        match_reason = f"候选词包含项目名"
        
        # 策略3：组合候选词匹配
        if max_score < 80:
            if combined_candidate == normalized_project_name:
                max_score = 95
                match_reason = f"组合精确匹配：'{'+'.join(candidates)}'"
            elif combined_candidate in normalized_project_name:
                score = 85
                if score > max_score:
                    max_score = score
                    match_reason = f"项目名包含组合词：'{'+'.join(candidates)}'"
            elif normalized_project_name in combined_candidate:
                score = 70
                if score > max_score:
                    max_score = score
                    match_reason = f"组合词包含项目名"
        
        # 策略4：模糊匹配（相似度）
        if max_score < 70:
            for i, candidate in enumerate(normalized_candidates):
                similarity = calculate_similarity(candidate, normalized_project_name)
                score = similarity * 60  # 最高60分
                if score > max_score and similarity > 0.6:
                    max_score = score
                    match_reason = f"模糊匹配：'{candidates[i]}'（相似度{similarity:.2f}）"
            
            # 组合词相似度
            similarity = calculate_similarity(combined_candidate, normalized_project_name)
            score = similarity * 65
            if score > max_score and similarity > 0.6:
                max_score = score
                match_reason = f"组合模糊匹配（相似度{similarity:.2f}）"
        
        # 如果匹配分数 > 60，认为是有效匹配
        if max_score >= 60:
            matched_projects.append({
                "id": project_id,
                "name": project_name,
                "match_score": max_score,
                "match_reason": match_reason,
                # 保留原始项目的其他字段
                **{k: v for k, v in project.items() if k not in ['id', 'name']}
            })
            match_scores.append(max_score)
    
    # 按匹配分数降序排序
    matched_projects.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matched_projects


def determine_match_type(matched_projects):
    """判断匹配类型"""
    count = len(matched_projects)
    if count == 0:
        return "none"
    elif count == 1:
        score = matched_projects[0].get('match_score', 0)
        if score >= 95:
            return "exact"
        else:
            return "fuzzy"
    else:
        # 检查是否有明显的最佳匹配（分数远高于其他）
        if len(matched_projects) >= 2:
            top_score = matched_projects[0].get('match_score', 0)
            second_score = matched_projects[1].get('match_score', 0)
            if top_score - second_score >= 20:
                return "best_match"
        return "multiple"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="智能空间名称匹配器")
    parser.add_argument("--candidates", type=str, required=True,
                        help="候选词列表（逗号分隔），如 '康哲,知识库'")
    parser.add_argument("--project-list", type=str, required=True,
                        help="项目列表 JSON 数组")
    args = parser.parse_args()
    
    try:
        # 解析候选词
        candidates = [c.strip() for c in args.candidates.split(',') if c.strip()]
        
        # 解析项目列表
        project_list = json.loads(args.project_list)
        
        if not isinstance(project_list, list):
            raise ValueError("project_list must be a JSON array")
        
        # 执行匹配
        matched_projects = match_projects(candidates, project_list)
        match_type = determine_match_type(matched_projects)
        
        result = {
            "resultCode": 0,
            "resultMsg": "success",
            "data": {
                "matched_projects": matched_projects,
                "match_count": len(matched_projects),
                "match_type": match_type,
                "input_candidates": candidates
            }
        }
        
        print(json.dumps(result, ensure_ascii=False))
    
    except json.JSONDecodeError as e:
        print(json.dumps({
            "resultCode": -1,
            "resultMsg": f"JSON 解析失败: {str(e)}",
            "data": {}
        }, ensure_ascii=False))
        sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "resultCode": -1,
            "resultMsg": f"匹配失败: {str(e)}",
            "data": {}
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
