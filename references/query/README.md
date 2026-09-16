# query — 模块说明

> **调用方式（强制）**：标准 `exec` + python3 -B <skill-dir>/scripts/...；将 `<skill-dir>` 换成本 skill 根目录绝对路径；命令含业务参数 + 可选 `--app-key`。


## 目录

- 适用场景
- 鉴权模式
- 脚本清单
- 输入要求
- 参数详细说明
- 动作列表
- 输出说明
- 标准流程
- 预览与下载
- 运行方式速查

## 适用场景

- 用户说"帮我找一下 xxx 文件"、"搜索 xxx"
- 用户想找到某个文件并获取其内容、下载链接或预览链接
- AI Agent 需要读取文件内容进行分析、总结或 RAG 消费

## 鉴权模式

见 [`common-params.md`](../common-params.md)。可选 `--app-key`；未传时由脚本自行获取。旧条款「不得传入 AppKey」已废止。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/query/search.py` | `GET /open-api/document-database/file/searchFile` | 搜索文件或目录 |
| `scripts/query/get-full-content.py` | `GET /open-api/document-database/file/getFullFileContent` | 获取文件全局提纯文本（Markdown），RAG 入口 |
| `scripts/query/get-download-info.py` | `GET /open-api/document-database/file/getDownloadInfo` | 默认获取正式 `previewUrl`；显式 `--force-download` 才选择下载链接 |
| `scripts/query/download-file.py` | `GET /open-api/document-database/file/getDownloadInfo` + 本地下载 | 下载文件到本地，解决内网 URL 无法被 AI 工具访问的问题 |
| `scripts/query/get-file-content.py` | `GET /open-api/document-database/file/getFileContent` | 分页获取文件文本内容 |
| `scripts/query/batch-get-content.py` | `POST /open-api/document-database/ai/batchGetContent` | 批量获取多个文件全文，建议≤10个 |
| `scripts/query/list-descendant-files.py` | `GET /open-api/document-database/file/listDescendantFiles` | 子树扁平列举（冷启动同步） |
| `scripts/query/list-changes.py` | `GET /open-api/document-database/file/listChanges` | 增量变更列表（since/cursor） |
| `scripts/query/batch-get-meta.py` | `POST /open-api/document-database/file/batchGetMeta` | 按 fileId 批量查元数据（无正文） |
| `scripts/query/batch-download-files.py` | `getDownloadInfo` + 本地下载 | 受控批量下载（默认并发 2，B-03） |


## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 搜索文件 | nameKey（关键词）, projectId | rootFileId, startTime, endTime, excludeFileTypes, excludeFolderNames |
| 获取文件全文 | fileId | relationId, fileType |
| 获取下载/预览凭据 | fileId | forceDownload, versionNumber |
| 下载文件到本地 | fileId | output |
| 分页读取文件内容 | fileId | pageNumber |
| 批量获取文件全文 | files（fileId 列表） | maxChars, maxCharsPerFile |
| 子树扁平列举 | rootFileId | projectId, suffix, cursor, limit, includePath, includeFolders |
| 增量变更列表 | （无强制必填；建议 projectId+since/cursor） | projectId, rootFileId, since, cursor, limit, includePath, includeMoveHint |
| 批量查元数据 | fileIds（`--file-ids` 或 `--files-json`） | — |

## 参数详细说明

### search.py — 搜索文件

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--name-key` | String | 是 | 搜索关键词，支持模糊匹配 | 任意字符串，中文需 URL 编码（UTF-8） | - |
| `--project-id` | Long | 是 | 项目/空间 ID，限定搜索范围 | 有效项目 ID（可通过 get-project-list.py 获取） | - |
| `--root-file-id` | Long | 否 | 指定根目录 ID，在此目录下搜索 | 有效文件 ID（文件夹类型） | 需在 project-id 对应的项目内 |
| `--start-time` | Long | 否 | 创建时间-开始时间戳（毫秒） | Unix 时间戳（毫秒），如 1704067200000 | 通常与 --end-time 配对使用 |
| `--end-time` | Long | 否 | 创建时间-结束时间戳（毫秒） | Unix 时间戳（毫秒），如 1704153600000 | 通常与 --start-time 配对使用 |
| `--is-file-storage` | Boolean | 否 | 是否搜索文件存储区 | true/false（默认 false） | - |
| `--permission-query` | String | 否 | 权限查询条件 | 权限标识字符串 | - |
| `--exclude-file-types` | String | 否 | 排除的文件业务分类 | 枚举：`work_report`（工作汇报）、`work_plan`（工作计划）、`huiji`（会议纪要）、`ai-report`（AI报告）等，多个用逗号分隔 | - |
| `--exclude-folder-names` | String | 否 | 排除的文件夹名称 | 任意文件夹名称，多个用逗号分隔，如 `临时文件,测试文件夹` | - |

### get-full-content.py — 获取文件全文

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--file-id` | Long | 是 | 文件 ID | 有效文件 ID（可通过 search.py 获取） | - |
| `--relation-id` | String | 否 | 业务关联 ID | 业务系统中的关联标识 | - |
| `--file-type` | String | 否 | 业务类型 | 枚举：`doc`（文档）、`file`（物理文件）、`work_report`（工作汇报）等 | - |

### get-download-info.py — 获取下载/预览凭据

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--file-id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--force-download` | Boolean | 否 | 强制获取下载链接（而非预览链接） | 无值标志，存在即为 true | - |
| `--version-number` | Integer | 否 | 指定版本号 | 有效版本号（可通过 get-version-list.py 获取） | - |

### download-file.py — 下载文件到本地

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--file-id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--output` | String | 否 | 本地保存路径 | 有效本地路径；不传则保存到系统临时目录 | - |

下载采用 1MB 分块写入（与 `download-file.py` 的 CHUNK_SIZE 一致），下载阶段最多重试 3 次，退避间隔为 1 秒、2 秒、4 秒。

输出路径默认在系统临时目录；绝对路径必须落在临时目录或环境变量 `CMS_DOCDB_DOWNLOAD_DIR` 指定根下（防路径穿越）。

**唯一默认预览路径**：调用 `get-download-info.py` 且不带 `--force-download`，使用返回的 `data.selectedUrl`（其来源固定为正式字段 `previewUrl`）。成功响应缺少 `previewUrl` 时，脚本保留服务端原始 `resultCode`，同时返回 `urlAvailable=false`、`urlError` 并以非零状态退出；不回退到 `downloadUrl`、`getShareUrl` 或 ticket 旁路。显式 `--force-download` 时对正式 `downloadUrl` 执行同样校验。`getShareUrl` 只属于已授权协同分享后的链接分发，不是普通打开/预览入口。

下载与上传的分块规则是两个独立链路：本地下载读取块为 **1MB**；multipart 整文件上传发送块为 **5MB**。两者均与当前实现一致，不应互相套用。

### get-file-content.py — 分页读取文件内容

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--file-id` | Long | 是 | 文件 ID | 有效文件 ID（文档类型，非物理文件） | - |
| `--page-number` | Integer | 否 | 页码 | ≥1（默认 1） | - |

### batch-get-content.py — 批量获取文件全文

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `files` | JSON String | 是 | 文件 ID 列表 | JSON 数组格式，如 `'[{"fileId":123},{"fileId":456}]'`，建议单次≤10个 | - |
| `--max-chars` | Integer | 否 | 内容字段总字符上限 | 默认 `0`，表示不限制；面向 LLM 消费时建议按上下文预算显式设置 | - |
| `--max-chars-per-file` | Integer | 否 | 单个内容字段字符上限 | 默认 `0`，表示不限制；面向 LLM 消费时建议按上下文预算显式设置 | - |

### list-descendant-files.py — 子树扁平列举

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--root-file-id` | Long | 是 | 映射根目录 | `0`=空间根；`>0` 为某文件夹 | rootFileId=0 时建议传 `--project-id` |
| `--project-id` | Long | 否 | 项目/空间 ID | 有效项目 ID | - |
| `--suffix` | String | 否 | 后缀过滤 | 默认 `md` | - |
| `--cursor` | String | 否 | 分页游标 | 上次响应 nextCursor | - |
| `--limit` | Integer | 否 | 每页条数 | 正整数 | - |
| `--include-path` | Boolean | 否 | 返回 relativePath | 标志位 | - |
| `--include-folders` | Boolean | 否 | 一并返回文件夹 | 标志位 | - |

### list-changes.py — 增量变更列表

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--project-id` | Long | 否 | 项目/空间 ID | 有效项目 ID | 强烈建议传 |
| `--root-file-id` | Long | 否 | 限定子树 | `0`=空间根 | - |
| `--since` | Long | 否 | 水位时间戳（毫秒） | Unix ms | 可与 `--cursor` 配合 |
| `--cursor` | String | 否 | 分页游标 | 上次 nextCursor | - |
| `--limit` | Integer | 否 | 每页条数 | 正整数 | - |
| `--include-path` | Boolean | 否 | 返回 relativePath | 标志位 | - |
| `--include-move-hint` | Boolean | 否 | 返回移动提示 | 标志位 | - |

### batch-get-meta.py — 批量查元数据

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `--file-ids` | String | 二选一 | 逗号分隔 fileId | 如 `123,456` | 与 `--files-json` 互斥 |
| `--files-json` | JSON String | 二选一 | fileId 列表 JSON | `[123,456]` / `[{"fileId":123}]` / `{"fileIds":[123]}` | 与 `--file-ids` 互斥 |

## 动作列表

### 1. 搜索文件
- **脚本**: `search.py`
- **用途**: 根据关键词搜索文件或目录，返回匹配的文件和文件夹列表
- **注意**: 中文关键词必须 URL 编码（UTF-8）
- **输出**: 返回 `{ folders: [...], files: [...] }`

### 2. 获取文件全文（AI 摘要/RAG 首选）
- **脚本**: `get-full-content.py`
- **用途**: 获取文件的全局提纯文本（Markdown 格式），面向 AI Agent 的智能全文提取
- **适用**: 所有文件类型（doc/file/work_report 等）
- **输出**: 返回 Markdown 格式全文字符串

### 3. 获取下载/预览凭据
- **脚本**: `get-download-info.py`
- **用途**: 获取文件的下载链接或在线预览凭据
- **注意**: 返回的 downloadUrl 为临时签名链接，有时效性
- **输出**: 返回 downloadUrl、openWith（打开方式）、lazyLoad 等

### 4. 下载文件到本地
- **脚本**: `download-file.py`
- **用途**: 获取下载链接后在本地下载原始文件，供 AI 读取 PDF/Word/Excel 等二进制文件
- **输出**: 返回 `{ fileId, fileName, localPath, fileSize }`

### 5. 分页读取文件内容
- **脚本**: `get-file-content.py`
- **用途**: 分页获取文件的排版文本内容，主要用于 UI 界面流式展示
- **注意**: 物理文件（fileType=file）请使用 `get-full-content.py`，本接口对物理文件返回空
- **输出**: 返回该页的排版文本字符串

### 6. 批量获取文件全文
- **脚本**: `batch-get-content.py`
- **用途**: 批量获取多个文件的全文内容，减少往返次数，提升 RAG 效率
- **注意**: 建议单次不超过 10 个文件；默认不截断内容。若结果将直接进入 LLM 上下文，应显式设置 `--max-chars` 和 `--max-chars-per-file`
- **输出**: 返回每个文件的 `{ fileId, content, status, message }`

### 7. 子树扁平列举（冷启动）
- **脚本**: `list-descendant-files.py`
- **用途**: 在映射根下分页拉取后代文件元数据（可选文件夹与 relativePath）
- **输出**: 分页列表 + nextCursor（以接口契约为准）

### 8. 增量变更列表
- **脚本**: `list-changes.py`
- **用途**: 按 since/cursor 拉取变更事件，更新本地水位
- **输出**: items + serverTime / nextCursor（以接口契约为准）

### 9. 批量查元数据（对账）
- **脚本**: `batch-get-meta.py`
- **用途**: 无需拉全文即可核对元数据是否变更
- **输出**: 文件元数据列表（无正文）

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

`openWith` 打开方式枚举：
- `0`: 默认/下载
- `1`: WPS
- `2`: PDF
- `3`: 畅写
- `4`: HTML
- `5`: 工作协同
- `6`: PDF-v5

## 标准流程

2. 调用 `search.py` 搜索文件
3. 根据搜索结果数量处理：
   - 多个结果：返回文件列表，告知用户可以进一步操作
   - 单个结果：直接提供操作选项
4. 用户确定目标文件后，根据需求调用：
   - AI 分析/总结 → `get-full-content.py`
   - 下载/预览 → `get-download-info.py`
   - 分页读取大文件 → `get-file-content.py`
   - 批量读取多文件 → `batch-get-content.py`

## 用户话术示例

- "帮我找一下周报 xxx"
- "搜索一下有没有这份文档"
- "找到这个文件后帮我总结一下"
- "帮我下载这个文件"
- "直接打开让我看看内容"

## 运行方式速查

**调用方式（强制）**：标准 `exec` + python3 -B <skill-dir>/scripts/...；将 `<skill-dir>` 换成本 skill 根目录绝对路径；命令含业务参数 + 可选 `--app-key`。


```bash
python3 -B <skill-dir>/scripts/query/search.py --name-key "关键词" --project-id <project_id> [--root-file-id <root_id>] [--start-time <ts>] [--end-time <ts>] [--exclude-file-types "work_report,huiji"]
python3 -B <skill-dir>/scripts/query/get-full-content.py --file-id <file_id> [--relation-id <relation_id>] [--file-type <file_type>]
python3 -B <skill-dir>/scripts/query/get-download-info.py --file-id <file_id>
python3 -B <skill-dir>/scripts/query/get-download-info.py --file-id <file_id> --force-download
python3 -B <skill-dir>/scripts/query/download-file.py --file-id <file_id> [--output /path/to/save.pdf]
python3 -B <skill-dir>/scripts/query/get-file-content.py --file-id <file_id> [--page-number 1]
python3 -B <skill-dir>/scripts/query/batch-get-content.py --files-json '[{"fileId":123},{"fileId":456}]' [--max-chars 60000] [--max-chars-per-file 20000]
python3 -B <skill-dir>/scripts/query/list-descendant-files.py --root-file-id <root_id> [--project-id <pid>] [--suffix md] [--include-path] [--include-folders]
python3 -B <skill-dir>/scripts/query/list-changes.py [--project-id <pid>] [--root-file-id <root_id>] [--since <ms>] [--cursor <c>] [--include-path] [--include-move-hint]
python3 -B <skill-dir>/scripts/query/batch-get-meta.py --file-ids 123,456
python3 -B <skill-dir>/scripts/query/batch-get-meta.py --files-json '[123,456]'
```
