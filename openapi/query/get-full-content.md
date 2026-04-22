# GET /open-api/document-database/file/getFullFileContent

## 作用

获取文件的全局提纯文本（Markdown 格式），面向 AI Agent 的智能全文提取。用于 AI 总结、分析、对话等 RAG 消费场景。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 文件 ID |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["fileId"],
  "properties": {
    "fileId": { "type": "integer", "description": "文件 ID" }
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
    "data": { "type": "string", "description": "全局提纯的 Markdown 格式文本" }
  }
}
```

## 脚本映射

- `../../scripts/query/get-full-content.py`
