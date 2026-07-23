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

所有动作统一使用 `appKey` 鉴权，运行时从小龙虾上下文变量 `appkey` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/browse/get-app-list.py` | `GET /open-api/document-database/app/listAll` | 当前企业可用应用通道（意图不明时先调用） |
| `scripts/browse/get-project-list.py` | `GET /open-api/document-database/project/list` | 获取有权限访问的所有空间列表 |
| `scripts/browse/get-personal-project-id.py` | `GET /open-api/document-database/project/personal/getProjectId` | 获取当前用户的个人知识库空间 ID |
| `scripts/browse/get-uploadable-list.py` | `GET /open-api/document-database/project/uploadableList` | 获取有上传/编辑权限的空间列表 |
| `scripts/browse/get-level1-folders.py` | `GET /open-api/document-database/file/getLevel1Folders` | 拉取项目空间根目录下的所有内容 |
| `scripts/browse/browse.py` | `GET /open-api/document-database/file/getChildFiles` | 浏览指定目录下的直接子项 |
| `scripts/browse/get-recent-files.py` | `POST /open-api/document-database/project/personal/getRecentFiles` | 获取当前用户最近上传的文件列表（个人库捷径） |
| `scripts/browse/get-my-upload-records.py` | `GET /open-api/document-database/operationLog/getMyUploadRecords` | 分页查询全空间上传/新建记录（默认近90天，无需传 operations） |
| `scripts/browse/get-my-recent-used.py` | `GET /open-api/document-database/operationLog/getMyRecentUsed` | 最近使用（预览/下载/Agent上传，与前端主页一致） |
| `scripts/browse/get-file-basic-info.py` | `GET /open-api/document-database/file/getFileBasicInfo` | 根据 fileId 查 projectId、type 等轻量元数据 |

运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 列出企业可用应用 | 无 | 无 |
| 获取个人空间 ID | 无 | appCode |
| 列出所有可访问空间 | 无（**强烈建议传 appCode**） | appCode, nameKey, bizCode |
| 列出可写空间 | 无（**强烈建议传 appCode**） | appCode, nameKey, bizCode |
| 浏览项目根目录 | projectId | order, permissionQuery |
| 浏览指定目录 | parentId | type, order, excludeFileTypes, excludeFolderNames, returnFileDesc |
| 获取最近上传文件 | 无 | limit, searchKey |
| 查询全空间上传记录 | 无 | pageIndex, pageSize, projectId, startTime, endTime |
| 查询文件/文件夹基本信息 | fileId | 无 |

## 参数详细说明

### get-app-list.py — 企业可用应用通道

无额外参数。返回 `[{ "name", "appCode" }]`。  
典型 appCode：`kz_doc`（资料库/玄关知识库）、`kz_knowledge_base`（康哲/德镁知识库）、`fw_doc`（法务文档）。

### get-personal-project-id.py — 获取个人空间 ID

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用编码 | `kz_doc` / `fw_doc` / `kz_knowledge_base` | - |

### get-project-list.py — 列出所有可访问空间

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用通道 | `kz_doc` / `fw_doc` / `kz_knowledge_base`；不传=后端企业默认 | 访问非默认通道时必传 |
| `--name-key` | String | 否 | 空间名称关键词 | 任意字符串 | - |
| `--biz-code` | String | 否 | 业务线编码 | 如 `pmo`（**不是** `kz_doc`） | 与 appCode 无关 |

### get-uploadable-list.py — 列出可写空间

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--app-code` | String | 否 | 应用通道 | 同 get-project-list | 建议先由 get-app-list 确定 |
| `--name-key` | String | 否 | 空间名称关键词 | 任意字符串 | - |
| `--biz-code` | String | 否 | 业务线编码 | 如 `pmo` | - |

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

### get-my-recent-used.py — 最近使用（与前端主页一致）

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--page-index` | Integer | 否 | 页码 | 从 1 开始，默认 1 | - |
| `--page-size` | Integer | 否 | 每页条数 | 1–100，默认 20 | - |
| `--biz-code` | String | 否 | 空间业务编码筛选 | 如 `pmo`（不是 `kz_doc`） | - |

> 服务端固定查询 `file_online_read`、`file_download`、`upload2agent`，详见 dev-guide **1.16**。

### get-file-basic-info.py — 文件/文件夹轻量元数据

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件或文件夹 ID | 有效 fileId | 上传前反查 projectId 时常用 |

> 返回 `projectId`、`type`、`parentId` 等，不含正文与权限子集，详见 dev-guide **1.17**。

## 动作列表

### 0. 列出企业可用应用通道
- **脚本**: `get-app-list.py`
- **用途**: 意图/通道不明时先调用；仅返回当前企业用户可访问的应用
- **输出**: `[{ "name", "appCode" }]`

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

### 8. 查询最近使用
- **脚本**: `get-my-recent-used.py`
- **用途**: 查询当前用户最近预览/下载/Agent 上传过的文件（与前端「最近使用」一致）
- **输出**: 分页 `pageData`，`operation` 为 `file_online_read` / `file_download` / `upload2agent`

### 9. 查询文件/文件夹基本信息
- **脚本**: `get-file-basic-info.py`
- **用途**: 根据 `fileId` 反查 `projectId`、判断文件/文件夹类型；上传到指定父目录前推荐使用
- **输出**: `FileBasicInfoVO`（含 `projectId`、`parentId`、`type` 等）

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
   - 查看最近使用（预览/下载）→ `get-my-recent-used.py`
   - 查看最近上传（个人库）→ `get-recent-files.py`
   - 查看全空间上传记录（含新建文件/文件夹）→ `get-my-upload-records.py`

4. **元数据反查（上传前）**：
   - 仅有 `fileId`/`parentId` 时 → `get-file-basic-info.py` 取得 `projectId` 后再调 `save-file-by-parent-id.py`

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
- "我最近看过哪些文件"
- "最近使用里有什么"
- "这个文件的 projectId 是多少"
- "查一下这个文件夹属于哪个空间"

## 运行方式速查

**重要说明**：以下示例使用相对路径以便阅读，实际执行时必须替换为绝对路径。例如：
- 文档示例：`python3 scripts/browse/browse.py <parent_id>`
- 实际执行：`python3 <skill-dir>/scripts/browse/browse.py <parent_id>`（将 `<skill-dir>` 换成 skill 根目录绝对路径）

禁止使用 `cd`、`&&`、管道等 shell 构造。每个脚本必须在单独的命令中使用绝对路径执行。

```bash
python3 scripts/browse/get-project-list.py
python3 scripts/browse/get-personal-project-id.py
python3 scripts/browse/get-uploadable-list.py
python3 scripts/browse/get-level1-folders.py <project_id> [--order 1|2|5|6] [--permission-query <query>]
python3 scripts/browse/browse.py <parent_id> [--type 1|2] [--order 1|2|3|4|5|6] [--exclude-file-types "work_report,huiji"] [--exclude-folder-names "临时文件"]
python3 scripts/browse/get-recent-files.py [--limit 10] [--search-key "关键词"]
python3 scripts/browse/get-my-upload-records.py [--page-index 1] [--page-size 20] [--project-id <id>]
python3 scripts/browse/get-my-recent-used.py [--page-index 1] [--page-size 20] [--biz-code pmo]
python3 scripts/browse/get-app-list.py
python3 scripts/browse/get-project-list.py --app-code fw_doc
python3 scripts/browse/get-project-list.py --app-code kz_doc
python3 scripts/browse/get-project-list.py --app-code kz_knowledge_base
python3 scripts/browse/get-file-basic-info.py <file_id>
```
