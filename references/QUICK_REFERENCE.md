# 快速参考卡 - 智能导航（空间+目录）

## 何时使用智能导航？

当用户输入包含以下模式时，触发智能导航流程：

### 空间匹配触发
- "保存到XXX"、"上传到XXX"
- "搜索XXX里的..."、"查询XXX中的..."
- "打开XXX"、"浏览XXX"
- "XXX知识库"、"XXX空间"

### 目录导航触发
- "放到XXX目录"、"存到XXX文件夹"
- "上传到XXX/YYY"（多级路径）
- "保存到XXX目录里"

## 快速流程（4步）

### 步骤1️⃣：提取参数
```bash
python3 parameter-extractor.py "保存到康哲知识库的产品资料目录"
```
→ 获取 `project_name_candidates`, `folder_name_candidates` 和相应标记

### 步骤2️⃣：匹配空间（如果 needs_project_list）
```bash
# 上传场景
python3 browse/get-uploadable-list.py

# 查询/浏览场景
python3 browse/get-project-list.py

# 智能匹配
python3 project-matcher.py \
  --candidates "康哲,知识库" \
  --project-list '[...]'
```

### 步骤3️⃣：导航目录（如果 needs_folder_navigation）
```bash
# 按目录名搜索
python3 folder-navigator.py \
  --project-id 10001 \
  --folder-name "产品资料"

# 或按路径导航
python3 folder-navigator.py \
  --project-id 10001 \
  --folder-path "产品资料/慷彼申"
```

### 步骤4️⃣：执行操作
使用获得的 `project_id` 和 `folder_id` 执行实际操作

## 匹配结果处理

### 空间匹配结果

| match_type | match_count | 处理方式 |
|-----------|-------------|---------|
| exact | 1 | ✅ 直接使用 |
| best_match | 1 | ✅ 直接使用（可告知） |
| fuzzy | 1 | ⚠️ 建议确认后使用 |
| multiple | ≥2 | 📋 列出让用户选择 |
| none | 0 | 📋 列出所有空间 |

### 目录匹配结果

| match_type | match_count | 处理方式 |
|-----------|-------------|---------|
| exact | 1 | ✅ 直接使用 |
| fuzzy | 1 | ⚠️ 建议确认后使用 |
| multiple | ≥2 | 📋 列出完整路径让用户选择 |
| none | 0 | 💡 建议创建或浏览目录结构 |

## AI 输出模板

### ✅ 完整匹配（空间+目录）
```
已识别目标位置 ✅
  空间：康哲知识库
  目录：产品资料

正在保存文件...
```

### 📋 空间多个匹配
```
找到多个匹配的空间：
1. 康哲知识库（精确匹配）
2. 康哲研发中心（包含匹配）

请选择序号或空间名称。
```

### 📋 目录多个匹配
```
在"康哲知识库"中找到多个"产品资料"目录：
1. 产品资料（路径：产品资料）
2. 产品资料备份（路径：归档/产品资料备份）

请选择序号。
```

### 💡 目录未找到
```
未找到"产品资料"目录。

你可以：
1. 创建新目录"产品资料"
2. 浏览"康哲知识库"的目录结构
3. 保存到根目录

请选择。
```

## 决策树

```text
用户输入
    ↓
提取参数 (parameter-extractor.py)
    ↓
needs_project_list?
    ├─ Yes → 空间匹配流程
    │         ├─ 获取空间列表
    │         ├─ 智能匹配
    │         └─ 得到 project_id
    └─ No → 使用上下文或询问
    ↓
needs_folder_navigation?
    ├─ Yes → 目录导航流程
    │         ├─ 递归搜索/路径导航
    │         ├─ 智能匹配
    │         └─ 得到 folder_id
    └─ No → 使用根目录或默认目录
    ↓
执行操作
```

## 接口选择速查

| 场景 | 空间列表接口 | 说明 |
|-----|------------|------|
| 上传/保存/归档 | get-uploadable-list.py | 仅返回有写权限的空间 |
| 搜索/查询/浏览 | get-project-list.py | 返回所有可访问的空间 |
| 删除/移动/重命名 | get-uploadable-list.py | 需要写权限 |

## 常用命令速查

```bash
# 空间匹配（上传场景）
python3 browse/get-uploadable-list.py | \
  python3 project-matcher.py --candidates "康哲,知识库" --project-list "$(cat -)"

# 空间匹配（查询场景）
python3 browse/get-project-list.py | \
  python3 project-matcher.py --candidates "玄关" --project-list "$(cat -)"

# 目录搜索（单层）
python3 folder-navigator.py \
  --project-id 10001 \
  --folder-name "产品资料" \
  --max-depth 3

# 目录导航（多层）
python3 folder-navigator.py \
  --project-id 10001 \
  --folder-path "产品资料/慷彼申"

# 跨空间搜索目录
python3 folder-navigator.py \
  --project-ids "10001,10002,10003" \
  --folder-name "AI生成"
```

## 关键点

### ✅ DO
1. **先列举再匹配**，不要盲目搜索
2. **分层导航**，先空间后目录
3. **支持模糊匹配**，容忍用户输入不完整
4. **提供清晰反馈**，告诉用户识别到了什么
5. **多个匹配时列出完整信息**（路径、空间等）
6. **记录上下文**，减少重复询问
7. **递归搜索目录**，但限制深度避免性能问题

### ❌ DON'T
1. 不要直接用分词结果搜索空间或目录
2. 不要简单说"找不到"或"无权限"
3. 不要忽略用户的上下文
4. 不要无限递归搜索
5. 不要假设用户知道 ID 或完整路径
6. 不要跳过匹配步骤

## 性能建议

- 空间列表缓存：5分钟
- 目录结构缓存：3分钟
- 递归搜索深度：最多3层
- 网络超时：60秒
- 失败重试：最多3次
