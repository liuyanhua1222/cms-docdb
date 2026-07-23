# 智能导航完整指南 - 空间+目录双重匹配

## 企业应用先筛（必读）

意图或通道不明时，**禁止**直接猜 appCode：

1. `get-app-list.py` 拉本企业可用应用
2. `app_code_router.py "用户话术" --apps '<listAll data JSON>'` 求交
3. 唯一则直用并 `context-manager.py set_app_code --app-code …`；多个则追问（只列本企业）
4. 再 `get-project-list.py --app-code …`

| 说法 | appCode |
|---|---|
| 法务文档 | `fw_doc` |
| 资料库 / 文档数据库 / 玄关知识库 | `kz_doc` |
| 康哲/德镁知识库 | `kz_knowledge_base` |

`bizCode`（如 `pmo`）≠ `appCode`。

## 问题概述

用户在使用知识库时，经常遇到两类匹配失败问题：

### 问题1：空间匹配失败
- 用户说："保存到康哲知识库"
- AI 说："找不到该空间" ❌
- 原因：分词错误（"康哲知识库" → "康哲" + "知识库"）

### 问题2：目录匹配失败
- 用户说："放到产品资料目录"
- AI 说："没有权限" 或 "找不到目录" ❌
- 原因：
  - 不知道在哪个空间找
  - 盲目搜索导致失败
  - 没有递归查找子目录

## 解决方案：分层智能导航

### 总体策略
```
用户输入 → 提取参数 → 1️⃣匹配空间 → 2️⃣导航目录 → 执行操作
```

### 完整流程图

```text
用户输入："保存到康哲知识库的产品资料目录"
    ↓
┌─────────────────────────────────────────┐
│ 步骤1: 参数提取                         │
│ parameter-extractor.py                 │
└─────────────────────────────────────────┘
    ↓
识别结果：
  • project_name_candidates: ["康哲", "知识库"]
  • folder_name_candidates: ["产品资料"]
  • needs_project_list: true
  • needs_folder_navigation: true
    ↓
┌─────────────────────────────────────────┐
│ 步骤2: 空间匹配                         │
│ get-uploadable-list.py                 │
│ project-matcher.py                     │
└─────────────────────────────────────────┘
    ↓
匹配到空间：
  • project_id: 10001
  • project_name: "康哲知识库"
  • match_type: "exact"
    ↓
┌─────────────────────────────────────────┐
│ 步骤3: 目录导航                         │
│ folder-navigator.py                    │
└─────────────────────────────────────────┘
    ↓
导航到目录：
  • folder_id: 20001
  • folder_name: "产品资料"
  • path: "产品资料"
  • match_type: "exact"
    ↓
┌─────────────────────────────────────────┐
│ 步骤4: 执行上传                         │
│ upload-content.py                      │
└─────────────────────────────────────────┘
    ↓
成功 ✅
```

## 详细流程

### 步骤1️⃣：参数提取

```bash
python3 -B <skill-dir>/scripts/parameter-extractor.py "保存到康哲知识库的产品资料目录"
```

**输出**：
```json
{
  "resultCode": 0,
  "data": {
    "parameters": {
      "project_name_candidates": ["康哲", "知识库"],
      "folder_name_candidates": ["产品资料"],
      "needs_project_list": true,
      "needs_folder_navigation": true
    },
    "missing_hint": "识别到空间名称：康哲, 知识库，需要先获取你有权限的空间列表进行匹配\n识别到目录名称：产品资料，需要在空间内查找匹配的目录"
  }
}
```

**支持的输入格式**：

| 用户输入 | 提取结果 |
|---------|---------|
| "保存到康哲知识库" | project: ["康哲","知识库"] |
| "放到产品资料目录" | folder: ["产品资料"] |
| "保存到康哲知识库的产品资料目录" | project: ["康哲","知识库"]<br>folder: ["产品资料"] |
| "上传到产品资料/慷彼申" | folder_path: "产品资料/慷彼申" |
| "存到AI生成文件夹" | folder: ["AI生成"] |

### 步骤2️⃣：空间匹配（已实现）

```bash
# 获取可上传空间
python3 -B <skill-dir>/scripts/browse/get-uploadable-list.py

# 智能匹配
python3 -B <skill-dir>/scripts/project-matcher.py --candidates "康哲,知识库" --project-list '[...]'
```

详见 [SPACE_MATCHING_GUIDE.md](./SPACE_MATCHING_GUIDE.md)

### 步骤3️⃣：目录导航（新增）

#### 场景A：按目录名搜索

```bash
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料" --max-depth 3
```

**输出**：
```json
{
  "resultCode": 0,
  "data": {
    "matched_folders": [
      {
        "id": 20001,
        "name": "产品资料",
        "parentId": 0,
        "path": "产品资料",
        "depth": 1,
        "match_score": 100,
        "match_reason": "精确匹配",
        "project_id": 10001
      }
    ],
    "match_count": 1,
    "match_type": "exact",
    "searched_projects": [10001]
  }
}
```

**特性**：
- ✅ 递归搜索（默认3层深度，可配置）
- ✅ 模糊匹配（相似度 > 0.6）
- ✅ 返回完整路径
- ✅ 支持跨空间搜索

#### 场景B：按路径导航（多级目录）

```bash
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申"
```

**输出**：
```json
{
  "resultCode": 0,
  "data": {
    "matched_folders": [
      {
        "id": 20002,
        "name": "慷彼申",
        "parentId": 20001
      }
    ],
    "match_count": 1,
    "match_type": "exact",
    "navigation_path": [
      {
        "level": 1,
        "name": "产品资料",
        "id": 20001,
        "match_score": 100,
        "match_reason": "精确匹配"
      },
      {
        "level": 2,
        "name": "慷彼申",
        "id": 20002,
        "match_score": 100,
        "match_reason": "精确匹配"
      }
    ],
    "project_id": 10001
  }
}
```

**特性**：
- ✅ 逐层匹配（每一层都支持模糊匹配）
- ✅ 返回完整导航路径
- ✅ 支持混合分隔符（/ 或 -）

#### 场景C：跨空间搜索目录

```bash
python3 -B <skill-dir>/scripts/folder-navigator.py --project-ids "10001,10002,10003" --folder-name "AI生成"
```

**用途**：当用户没明确说空间，但说了目录名时使用

**输出**：
```json
{
  "resultCode": 0,
  "data": {
    "matched_folders": [
      {
        "id": 20005,
        "name": "AI生成",
        "project_id": 10001,
        "path": "AI生成",
        "depth": 1,
        "match_score": 100
      },
      {
        "id": 30008,
        "name": "AI生成文档",
        "project_id": 10002,
        "path": "工作文档/AI生成文档",
        "depth": 2,
        "match_score": 85
      }
    ],
    "match_count": 2,
    "match_type": "multiple"
  }
}
```

### 步骤4️⃣：结果处理

根据匹配结果采取不同策略：

#### ✅ 唯一精确匹配
```python
if match_type == "exact" and match_count == 1:
    folder = matched_folders[0]
    # 直接使用
    upload_to_folder(folder['id'], folder['project_id'])
```

**AI 输出**：
```
已识别目标位置：
  空间：康哲知识库
  目录：产品资料
正在保存文件...
```

#### 📋 多个匹配
```python
if match_type == "multiple":
    # 列出让用户选择
    for i, folder in enumerate(matched_folders):
        print(f"{i+1}. {folder['name']} (路径: {folder['path']})")
```

**AI 输出**：
```
找到多个"产品资料"目录：
1. 产品资料（路径：产品资料）- 康哲知识库
2. 产品资料备份（路径：归档/产品资料备份）- 康哲知识库

请选择序号。
```

#### ❌ 无匹配
```python
if match_type == "none":
    # 建议创建或列出可用目录
    suggest_create_or_browse()
```

**AI 输出**：
```
未找到"产品资料"目录。

你可以：
1. 创建新目录"产品资料"
2. 浏览"康哲知识库"的目录结构来选择其他位置
3. 保存到根目录

请选择。
```

## 完整示例

### 示例1：完整路径（空间+目录）

**用户输入**：
```
"把这份报告保存到康哲知识库的产品资料目录"
```

**AI 执行**：
```bash
# 1. 提取参数
python3 -B <skill-dir>/scripts/parameter-extractor.py "..."
# → project: ["康哲","知识库"], folder: ["产品资料"]

# 2. 匹配空间
python3 -B <skill-dir>/scripts/browse/get-uploadable-list.py
python3 -B <skill-dir>/scripts/project-matcher.py --candidates "康哲,知识库" --project-list '[...]'
# → project_id: 10001, name: "康哲知识库"

# 3. 导航目录
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料"
# → folder_id: 20001, name: "产品资料"

# 4. 执行上传
python3 -B <skill-dir>/scripts/upload/upload-content.py "报告内容" "报告.md" --project-id 10001 --folder-name "产品资料" --confirm YES
```

**AI 输出**：
```
已保存到知识库 ✅

文件：报告.md
空间：康哲知识库
位置：康哲知识库 / 产品资料

[下载链接]
```

### 示例2：仅目录名（需要推断空间）

**用户输入**：
```
"放到AI生成目录"
```

**AI 执行**：
```bash
# 1. 提取参数
python3 -B <skill-dir>/scripts/parameter-extractor.py "..."
# → folder: ["AI生成"], 无 project

# 2. 策略选择：
#    - 如果上下文有当前空间 → 直接在该空间查找
#    - 如果没有 → 跨所有可上传空间查找

# 2a. 无上下文 → 获取所有可上传空间
python3 -B <skill-dir>/scripts/browse/get-uploadable-list.py
# → projects: [10001, 10002, 10003]

# 3. 跨空间搜索目录
python3 -B <skill-dir>/scripts/folder-navigator.py --project-ids "10001,10002,10003" --folder-name "AI生成"
# → 找到2个匹配
```

**AI 输出**：
```
找到多个"AI生成"目录：
1. AI生成（康哲知识库 / AI生成）
2. AI生成文档（玄关知识库 / 工作文档 / AI生成文档）

请选择序号或空间名称。
```

### 示例3：多级路径

**用户输入**：
```
"上传到产品资料/慷彼申/临床研究"
```

**AI 执行**：
```bash
# 1. 提取参数
python3 -B <skill-dir>/scripts/parameter-extractor.py "..."
# → folder_path: "产品资料/慷彼申/临床研究"

# 2. 需要空间上下文
#    - 如果上下文有 → 直接使用
#    - 如果没有 → 询问用户

# 假设上下文有：current_project_id = 10001

# 3. 路径导航
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申/临床研究"
# → 逐层导航，返回最终目录

# 4. 执行上传
```

**AI 输出**：
```
已导航到目标目录 ✅

空间：康哲知识库
路径：产品资料 → 慷彼申 → 临床研究

正在保存文件...
```

## 决策树

### 何时使用哪个工具？

```text
用户输入
    ↓
是否提到空间名？
    ├─ 是 → parameter-extractor.py
    │        ↓
    │      needs_project_list == true?
    │        ↓
    │      get-uploadable-list.py / get-project-list.py
    │        ↓
    │      project-matcher.py
    │        ↓
    │      得到 project_id
    │
    └─ 否 → 使用上下文或询问
             ↓
           得到 project_id
    ↓
是否提到目录名/路径？
    ├─ 是 → parameter-extractor.py
    │        ↓
    │      needs_folder_navigation == true?
    │        ↓
    │      folder-navigator.py
    │        ↓
    │      得到 folder_id
    │
    └─ 否 → 保存到根目录或默认目录
    ↓
执行操作（上传/搜索/浏览等）
```

## 性能优化

### 缓存策略
```python
# 缓存空间列表（5分钟）
project_list_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 300  # 5分钟
}

# 缓存目录结构（3分钟）
folder_structure_cache = {
    f'{project_id}': {
        'folders': [...],
        'timestamp': 0,
        'ttl': 180  # 3分钟
    }
}
```

### 搜索深度控制
```python
# 默认搜索3层，避免过深递归
max_depth = 3

# 如果前3层没找到，询问用户是否继续
if not matched and depth >= max_depth:
    ask_user_to_continue_search()
```

## 错误处理

### 常见错误及处理

| 错误场景 | 处理方式 |
|---------|---------|
| 空间不存在 | 列出所有可用空间 |
| 目录不存在 | 建议创建或列出可选目录 |
| 无权限访问空间 | 提示用户申请权限 |
| 无权限上传到目录 | 提示权限不足，建议选择其他目录 |
| 网络超时 | 重试3次，失败后提示用户 |
| 路径导航中断 | 显示已导航到的层级，建议用户调整 |

## 最佳实践

### ✅ DO
1. **总是先列举再匹配**，不要盲目搜索
2. **支持模糊匹配**，用户可能输入不完整
3. **提供清晰反馈**，告诉用户识别到了什么
4. **多个匹配时列出选项**，让用户决策
5. **记录上下文**，减少重复询问

### ❌ DON'T
1. 不要直接用分词结果搜索
2. 不要简单说"找不到"
3. 不要忽略用户的上下文
4. 不要无限递归搜索目录
5. 不要假设用户知道 ID

## 总结

通过**分层智能导航**（空间匹配 + 目录导航），我们解决了用户使用知识库时的两大痛点：

1. ✅ **空间匹配准确**：先列举可用空间，再智能匹配
2. ✅ **目录查找智能**：递归搜索，支持模糊匹配和路径导航
3. ✅ **用户体验友好**：提供清晰反馈和多选项
4. ✅ **性能优化**：缓存 + 深度控制
5. ✅ **容错能力强**：多种匹配策略，失败时有兜底

这套方案大幅提升了小龙虾调用 skill 的精准度和用户满意度。
