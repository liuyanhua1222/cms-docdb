# upload — 模块说明

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

- 用户说"帮我把这个文档存到知识库"、"上传 xxx 到知识库"、"把这份报告归档"
- 用户想让 AI 分析完某个内容后自动保存结果
- **仅用于新建文件**：若目标文件已存在，必须路由到 `manage` 模块走版本更新，禁止在此模块覆盖

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/upload/upload-content.py` | `POST /open-api/document-database/file/uploadContent` | 一键保存纯文本到个人知识库或指定项目空间 |
| `scripts/upload/save-file-by-path.py` | `POST /open-api/document-database/file/saveFileByPath` | 按逻辑路径保存物理文件到项目空间 |
| `scripts/upload/save-file-by-parent-id.py` | `POST /open-api/document-database/file/saveFileByParentId` | 已知父目录 ID 时保存物理文件 |
| `scripts/upload/upload-whole-file.py` | `POST /open-api/cwork-file/uploadWholeFile` | 小文件整传（建议 20MB 以下），返回 resourceId |
| `scripts/upload/check-slice.py` | `GET /open-api/document-database/file/getSliceIdByMd5V2` | 大文件分片预检，支持秒传判定 |
| `scripts/upload/register-slice.py` | `POST /open-api/document-database/file/uploadFileSliceV2` | 注册分片元信息，换取 sliceId |
| `scripts/upload/merge-resource.py` | `POST /open-api/document-database/file/saveResource` | 合并分片生成最终 resourceId |
| `scripts/upload/get-file-download-info.py` | `GET /open-api/cwork-file/getDownloadInfo` | 根据 resourceId 获取下载 URL（有效期 1 小时） |

运行前先按 `cms-auth-skills/SKILL.md` 设置 `XG_BIZ_API_KEY` 或 `XG_APP_KEY`。系统会自动检测 Python 命令，优先使用 `python3`，如不存在则使用 `python`。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 纯文本上传 | content, fileName | fileSuffix, folderName, projectId, updateFileId, versionName, versionRemark |
| 物理文件整传 | 本地文件路径 | — |
| 按父 ID 保存 | projectId, parentId, resourceId, name, fileType | suffix, size, isSensitive |
| 按路径保存 | projectId, resourceId, name, fileType | path, suffix, size, isSensitive |
| 分片预检 | md5, size, suffix | — |
| 注册分片 | filePath, md5, size, storageType | — |
| 合并分片 | name, sliceIds | suffix, size |

## 参数详细说明

### upload-content.py — 纯文本上传

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `content` | String | 是 | 文件内容 | 任意文本内容（Markdown/HTML/纯文本） | - |
| `file_name` | String | 是 | 文件名 | 建议带扩展名，如 `总结.md`、`报告.html` | - |
| `--file-suffix` | String | 否 | 文件后缀 | 枚举：`md`（默认）、`html`、`txt`、`json` | - |
| `--folder-name` | String | 否 | 逻辑目录路径 | 支持多级，如 `AI生成/周报`，仅新建模式有效 | 不能与 --update-file-id 同时使用 |
| `--project-id` | Long | 否 | 目标项目空间 ID | 有效项目 ID（可通过 get-project-list.py 获取） | 不传则保存到个人知识库 |
| `--update-file-id` | Long | 否 | 版本更新模式的目标文件 ID | 有效文件 ID | 传入后切换为版本更新模式，不能与 --folder-name 同时使用 |
| `--version-name` | String | 否 | 版本名称 | 如 `V2.0` | 仅版本更新模式有效（需传 --update-file-id） |
| `--version-remark` | String | 否 | 版本说明 | 任意文本 | 仅版本更新模式有效（需传 --update-file-id） |

### upload-whole-file.py — 物理文件整传

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_path` | String | 是 | 本地文件路径 | 有效文件路径，建议≤20MB | - |

文件体采用 5MB 分块发送，避免一次性读入内存。大文件优先建议使用分片流程，但脚本不做 20MB 硬限制。

### save-file-by-parent-id.py — 按父 ID 保存

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `project_id` | Long | 是 | 项目/空间 ID | 有效项目 ID | - |
| `parent_id` | Long | 是 | 父目录 ID | 有效文件夹 ID（根目录传项目根目录 ID） | 需在 project_id 对应的项目内 |
| `resource_id` | Long | 是 | 物理资源 ID | 通过 upload-whole-file.py 或 merge-resource.py 获取 | - |
| `name` | String | 是 | 文件名 | 建议带扩展名，如 `报告.pdf` | - |
| `--file-type` | String | 否 | 文件业务类型 | 枚举：`file`（默认，物理文件）、`doc`（文档） | - |
| `--suffix` | String | 否 | 文件后缀 | 如 `pdf`、`docx`、`xlsx` | - |
| `--size` | Long | 否 | 文件大小（字节） | 文件实际大小 | - |
| `--is-sensitive` | Boolean | 否 | 是否敏感文件 | true/false | - |

### save-file-by-path.py — 按路径保存

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `project_id` | Long | 是 | 项目/空间 ID | 有效项目 ID | - |
| `name` | String | 是 | 文件名 | 建议带扩展名 | - |
| `resource_id` | Long | 是 | 物理资源 ID | 通过 upload-whole-file.py 或 merge-resource.py 获取 | - |
| `--path` | String | 否 | 逻辑目录路径 | 如 `AI生成/周报`，不存在自动创建 | - |
| `--file-type` | String | 否 | 文件业务类型 | 枚举：`file`（默认）、`doc` | - |
| `--suffix` | String | 否 | 文件后缀 | 如 `pdf`、`docx` | - |
| `--size` | Long | 否 | 文件大小（字节） | 文件实际大小 | - |
| `--is-sensitive` | Boolean | 否 | 是否敏感文件 | true/false | - |

### check-slice.py — 大文件分片预检

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `md5` | String | 是 | 文件 MD5 值 | 32位十六进制字符串 | - |
| `--size` | Long | 否 | 文件大小（字节） | 文件实际大小 | - |
| `--suffix` | String | 否 | 文件后缀 | 如 `pdf`、`mp4` | - |

### register-slice.py — 注册分片

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `full_path` | String | 是 | 分片临时文件路径 | 有效文件路径 | - |
| `md5` | String | 是 | 分片 MD5 值 | 32位十六进制字符串 | - |
| `size` | Long | 是 | 分片大小（字节） | 分片实际大小 | - |
| `storage_type` | String | 是 | 存储类型 | 枚举：`MINIO`（固定值） | - |

### merge-resource.py — 合并分片

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `name` | String | 是 | 文件名 | 建议带扩展名 | - |
| `slice_ids` | String | 是 | 分片 ID 列表 | 通过 register-slice.py 获取，多个用逗号分隔，如 `sliceId1,sliceId2` | - |
| `--suffix` | String | 否 | 文件后缀 | 如 `pdf` | - |
| `--size` | Long | 否 | 文件总大小（字节） | 所有分片大小之和 | - |

### get-file-download-info.py — 获取资源下载链接

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `resource_id` | Long | 是 | 物理资源 ID | 通过 upload-whole-file.py 或 merge-resource.py 获取 | - |

## 动作列表

### 1. 纯文本上传（AI 内容入库首选）
- **脚本**: `upload-content.py`
- **用途**: 一键保存纯文本/Markdown/HTML 内容到个人知识库或指定知识库项目空间
- **注意**: 仅支持纯文本，不支持二进制文件；不传 fileSuffix 时默认为 md
- **空间路由**: 不传 projectId 时保存到个人知识库，传入 projectId 时保存到指定知识库项目空间（需确保用户有访问权限）
- **新建模式响应**: 返回 `{ projectId, projectName, folderId, folderName, fileId, fileName, downloadUrl }`
- **版本更新模式响应**: 传入 `--update-file-id` 时，仅返回 `{ fileId, fileName }`

### 2. 物理文件整传
- **脚本**: `upload-whole-file.py`
- **用途**: 小文件（建议 20MB 以下）整体上传，返回 resourceId；脚本会分块发送文件体以降低内存峰值
- **输出**: 返回 resourceId（用于后续绑定到知识库）

### 3. 按父 ID 保存到项目目录
- **脚本**: `save-file-by-parent-id.py`
- **用途**: 已知目标文件夹 ID 时，将物理文件资源绑定到项目知识库
- **输出**: 返回新建文件的 fileId

### 4. 按路径保存到项目目录
- **脚本**: `save-file-by-path.py`
- **用途**: 通过逻辑路径保存物理文件，路径不存在时自动递归创建目录
- **输出**: 返回新建文件的 fileId

### 5. 大文件分片预检
- **脚本**: `check-slice.py`
- **用途**: 大文件（>20MB）上传前预检，支持秒传判定
- **输出**: 返回 sliceId（秒传命中）或 uploadUrl + fullPath（需上传）

### 6. 注册分片
- **脚本**: `register-slice.py`
- **用途**: 注册分片元信息，换取 sliceId
- **输出**: 返回 sliceId

### 7. 合并分片
- **脚本**: `merge-resource.py`
- **用途**: 合并所有分片生成最终 resourceId
- **输出**: 返回 resourceId

### 8. 获取资源下载链接
- **脚本**: `get-file-download-info.py`
- **用途**: 根据 resourceId 获取下载 URL（有效期 1 小时）
- **输出**: 返回 downloadUrl

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

## 标准流程

### 纯文本上传（推荐用于 AI 生成内容）

1. 鉴权预检（通过 `cms-auth-skills` 获取 appKey）
2. 确认文件名（建议带扩展名）和内容
3. 调用 `upload-content.py`
   - 不传 `--project-id`：自动归档至个人空间"和AI的对话"目录（或指定目录）
   - 传入 `--project-id`：保存到指定项目空间（需确保用户有访问权限）
4. 返回 fileId

## 用户感知与对话输出规范（建议）

> 目标：让用户明确知道“保存成功了吗、保存到了哪里、后续还能不能继续改”。

### A. 保存成功结果卡片（推荐）

当用户说“帮我保存到知识库/归档到知识库”并保存成功后，建议输出如下“结果卡片”文本：

```text
已保存到知识库 ✅

文件：{fileName}
空间：{projectName}
位置：{projectName} / {ancestorNames 或 folderName}
版本：{versionName 或 V1 · {time}}

你继续让我修改这份文档时，我会更新到同一个知识库文件（通过版本管理生成新版本）。

下一步：
- 查看文件：可让我生成预览短链或下载链接
- 打开知识库位置：可让我浏览该目录下的其他文件
- 分享：可让我把该文件授权分享给指定同事（默认带分享+预览+查看，并发送钉钉通知）
```

字段说明：
- `projectName`/`folderName`：来自保存接口返回数据（若为空，表示保存到了个人空间或默认目录）
- `ancestorNames`：如 browse 接口返回了完整路径（`ancestorNames`），优先使用它构造“位置”

### B. 默认空间提示（可选）

若本次保存是系统默认选择空间/目录（用户未指定 projectId 或 folderName），建议补充一句：

```text
已按默认设置保存到「{projectName 或 个人知识库}」。
```

### 物理文件上传（PDF/DOCX 等）

1. 鉴权预检
2. 小文件整传（建议 20MB 以下）：调用 `upload-whole-file.py` → 获得 resourceId
3. 大文件或整传失败：`check-slice.py` → `register-slice.py` → `merge-resource.py` → 获得 resourceId
4. 调用 `save-file-by-path.py` 或 `save-file-by-parent-id.py` 绑定到知识库
5. 返回 fileId

## 用户话术示例

- "帮我把这段总结存到知识库"
- "上传这份 PDF 到 AI 生成文件夹"
- "把这份 Markdown 文档归档"
- "帮我保存这个文件"

## 运行方式速查

```bash
python scripts/upload/upload-content.py "内容" "文件名.md" [--file-suffix md] [--folder-name "AI生成/周报"] [--project-id <project_id>]
python scripts/upload/upload-content.py "新内容" "文件名.md" --update-file-id <file_id> [--version-name "V2.0"] [--version-remark "修订说明"]
python scripts/upload/upload-whole-file.py <file_path>
python scripts/upload/check-slice.py <md5> [--size <size>] [--suffix <suffix>]
python scripts/upload/register-slice.py <full_path> <md5> <size> MINIO
python scripts/upload/merge-resource.py "文件名.pdf" "sliceId1,sliceId2,..." [--suffix pdf] [--size <size>]
python scripts/upload/save-file-by-parent-id.py <project_id> <parent_id> <resource_id> "文件名.pdf" [--suffix pdf]
python scripts/upload/save-file-by-path.py <project_id> "文件名.pdf" <resource_id> [--path "目录"] [--suffix pdf]
python scripts/upload/get-file-download-info.py <resource_id>
```
