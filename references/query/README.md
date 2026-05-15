# query — 模块说明

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

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/query/search.py` | `GET /open-api/document-database/file/searchFile` | 搜索文件或目录 |
| `scripts/query/get-full-content.py` | `GET /open-api/document-database/file/getFullFileContent` | 获取文件全局提纯文本（Markdown），RAG 入口 |
| `scripts/query/get-download-info.py` | `GET /open-api/document-database/file/getDownloadInfo` | 获取文件下载/预览凭据 |
| `scripts/query/download-file.py` | `GET /open-api/document-database/file/getDownloadInfo` + 本地下载 | 下载文件到本地，解决内网 URL 无法被 AI 工具访问的问题 |
| `scripts/query/get-file-content.py` | `GET /open-api/document-database/file/getFileContent` | 分页获取文件文本内容 |
| `scripts/query/batch-get-content.py` | `POST /open-api/document-database/ai/batchGetContent` | 批量获取多个文件全文，建议≤10个 |

运行前先按 `cms-auth-skills/SKILL.md` 设置 `XG_BIZ_API_KEY` 或 `XG_APP_KEY`。系统会自动检测 Python 命令，优先使用 `python3`，如不存在则使用 `python`。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 搜索文件 | nameKey（关键词）, projectId | rootFileId, startTime, endTime, excludeFileTypes, excludeFolderNames |
| 获取文件全文 | fileId | relationId, fileType |
| 获取下载/预览凭据 | fileId | forceDownload, versionNumber |
| 下载文件到本地 | fileId | output |
| 分页读取文件内容 | fileId | pageNumber |
| 批量获取文件全文 | files（fileId 列表） | — |

## 参数详细说明

### search.py — 搜索文件

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `name_key` | String | 是 | 搜索关键词，支持模糊匹配 | 任意字符串，中文需 URL 编码（UTF-8） | - |
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
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID（可通过 search.py 获取） | - |
| `--relation-id` | String | 否 | 业务关联 ID | 业务系统中的关联标识 | - |
| `--file-type` | String | 否 | 业务类型 | 枚举：`doc`（文档）、`file`（物理文件）、`work_report`（工作汇报）等 | - |

### get-download-info.py — 获取下载/预览凭据

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--force-download` | Boolean | 否 | 强制获取下载链接（而非预览链接） | 无值标志，存在即为 true | - |
| `--version-number` | Integer | 否 | 指定版本号 | 有效版本号（可通过 get-version-list.py 获取） | - |

### download-file.py — 下载文件到本地

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--output` | String | 否 | 本地保存路径 | 有效本地路径；不传则保存到系统临时目录 | - |

### get-file-content.py — 分页读取文件内容

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID（文档类型，非物理文件） | - |
| `--page-number` | Integer | 否 | 页码 | ≥1（默认 1） | - |

### batch-get-content.py — 批量获取文件全文

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `files` | JSON String | 是 | 文件 ID 列表 | JSON 数组格式，如 `'[{"fileId":123},{"fileId":456}]'`，建议单次≤10个 | - |

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
- **注意**: 建议单次不超过 10 个文件
- **输出**: 返回每个文件的 `{ fileId, content, status, message }`

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

1. 鉴权预检（通过 `cms-auth-skills` 获取 appKey）
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

```bash
python scripts/query/search.py "关键词" --project-id <project_id> [--root-file-id <root_id>] [--start-time <ts>] [--end-time <ts>] [--exclude-file-types "work_report,huiji"]
python scripts/query/get-full-content.py <file_id> [--relation-id <relation_id>] [--file-type <file_type>]
python scripts/query/get-download-info.py <file_id>
python scripts/query/get-download-info.py <file_id> --force-download
python scripts/query/download-file.py <file_id> [--output /path/to/save.pdf]
python scripts/query/get-file-content.py <file_id> [--page-number 1]
python scripts/query/batch-get-content.py '[{"fileId":123},{"fileId":456}]'
```
