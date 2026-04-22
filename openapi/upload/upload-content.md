# POST /open-api/document-database/file/uploadContent

## 作用

一键快速保存纯文本内容（如 Markdown、HTML、纯文本）到个人知识库。AI 内容入库首选方案，无需关心具体空间 ID，系统自动关联当前用户。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `content` | String | 是 | 文本/Markdown/HTML 源码内容 |
| `fileName` | String | 是 | 保存的文件名（建议带扩展名，如 `xxx.md`） |
| `fileSuffix` | String | 否 | 文件后缀（如 `md`、`json`、`html`、`txt`），不传则从文件名自动识别 |
| `folderName` | String | 否 | 逻辑目录路径（如 `AI生成/周报`），不传则默认归档至"和AI的对话" |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["content", "fileName"],
  "properties": {
    "content": { "type": "string", "description": "文本/Markdown/HTML 内容" },
    "fileName": { "type": "string", "description": "文件名，建议带扩展名" },
    "fileSuffix": { "type": "string", "description": "文件后缀" },
    "folderName": { "type": "string", "description": "逻辑目录路径，支持多级" }
  }
}
```

## 响应 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "resultCode": { "type": "number" },
    "resultMsg": { "type": ["string", "null"] },
    "data": {
      "type": "object",
      "properties": {
        "projectId": { "type": "integer" },
        "projectName": { "type": "string" },
        "folderId": { "type": "integer" },
        "folderName": { "type": "string" },
        "fileId": { "type": "integer" },
        "fileName": { "type": "string" },
        "downloadUrl": { "type": "string" }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/upload/upload-content.py`
