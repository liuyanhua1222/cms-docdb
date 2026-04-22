# upload — 模块说明

## 适用场景

- 用户说"帮我把这个文档存到知识库"、"上传 xxx 到知识库"、"把这份报告归档"
- 用户想让 AI 分析完某个内容后自动保存结果
- **仅用于新建文件**：若目标文件已存在，必须路由到 `manage` 模块走版本更新，禁止在此模块覆盖

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 纯文本上传 | content, fileName | fileSuffix, folderName |
| 物理文件整传 | 本地文件路径 | — |
| 按父 ID 保存 | projectId, parentId, resourceId, name, fileType | suffix, size, isSensitive |
| 按路径保存 | projectId, resourceId, name, fileType | path, suffix, size, isSensitive |
| 分片预检 | md5, size, suffix | — |
| 注册分片 | filePath, md5, size, storageType | — |
| 合并分片 | name, sliceIds | suffix, size |

## 动作列表

### 1. 纯文本上传（AI 内容入库首选）
- **脚本**: `upload-content.py`
- **用途**: 一键保存纯文本/Markdown/HTML 内容到个人知识库，无需关心 projectId
- **注意**: 仅支持纯文本，不支持二进制文件；不传 fileSuffix 时默认为 md
- **新建模式响应**: 返回 `{ projectId, projectName, folderId, folderName, fileId, fileName, downloadUrl }`
- **版本更新模式响应**: 传入 `--update-file-id` 时，仅返回 `{ fileId, fileName }`

### 2. 物理文件整传
- **脚本**: `upload-whole-file.py`
- **用途**: 小文件（≤20MB）整体上传，返回 resourceId
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
4. 自动归档至个人空间"和AI的对话"目录（或指定目录）
5. 返回 fileId

### 物理文件上传（PDF/DOCX 等）

1. 鉴权预检
2. 小文件（≤20MB）：调用 `upload-whole-file.py` → 获得 resourceId
3. 大文件（>20MB）：`check-slice.py` → `register-slice.py` → `merge-resource.py` → 获得 resourceId
4. 调用 `save-file-by-path.py` 或 `save-file-by-parent-id.py` 绑定到知识库
5. 返回 fileId

## 用户话术示例

- "帮我把这段总结存到知识库"
- "上传这份 PDF 到 AI 生成文件夹"
- "把这份 Markdown 文档归档"
- "帮我保存这个文件"
