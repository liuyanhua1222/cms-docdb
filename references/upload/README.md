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

所有动作统一使用 `appKey` 鉴权，运行时从小龙虾上下文变量 `appkey` 获取。

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
| `scripts/upload/create-folder.py` | `POST /open-api/document-database/file/createFolder` | 显式创建空文件夹（`parentId=0` 表示空间根下建一级目录） |

运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 纯文本上传 | content, fileName | fileSuffix, folderName, projectId, updateFileId, versionName, versionRemark |
| 物理文件整传 | 本地文件路径 | — |
| 按父 ID 保存 | parentId, resourceId, name | projectId（parentId≠0 可自动反查）, suffix, size, isSensitive |
| 按路径保存 | projectId, resourceId, name, fileType | path, suffix, size, isSensitive |
| 分片预检 | md5, size, suffix | — |
| 注册分片 | filePath, md5, size, storageType | — |
| 合并分片 | name, sliceIds | suffix, size |
| 创建文件夹 | parentId, name | projectId（parentId≠0 可自动反查）, cover, autoRename |

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
| `parent_id` | Long | 是 | 父目录 ID | 有效文件夹 ID；空间根传 **0** | `parentId≠0` 时脚本自动调 **1.17 getFileBasicInfo** 解析 projectId |
| `--project-id` | Long | 条件 | 空间 ID | 有效 projectId | `parentId=0` 时必填；否则可省略 |
| `--no-resolve-project-id` | Flag | 否 | 跳过自动反查 | - | 不推荐；须同时传 `--project-id` |
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

### create-folder.py — 创建空文件夹

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `parent_id` | Long | 是 | 父目录 ID | 空间根传 **0** | `parentId≠0` 时自动反查 projectId |
| `--project-id` | Long | 条件 | 空间 ID | 有效 projectId | `parentId=0` 时必填 |
| `--no-resolve-project-id` | Flag | 否 | 跳过自动反查 | - | 不推荐 |
| `name` | String | 是 | 文件夹名 | 勿含 `/`、`\` | - |
| `--cover` | Boolean | 否 | 同名覆盖 | 默认 false | 与 auto-rename 互斥策略见 API |
| `--auto-rename` | Boolean | 否 | 同名自动重命名 | 默认 false | - |

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
- **projectId**：`parentId≠0` 时默认自动反查（避免 projectId 与 parentId 不一致导致脏数据）；服务端亦有自动修正兜底
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

### 9. 创建空文件夹
- **脚本**: `create-folder.py`
- **用途**: 同步/归档前预置目录，或在空间根（`parentId=0`）下建一级文件夹
- **输出**: 返回新建文件夹的 `fileId`（Long）

## projectId 自动补全机制（v2.5）

docdb 后端已实现智能 `projectId` 补全，以下脚本受益：

### 1. save-file-by-parent-id.py
- **`parentId > 0` 时**: 脚本默认不传 `projectId`，docdb 自动从 `parentId` 反查
- **`parentId = 0` 时**: 必须传 `--project-id`（空间根直接子节点）
- **反查失败**: docdb 抛异常，脚本返回错误信息

**示例**：
```bash
# 推荐：省略 projectId（parentId > 0 时）
python3 scripts/upload/save-file-by-parent-id.py \
  --parent-id 10086 \
  --resource-id 987654321 \
  --name "技术方案.pdf"

# 必填：parentId=0 时必须传 projectId
python3 scripts/upload/save-file-by-parent-id.py \
  --project-id 2025001 \
  --parent-id 0 \
  --resource-id 987654321 \
  --name "根目录文件.pdf"
```

### 2. create-folder.py
- **规则**: 同 `save-file-by-parent-id.py`
- **`parentId > 0`**: 省略 `--project-id`
- **`parentId = 0`**: 必须传 `--project-id`

**示例**：
```bash
# 推荐：省略 projectId（parentId > 0 时）
python3 scripts/upload/create-folder.py \
  --parent-id 10086 \
  --name "新建文件夹"

# 必填：parentId=0 时必须传 projectId
python3 scripts/upload/create-folder.py \
  --project-id 2025001 \
  --parent-id 0 \
  --name "空间根文件夹"
```

### 3. save-file-by-path.py
- **`path` 不为空时**: docdb 自动从路径反查 `projectId`
- **`path` 为空时**: 需传 `--project-id` 或默认个人知识库
- **个人库**: 不传 `--project-id` 且 `path` 为空时，存入个人知识库根目录

**示例**：
```bash
# 推荐：省略 projectId（path 不为空时）
python3 scripts/upload/save-file-by-path.py \
  --path "工程档案/设计图纸" \
  --resource-id 987654321 \
  --name "方案.pdf"

# 默认个人库：path 为空时
python3 scripts/upload/save-file-by-path.py \
  --resource-id 987654321 \
  --name "笔记.pdf"
```

### 4. upload-content.py
- **projectId 可选**: 不传时保存到个人知识库，传入时保存到指定空间
- **无自动反查**: 此接口为个人库捷径，不涉及 parentId 反查逻辑

**调用建议**: 优先省略 `projectId` 参数，减少参数传递错误风险。仅在以下场景显式传入：
1. `parentId = 0` 且需要在空间根下创建（save-file-by-parent-id / create-folder）
2. 明确指定目标空间（save-file-by-path 且 path 为空）

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

## 标准流程

### 纯文本上传（推荐用于 AI 生成内容）

1. 鉴权预检（从小龙虾运行时上下文获取 `appkey`）
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
4. 绑定到知识库：
   - 已知 **parentId**：`save-file-by-parent-id.py <parent_id> <resource_id> "文件名.pdf"`（自动反查 projectId）
   - 已知 **路径**：`save-file-by-path.py`（须传 projectId）
5. 返回 fileId

## 用户话术示例

- "帮我把这段总结存到知识库"
- "上传这份 PDF 到 AI 生成文件夹"
- "把这份 Markdown 文档归档"
- "帮我保存这个文件"

## 运行方式速查

```bash
python3 scripts/upload/upload-content.py "内容" "文件名.md" [--file-suffix md] [--folder-name "AI生成/周报"] [--project-id <project_id>]
python3 scripts/upload/upload-content.py "新内容" "文件名.md" --update-file-id <file_id> [--version-name "V2.0"] [--version-remark "修订说明"]
python3 scripts/upload/upload-whole-file.py <file_path>
python3 scripts/upload/check-slice.py <md5> [--size <size>] [--suffix <suffix>]
python3 scripts/upload/register-slice.py <full_path> <md5> <size> MINIO
python3 scripts/upload/merge-resource.py "文件名.pdf" "sliceId1,sliceId2,..." [--suffix pdf] [--size <size>]
python3 scripts/upload/save-file-by-parent-id.py <parent_id> <resource_id> "文件名.pdf" [--project-id <id>] [--suffix pdf]
python3 scripts/upload/save-file-by-path.py <project_id> "文件名.pdf" <resource_id> [--path "目录"] [--suffix pdf]
python3 scripts/upload/get-file-download-info.py <resource_id>
python3 scripts/upload/create-folder.py <parent_id> "文件夹名" [--project-id <id>] [--cover] [--auto-rename]
```
