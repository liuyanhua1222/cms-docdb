# browse — 模块说明

## 适用场景

- 用户说"帮我看看知识库里有什么"、"列出我的空间"
- 用户想浏览某个目录下的内容
- 用户想了解可以访问哪些空间
- 用户需要在保存文件前确定目标空间

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 获取个人空间 ID | 无 | appCode |
| 列出所有可访问空间 | 无 | appCode, nameKey, bizCode |
| 列出可写空间 | 无 | appCode, nameKey, bizCode |
| 浏览项目根目录 | projectId | order, permissionQuery |
| 浏览指定目录 | parentId | type, order, excludeFileTypes, excludeFolderNames, returnFileDesc |
| 获取最近上传文件 | 无 | limit, searchKey |

## 动作列表

### 1. 获取个人空间 ID
- **脚本**: `get-personal-project-id.py`
- **用途**: 快速获取当前用户的个人知识库空间 ID
- **输出**: 返回 projectId（Long）

### 2. 列出所有可访问空间
- **脚本**: `get-project-list.py`
- **用途**: 获取当前账号有权限访问的所有空间列表
- **输出**: 返回空间列表，每个空间包含 id、name、remark、type、role 等信息

### 3. 列出可写空间
- **脚本**: `get-uploadable-list.py`
- **用途**: 获取当前账号有上传/编辑权限的空间列表（保存文件前必须调用）
- **输出**: 返回可写空间列表

### 4. 浏览项目根目录
- **脚本**: `get-level1-folders.py`
- **用途**: 拉取指定项目空间的绝对顶层（根目录）下的所有文件夹及文件
- **输出**: 返回文件和文件夹列表

### 5. 浏览指定目录
- **脚本**: `browse.py`
- **用途**: 浏览指定目录下的直接子项（文件和文件夹）
- **输出**: 返回文件和文件夹列表，支持类型过滤、排序、排除规则

### 6. 获取最近上传文件
- **脚本**: `get-recent-files.py`
- **用途**: 获取当前用户最近上传的文件列表
- **输出**: 返回文件列表，支持数量限制和关键字搜索

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

文件/文件夹对象包含字段：
- `id`: 文件/文件夹 ID
- `name`: 名称
- `type`: 1 文件夹，2 文件
- `parentId`: 父目录 ID
- `hasChild`: 是否有子项
- `size`: 文件大小（字节）
- `suffix`: 文件后缀
- `fileType`: 业务类型（doc/file/work_report 等）
- `ancestorNames`: 完整路径（斜杠分隔）
- `createTime`: 创建时间戳
- `createTimeStr`: 格式化时间

## 标准流程

1. **空间发现**：
   - 快速获取个人空间 → `get-personal-project-id.py`
   - 查看所有可访问空间 → `get-project-list.py`
   - 保存文件前查看可写空间 → `get-uploadable-list.py`

2. **目录浏览**：
   - 浏览项目根目录 → `get-level1-folders.py` + projectId
   - 浏览子目录 → `browse.py` + parentId
   - 继续下钻 → 递归调用 `browse.py`

3. **快速访问**：
   - 查看最近上传 → `get-recent-files.py`

## 用户话术示例

- "帮我看看个人知识库里有什么"
- "浏览一下根目录"
- "查看 AI 研发中心这个空间"
- "我想保存文件，先看看有哪些空间可以写"
