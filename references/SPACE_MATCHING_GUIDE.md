# 空间智能匹配使用指南

## 应用通道（必读）

拉空间列表前必须确定 **appCode**（产品通道，来自 `t_doc_app`）：

| 用户说法 | appCode |
|---|---|
| 法务文档 / 法务 | `fw_doc` |
| 康哲/德镁资料库、资料库、文档数据库 | `kz_doc` |
| 玄关知识库 | `kz_doc` |
| 康哲/德镁知识库 | `kz_knowledge_base` |
| 仅说「知识库」 | 先 `get-app-list.py`，企业可用应用求交后再定 |

流程：`get-app-list.py` → `app_code_router.py --apps '...'` → `get-project-list.py --app-code <code>`。

`bizCode`（如 `pmo`）是空间业务线，**不是** appCode；禁止写 `--biz-code kz_doc`。

## 概述

本指南说明如何在小龙虾（AI Agent）中正确处理用户提到的空间名称，避免因分词错误导致的匹配失败。

## 问题场景

### 典型用户输入
- "保存到康哲知识库"
- "搜索玄关知识库里的文件"
- "上传到德镁知识库"
- "查询知识库中的政策"

### 传统方法的问题
1. **分词不准确**：AI 可能将"康哲知识库"分成"康哲"、"知识库"两个词
2. **盲目搜索**：直接用分词结果去匹配，容易失败
3. **没有反馈**：即使用户有权限，也可能因为名称不匹配而报错"找不到空间"

## 优化方案

### 核心思想
**先列举，再匹配** - 不要盲目搜索，而是先获取用户实际有权限的空间列表，然后在列表中智能匹配

### 工作流程

#### 步骤1：意图识别
```bash
python3 /path/to/scripts/intent-matcher.py "保存到康哲知识库"
```

输出：
```json
{
  "resultCode": 0,
  "data": {
    "intent": "upload",
    "keywords": []
  }
}
```

#### 步骤2：参数提取（识别空间名候选词）
```bash
python3 /path/to/scripts/parameter-extractor.py "保存到康哲知识库"
```

输出：
```json
{
  "resultCode": 0,
  "data": {
    "parameters": {
      "project_name_candidates": ["康哲", "知识库"],  // 或 ["康哲知识库"]
      "needs_project_list": true
    },
    "missing_hint": "识别到空间名称：康哲, 知识库，需要先获取你有权限的空间列表进行匹配"
  }
}
```

**关键字段说明**：
- `project_name_candidates`: 从用户输入中提取的空间名称候选词
- `needs_project_list`: 标记为 true，表示需要先获取空间列表

#### 步骤3：获取空间列表

根据意图选择合适的接口：

**上传场景（upload）**：
```bash
# 获取有上传权限的空间
python3 /path/to/scripts/browse/get-uploadable-list.py
```

**查询/浏览场景（query/browse）**：
```bash
# 先企业可用应用（意图不明时必做）
python3 /path/to/scripts/browse/get-app-list.py

# 获取所有可访问的空间（必须带 appCode）
python3 /path/to/scripts/browse/get-project-list.py --app-code kz_knowledge_base
# 资料库 / 法务示例：
# python3 /path/to/scripts/browse/get-project-list.py --app-code kz_doc
# python3 /path/to/scripts/browse/get-project-list.py --app-code fw_doc
```

输出示例：
```json
{
  "resultCode": 1,
  "data": [
    {"id": 10001, "name": "康哲知识库", "role": "owner"},
    {"id": 10002, "name": "玄关知识库", "role": "member"},
    {"id": 10003, "name": "德镁知识库", "role": "member"},
    {"id": 10004, "name": "个人知识库", "role": "owner"}
  ]
}
```

#### 步骤4：智能匹配

```bash
python3 /path/to/scripts/project-matcher.py \
  --candidates "康哲,知识库" \
  --project-list '[{"id":10001,"name":"康哲知识库"},{"id":10002,"name":"玄关知识库"}]'
```

输出示例：
```json
{
  "resultCode": 0,
  "data": {
    "matched_projects": [
      {
        "id": 10001,
        "name": "康哲知识库",
        "match_score": 95,
        "match_reason": "组合精确匹配：'康哲+知识库'",
        "role": "owner"
      }
    ],
    "match_count": 1,
    "match_type": "exact"
  }
}
```

**match_type 说明**：
- `exact`: 精确匹配（分数 >= 95），可直接使用
- `fuzzy`: 模糊匹配（分数 60-94），建议确认
- `best_match`: 有明显最佳匹配（第一名比第二名高20分以上）
- `multiple`: 多个匹配，需要用户选择
- `none`: 无匹配，需要列出所有空间让用户选择

#### 步骤5：结果处理

**场景A：唯一精确匹配（match_type = "exact" 且 match_count = 1）**
```python
# 直接使用匹配到的空间
project_id = matched_projects[0]['id']
project_name = matched_projects[0]['name']

# 继续执行上传/搜索等操作
```

AI 输出示例：
```
已识别目标空间：康哲知识库 ✅
正在保存文件...
```

**场景B：多个匹配（match_type = "multiple"）**
```python
# 列出所有匹配结果让用户选择
```

AI 输出示例：
```
找到多个匹配的空间，请选择：
1. 康哲知识库（精确匹配）
2. 康哲研发知识库（包含匹配）

请回复序号或空间名称。
```

**场景C：无匹配（match_type = "none"）**
```python
# 列出所有可用空间让用户选择
```

AI 输出示例：
```
未找到匹配"康哲知识库"的空间。

你有上传权限的空间：
1. 玄关知识库
2. 德镁知识库
3. 个人知识库

请选择目标空间，或回复空间名称。
```

## 匹配策略详解

`project-matcher.py` 使用以下策略进行智能匹配（按优先级排序）：

### 1. 精确匹配（分数：100）
候选词完全匹配项目名称（忽略大小写和空格）
- 输入：`["康哲知识库"]`
- 匹配：`"康哲知识库"` ✅

### 2. 包含匹配（分数：75-90）
- 项目名称包含候选词
  - 输入：`["康哲"]`
  - 匹配：`"康哲知识库"` ✅
- 候选词包含项目名称
  - 输入：`["康哲知识库管理系统"]`
  - 匹配：`"康哲知识库"` ✅

### 3. 组合匹配（分数：70-95）
多个候选词组合后匹配
- 输入：`["康哲", "知识库"]`
- 组合：`"康哲知识库"`
- 匹配：`"康哲知识库"` ✅

### 4. 模糊匹配（分数：36-65）
基于字符串相似度（需要相似度 > 0.6）
- 输入：`["康泽知识库"]`（用户打错字）
- 匹配：`"康哲知识库"` ✅（相似度 0.89）

### 匹配阈值
- 分数 >= 60 才认为是有效匹配
- 分数越高，匹配越可靠

## 完整示例

### 示例1：上传文件到康哲知识库

**用户输入**：
```
"把这份报告保存到康哲知识库"
```

**AI 执行流程**：

```bash
# 1. 意图识别
intent="upload"

# 2. 参数提取
candidates=["康哲", "知识库"]
needs_project_list=true

# 3. 获取可上传空间
python3 scripts/browse/get-uploadable-list.py
# 返回：[{"id":10001,"name":"康哲知识库"}, {"id":10002,"name":"玄关知识库"}, ...]

# 4. 智能匹配
python3 scripts/project-matcher.py \
  --candidates "康哲,知识库" \
  --project-list '[...]'
# 返回：match_type="exact", matched_projects=[{"id":10001,"name":"康哲知识库"}]

# 5. 直接使用匹配结果
python3 scripts/upload/upload-content.py \
  "报告内容" \
  "报告.md" \
  --project-id 10001
```

**AI 输出**：
```
已保存到知识库 ✅

文件：报告.md
空间：康哲知识库
位置：康哲知识库 / AI生成

你继续让我修改这份文档时，我会更新到同一个知识库文件（通过版本管理生成新版本）。
```

### 示例2：搜索文件（空间名不完整）

**用户输入**：
```
"搜索康哲里的政策文件"
```

**AI 执行流程**：

```bash
# 1. 意图识别
intent="query"

# 2. 参数提取
candidates=["康哲"]
keywords=["政策文件"]
needs_project_list=true

# 3. 获取可访问空间
python3 scripts/browse/get-project-list.py
# 返回：[{"id":10001,"name":"康哲知识库"}, {"id":10003,"name":"康哲研发中心"}, ...]

# 4. 智能匹配
python3 scripts/project-matcher.py \
  --candidates "康哲" \
  --project-list '[...]'
# 返回：match_type="multiple", matched_projects=[
#   {"id":10001,"name":"康哲知识库","match_score":85},
#   {"id":10003,"name":"康哲研发中心","match_score":82}
# ]

# 5. 让用户选择
```

**AI 输出**：
```
找到多个包含"康哲"的空间：
1. 康哲知识库
2. 康哲研发中心

请问你要在哪个空间搜索？或者我可以在所有这些空间中搜索。
```

### 示例3：搜索（未指定空间）

**用户输入**：
```
"搜索政策文件"
```

**AI 执行流程**：

```bash
# 1. 意图识别
intent="query"

# 2. 参数提取
candidates=[]  # 未提取到空间名
keywords=["政策文件"]
needs_project_list=false

# 3. 直接在所有空间搜索
python3 scripts/query/search.py "政策文件"
```

## 代码集成示例

### Python 示例

```python
import json
import subprocess

def smart_upload_to_project(user_input, content, filename):
    """智能上传文件到用户指定的空间"""
    
    # 1. 参数提取
    result = subprocess.run(
        ['python3', 'scripts/parameter-extractor.py', user_input],
        capture_output=True, text=True
    )
    params = json.loads(result.stdout)['data']['parameters']
    
    # 2. 检查是否需要空间匹配
    if not params.get('needs_project_list'):
        # 没有指定空间，使用个人库
        return upload_content(content, filename)
    
    # 3. 获取可上传空间列表
    result = subprocess.run(
        ['python3', 'scripts/browse/get-uploadable-list.py'],
        capture_output=True, text=True
    )
    project_list = json.loads(result.stdout)['data']
    
    # 4. 智能匹配
    candidates = ','.join(params['project_name_candidates'])
    result = subprocess.run(
        ['python3', 'scripts/project-matcher.py',
         '--candidates', candidates,
         '--project-list', json.dumps(project_list)],
        capture_output=True, text=True
    )
    match_result = json.loads(result.stdout)['data']
    
    # 5. 根据匹配结果处理
    if match_result['match_type'] in ['exact', 'best_match'] and match_result['match_count'] == 1:
        # 唯一匹配，直接使用
        project = match_result['matched_projects'][0]
        return upload_content(content, filename, project_id=project['id'])
    
    elif match_result['match_type'] == 'multiple':
        # 多个匹配，返回让用户选择
        return {
            'status': 'need_selection',
            'message': '找到多个匹配的空间，请选择：',
            'projects': match_result['matched_projects']
        }
    
    else:
        # 无匹配，列出所有空间
        return {
            'status': 'need_selection',
            'message': '未找到匹配的空间。你有上传权限的空间：',
            'projects': project_list
        }

def upload_content(content, filename, project_id=None):
    """执行实际上传"""
    cmd = ['python3', 'scripts/upload/upload-content.py', content, filename]
    if project_id:
        cmd.extend(['--project-id', str(project_id)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

## 注意事项

### 1. 必须先列举再匹配
❌ **错误做法**：
```python
# 直接搜索空间（可能因分词错误失败）
search_project_by_name("康哲 知识库")
```

✅ **正确做法**：
```python
# 先获取空间列表，再在列表中匹配
projects = get_uploadable_list()
matched = match_projects(["康哲", "知识库"], projects)
```

### 2. 根据意图选择合适的空间列表接口
- **上传/新建** → `get-uploadable-list.py`（仅可写空间）
- **搜索/浏览/下载** → `get-project-list.py`（所有可访问空间）

### 3. 处理匹配结果时的建议
- 精确匹配（exact）→ 直接使用，无需确认
- 最佳匹配（best_match）→ 可直接使用，也可告知用户
- 多个匹配（multiple）→ 必须让用户选择
- 无匹配（none）→ 列出所有空间，让用户选择或重新输入

### 4. 用户体验优化
- 匹配成功时，告知用户识别到的空间名称
- 匹配失败时，不要简单说"找不到"，而是列出可选空间
- 支持用户直接输入空间 ID 或序号进行选择

## 常见问题

### Q1: 为什么不直接用关键词搜索空间？
A: 因为分词不准确，"康哲知识库"可能被分成"康哲"+"知识库"，直接搜索容易失败。先获取实际列表再匹配更可靠。

### Q2: 匹配器会不会太慢？
A: 不会。空间列表通常只有几十个，匹配算法是 O(n)，几乎瞬间完成。

### Q3: 如果用户输入的空间名完全错误怎么办？
A: 匹配器会返回 `match_type="none"`，此时列出所有可用空间让用户选择。

### Q4: 支持缩写吗？
A: 支持。比如"康哲"可以匹配"康哲知识库"，但建议相似度不要太低（< 0.6）。

## 总结

采用"先列举，再匹配"的策略，可以有效解决用户上传/搜索时空间名称匹配失败的问题：

1. ✅ 避免分词错误
2. ✅ 提高匹配准确率
3. ✅ 提供更好的用户体验（有选择提示）
4. ✅ 减少"找不到空间"的错误

建议在所有涉及空间选择的场景（上传、搜索、浏览）中都使用这个流程。
