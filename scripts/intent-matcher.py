#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re
import json

# 意图模式匹配
INTENT_PATTERNS = {
    "browse": [
        r".*公司在线知识库.*",
        r".*打开.*(康哲|玄关|德镁)知识库.*",
        r".*(康哲|玄关|德镁)知识库.*里有什么.*",
        r".*打开.*文档数据库.*",
        r".*文档数据库.*里有什么.*",
        r".*打开.*知识库.*",
        r".*浏览.*(文件夹|目录|知识库|文档数据库).*",
        r".*知识库里有什么.*",
        r".*查看.*(目录|内容|结构).*",
        r".*有哪些.*(文件|文件夹).*",
        r".*目录结构.*",
        r".*文件夹内容.*",
        r".*空间.*(列表|内容).*",
        r".*项目.*(列表|内容).*"
    ],
    "query": [
        r".*(查询|搜索|查找|检索).*知识库.*",
        r".*(查询|搜索|查找|检索).*",
        r".*帮我找.*",
        r".*找一下.*",
        r".*搜索一下.*",
        r".*查询一下.*",
        r".*检索一下.*"
    ],
    "read": [
        r".*阅读.*知识库.*",
        r".*读取.*知识库.*",
        r".*(读取|阅读|查看).*内容.*",
        r".*打开.*文件.*",
        r".*看看.*文件.*",
        r".*查看.*文件.*",
        r".*阅读.*文档.*",
        r".*获取.*内容.*",
        r".*总结.*文件.*",
        r".*提取.*信息.*"
    ],
    "upload": [
        r".*(上传|保存|归档).*(康哲|玄关|德镁)知识库.*",
        r".*存到.*(康哲|玄关|德镁)知识库.*",
        r".*保存到.*(康哲|玄关|德镁)知识库.*",
        r".*上传到.*(康哲|玄关|德镁)知识库.*",
        r".*归档到.*(康哲|玄关|德镁)知识库.*",
        r".*(上传|保存|归档).*文档数据库.*",
        r".*存到.*文档数据库.*",
        r".*保存到.*文档数据库.*",
        r".*上传到.*文档数据库.*",
        r".*归档到.*文档数据库.*",
        r".*(上传|保存|归档).*知识库.*",
        r".*存到.*知识库.*",
        r".*保存到.*知识库.*",
        r".*上传到.*知识库.*",
        r".*归档到.*知识库.*",
        r".*新建.*文件.*"
    ],
    "delete": [
        r".*(删除|移除|删掉).*文件.*",
        r".*删除.*文档.*",
        r".*移除.*文件.*"
    ],
    "manage": [
        r".*(重命名|改名为|移动).*",
        r".*更新.*(康哲|玄关|德镁)知识库.*",
        r".*更新.*文档数据库.*",
        r".*更新.*知识库.*",
        r".*(版本|历史).*",
        r".*定稿.*",
        r".*版本管理.*",
        r".*历史版本.*",
        r".*更新内容.*",
        r".*存成新版本.*"
    ]
}

# 优先级顺序（确保更具体的意图优先匹配）
INTENT_PRIORITY = ["read", "query", "upload", "delete", "manage", "browse"]

def match_intent(user_input):
    """匹配用户意图"""
    # 按优先级顺序匹配
    for intent in INTENT_PRIORITY:
        for pattern in INTENT_PATTERNS.get(intent, []):
            if re.match(pattern, user_input, re.IGNORECASE):
                return intent
    return None

def extract_keywords(user_input):
    """从用户输入中提取关键词"""
    keywords = []
    
    # 提取引号内内容
    quote_patterns = [r"“([^”]+)”", r'"([^"]+)"', r"'([^']+)'"]
    for pattern in quote_patterns:
        matches = re.findall(pattern, user_input)
        keywords.extend(matches)
    
    # 提取文件名格式内容（以文件、资料、政策、文档结尾）
    file_pattern = r"([\u4e00-\u9fa5a-zA-Z0-9_\-\s]+?)\s*(文件|资料|政策|文档)"
    matches = re.findall(file_pattern, user_input)
    for match in matches:
        keywords.append(match[0].strip())
    
    # 提取括号内内容
    bracket_pattern = r"[（(]([^）)]+)[）)]"
    matches = re.findall(bracket_pattern, user_input)
    keywords.extend(matches)
    
    return list(filter(None, keywords))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "resultCode": -1, 
            "resultMsg": "缺少输入参数",
            "data": {}
        }, ensure_ascii=False))
        sys.exit(1)
    
    user_input = sys.argv[1]
    intent = match_intent(user_input)
    keywords = extract_keywords(user_input)
    
    result = {
        "resultCode": 0,
        "resultMsg": "success",
        "data": {
            "intent": intent,
            "keywords": keywords,
            "input": user_input
        }
    }
    
    print(json.dumps(result, ensure_ascii=False))