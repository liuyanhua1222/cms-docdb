# 脚本清单 — query

## 鉴权前置条件

- **鉴权模式**：`appKey`
- **环境变量**：`XG_BIZ_API_KEY` 或 `XG_APP_KEY`
- **获取方式**：通过 `cms-auth-skills` 获取并设置环境变量

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `search.py` | `GET /open-api/document-database/file/searchFile` | 搜索文件或目录 |
| `get-full-content.py` | `GET /open-api/document-database/file/getFullFileContent` | 获取文件全局提纯文本（Markdown），RAG 入口 |
| `get-download-info.py` | `GET /open-api/document-database/file/getDownloadInfo` | 获取文件下载/预览凭据 |
| `download-file.py` | `GET /open-api/document-database/file/getDownloadInfo` + 本地下载 | **下载文件到本地**（解决内网 URL 无法被 AI 工具访问的问题） |
| `get-file-content.py` | `GET /open-api/document-database/file/getFileContent` | 分页获取文件文本内容 |
| `batch-get-content.py` | `POST /open-api/document-database/ai/batchGetContent` | 批量获取多个文件全文，建议≤10个 |

## 运行方式

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# 搜索文件
python3 scripts/query/search.py "关键词" [--project-id 123]

# 获取文件全文（AI 摘要/RAG）
python3 scripts/query/get-full-content.py <file_id>

# 获取预览链接（用户自己查看）
python3 scripts/query/get-download-info.py <file_id>

# 获取下载链接
python3 scripts/query/get-download-info.py <file_id> --force-download

# 下载文件到本地（推荐用于 AI 分析场景）
python3 scripts/query/download-file.py <file_id> [--output /path/to/save.pdf]

# 分页获取文件内容
python3 scripts/query/get-file-content.py <file_id> [--page-number 1]

# 批量获取文件全文（RAG 场景）
python3 scripts/query/batch-get-content.py '[{"fileId":123},{"fileId":456}]'
```

## 返回说明

所有脚本的输出均为 **JSON 格式**，包含以下字段：

- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据（具体结构见各脚本文档）

## 特别说明：预览与下载

### 用户自己查看文件（预览链接）

**使用场景**：用户说"帮我打开这个文件"、"我想看看这个文档"

**脚本**：`get-download-info.py <file_id>`（不带 `--force-download` 参数）

**OpenClaw 处理方式**：
1. 执行脚本获取预览链接
2. 从返回的 `data.downloadUrl` 提取预览 URL
3. 将链接展示给用户（遵循"对外克制"原则：输出链接，不暴露内部字段）
4. 用户点击链接在浏览器中查看

**返回示例**：
```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": {
    "downloadUrl": "https://...",
    "fileName": "文件名.pdf",
    "openWith": 2,  // 2=PDF预览
    "lazyLoad": false
  }
}
```

### OpenClaw 分析文件内容（本地下载）

**使用场景**：用户说"帮我总结这个文件"、"分析一下这个文档"

由于 MinIO 服务器部署在内网，OpenClaw 的 `web_fetch` 和 `pdf` 工具会因为安全限制无法访问（错误：`Blocked: resolves to private/internal/special-use IP address`）。

**解决方案**：使用 `download-file.py` 在本地下载文件，绕过云端工具的限制。

**工作原理**：
1. 调用 `getDownloadInfo` API 获取 MinIO 预签名 URL
2. 使用 Python urllib 在本地下载文件
3. 保存到本地文件系统（临时目录或指定路径）
4. 返回本地文件路径供 OpenClaw 读取分析

**返回示例**：
```json
{
  "resultCode": 1,
  "resultMsg": null,
  "data": {
    "fileId": 1995404125101232130,
    "fileName": "文件名.pdf",
    "localPath": "/tmp/文件名.pdf",
    "fileSize": 1234567
  }
}
```

### 与其他脚本的选择

- **用户要自己查看文件**（在浏览器中预览）→ 使用 `get-download-info.py`（不带 `--force-download`），OpenClaw 将预览链接展示给用户
- **用户要下载文件**（保存到本地）→ 使用 `get-download-info.py --force-download` 获取下载链接，或使用 `download-file.py` 直接下载
- **OpenClaw 需要分析文件内容**（AI 分析、RAG）→ 优先使用 `get-full-content.py`（获取提纯文本，更高效）
- **OpenClaw 需要原始文件**（PDF、Word 等二进制文件）→ 使用 `download-file.py` 下载到本地后分析

## 规范

1. **必须使用 Python** 编写
2. **鉴权遵循** `cms-auth-skills/SKILL.md` 规范
3. **入参定义以** `openapi/` 文档为准
