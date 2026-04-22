# 脚本清单 — query

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `search.py` | `GET /open-api/document-database/file/searchFile` | 搜索文件或目录 |
| `get-full-content.py` | `GET /open-api/document-database/file/getFullFileContent` | 获取文件全局提纯文本（Markdown），RAG 入口 |
| `get-download-info.py` | `GET /open-api/document-database/file/getDownloadInfo` | 获取文件下载/预览凭据 |
| `get-file-content.py` | `GET /open-api/document-database/file/getFileContent` | 分页获取文件文本内容 |
| `batch-get-content.py` | `POST /open-api/document-database/ai/batchGetContent` | 批量获取多个文件全文，建议≤10个 |

## 使用方式

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# 搜索文件
python3 scripts/query/search.py "关键词" [--project-id 123]

# 获取文件全文（AI 摘要/RAG）
python3 scripts/query/get-full-content.py <file_id>

# 获取下载/预览凭据
python3 scripts/query/get-download-info.py <file_id> [--force-download]

# 分页获取文件内容
python3 scripts/query/get-file-content.py <file_id> [--page-number 1]

# 批量获取文件全文（RAG 场景）
python3 scripts/query/batch-get-content.py '[{"fileId":123},{"fileId":456}]'
```

## 输出说明

所有脚本的输出均为 **JSON 格式**。

## 规范

1. **必须使用 Python** 编写
2. **鉴权遵循** `cms-auth-skills/SKILL.md` 规范
3. **入参定义以** `openapi/` 文档为准
