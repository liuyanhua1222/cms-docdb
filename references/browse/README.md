# browse — 模块说明

## 目录

- 适用场景
- 鉴权模式
- 脚本清单
- 输入要求
- 参数详细说明
- 动作列表
- 输出说明
- 标准流程
- 运行方式速查

## 适用场景

- 用户说"帮我看看知识库里有什么"、"列出我的空间"
- 用户想浏览某个目录下的内容
- 用户想了解可以访问哪些空间
- 用户需要在保存文件前确定目标空间

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/browse/get-project-list.py` | `GET /open-api/document-database/project/list` | 获取有权限访问的所有空间列表 |
| `scripts/browse/get-personal-project-id.py` | `GET /open-api/document-database/project/personal/getProjectId` | 获取当前用户的个人知识库空间 ID |
| `scripts/browse/get-uploadable-list.py` | `GET /open-api/document-database/project/uploadableList` | 获取有上传/编辑权限的空间列表 |
| `scripts/browse/get-level1-folders.py` | `GET /open-api/document-database/file/getLevel1Folders` | 拉取项目空间根目录下的所有内容 |
| `scripts/browse/browse.py` | `GET /open-api/document-database/file/getChildFiles` | 浏览指定目录下的直接子项 |
| `scripts/browse/get-recent-files.py` | `POST /open-api/document-database/project/personal/getRecentFiles` | 获取当前用户最近上传的文件列表（个人库捷径） |
| `scripts/browse/get-my-upload-records.py` | `GET /open-api/document-database/operationLog/getMyUploadRecords` | 分页查询全空间上传/新建记录（默认近90天，无需传 operations） |

运行前先按 `cms-auth-skills/SKILL.md` 设置 `XG_BIZ_API_KEY` 或 `XG_APP_KEY`。系统会自动检测 Python 命令，优先使用 `python3`，如不存在则使用 `python`。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 获取个人空间 ID | 无 | appCode |
| 列出所有可访问空间 | 无 | appCode, nameKey, bizCode |
| 列出可写空间 | 无 | appCode, nameKey, bizCode |
| 浏览项目根目录 | projectId | order, permissionQuery |
| 浏览指定目录 | parentId | type, order, excludeFileTypes, excludeFolderNames, returnFileDesc |
| 获取最近上传文件 | 无 | limit, searchKey |
| 查询全空间上传记录 | 无 | pageIndex, pageSize, projectId, startTime, endTime |

## 参数详细说明

### get-personal-project-id.py — 获取个人空间 ID

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用编码 | 应用标识字符串 | - |

### get-project-list.py — 列出所有可访问空间

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用编码 | 应用标识字符串 | - |
| `--name-key` | String | 否 | 空间名称关键词 | 任意字符串，用于模糊搜索 | - |
| `--biz-code` | String | 否 | 业务编码 | 业务标识字符串 | - |

### get-uploadable-list.py — 列出可写空间

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用编码 | 应用标识字符串 | - |
| `--name-key` | String | 否 | 空间名称关键词 | 任意字符串 | - |
| `--biz-code` | String | 否 | 业务编码 | 业务标识字符串 | - |

### get-level1-folders.py — 浏览项目根目录

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `project_id` | Long | 是 | 项目/空间 ID | 有效项目 ID（可通过 get-project-list.py 获取） | - |
| `--order` | Integer | 否 | 排序规则 | 枚举：`1`（更新倒序）、`2`（更新顺序）、`5`（名字倒序）、`6`（名字顺序） | - |
| `--permission-query` | String | 否 | 权限查询条件 | 权限标识字符串 | - |

### browse.py — 浏览指定目录

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `parent_id` | Long | 是 | 父目录 ID | 有效文件夹 ID，根目录传 0 | - |
| `--type` | Integer | 否 | 查询类型 | 枚举：`1`（只查文件夹）、`2`（只查文件） | - |
| `--order` | Integer | 否 | 排序规则 | 枚举：`1`（更新倒序）、`2`（更新顺序）、`3`（创建倒序）、`4`（创建顺序）、`5`（名字倒序）、`6`（名字顺序） | - |
| `--exclude-file-types` | String | 否 | 排除的文件业务分类 | 枚举：`work_report`、`work_plan`、`huiji`、`ai-report` 等，多个用逗号分隔 | - |
| `--exclude-folder-names` | String | 否 | 排除的文件夹名称 | 任意文件夹名称，多个用逗号分隔 | - |
| `--no-return-file-desc` | Boolean | 否 | 不返回文件描述 | 无值标志，存在即为 true | - |

### get-recent-files.py — 获取最近上传文件

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--limit` | Integer | 否 | 返回数量限制 | ≥1（默认 10） | - |
| `--search-key` | String | 否 | 搜索关键词 | 任意字符串 | - |

### get-my-upload-records.py — 全空间上传记录（推荐 Agent 使用）

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--page-index` | Integer | 否 | 页码 | 从 1 开始，默认 1 | - |
| `--page-size` | Integer | 否 | 每页条数 | 1–100，默认 20 | - |
| `--project-id` | Long | 否 | 限定空间 | 有效 projectId | - |
| `--start-time` | Long | 否 | 开始时间（毫秒） | 时间戳 | 与 endTime 成对使用 |
| `--end-time` | Long | 否 | 结束时间（毫秒） | 时间戳 | 不传则默认当前时间 |

> 服务端固定查询 `file_upload`、`upload2agent`、`create_file`、`create_folder`，详见 dev-guide **1.15**。

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
- **用途**: 获取当前用户最近上传的文件列表（个人库）
- **输出**: 返回文件列表，支持数量限制和关键字搜索

### 7. 查询全空间上传记录
- **脚本**: `get-my-upload-records.py`
- **用途**: 小龙虾/Agent 查询「我最近在全空间上传/新建了哪些文件」
- **输出**: 分页 `pageData`，含 `projectName`、`operation`、`fileName`、`ancestorNames` 等

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
   - 查看最近上传（个人库）→ `get-recent-files.py`
   - 查看全空间上传记录（含新建文件/文件夹）→ `get-my-upload-records.py`

## 用户感知与对话输出规范（建议）

### A. “打开知识库位置”（目录定位）

当用户希望“打开知识库位置/打开目录/看看这个文件在哪”时，推荐做法：

1. 若已知目标文件的 `parentId`（保存返回或上下文里有 last_file.parentId），直接调用：
   - `scripts/browse/browse.py <parentId>`
2. 若要给用户展示“面包屑路径”，优先使用文件对象里的：
   - `ancestorNames`（若接口返回）
3. 若用户希望继续下钻查看更深层目录，继续递归调用 `browse.py`。

推荐输出（面向用户）：

```text
已打开知识库位置 ✅

位置：{ancestorNames}
当前目录包含：{foldersCount} 个文件夹，{filesCount} 个文件

你可以继续让我进入某个子目录，或直接打开某个文件。
```

## 用户话术示例

- "帮我看看个人知识库里有什么"
- "浏览一下根目录"
- "查看 AI 研发中心这个空间"
- "我想保存文件，先看看有哪些空间可以写"

## 运行方式速查

```bash
python scripts/browse/get-project-list.py
python scripts/browse/get-personal-project-id.py
python scripts/browse/get-uploadable-list.py
python scripts/browse/get-level1-folders.py <project_id> [--order 1|2|5|6] [--permission-query <query>]
python scripts/browse/browse.py <parent_id> [--type 1|2] [--order 1|2|3|4|5|6] [--exclude-file-types "work_report,huiji"] [--exclude-folder-names "临时文件"]
python scripts/browse/get-recent-files.py [--limit 10] [--search-key "关键词"]
python scripts/browse/get-my-upload-records.py [--page-index 1] [--page-size 20] [--project-id <id>]
```
