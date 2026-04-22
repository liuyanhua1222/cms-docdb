# GET /open-api/document-database/file/getFileContent

## 作用

分页获取文件的**排版文本内容**，主要用于 UI 界面进行分段分页的流式展示。适用于大文件内容的分页读取。

> ⚠️ **物理文件（fileType=file）说明**：物理文件的内容请使用 `getFullFileContent` 接口读取。`getFileContent` 对物理文件返回空，这是后端索引引擎差异导致的设计区分。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 文件 ID |
| `pageNumber` | Integer | 否 | 页码，从第一页开始（默认 1） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["fileId"],
  "properties": {
    "fileId": { "type": "integer", "description": "文件 ID" },
    "pageNumber": { "type": "integer", "description": "页码，从 1 开始" }
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
    "data": { "type": "string", "description": "该页的排版文本内容" }
  }
}
```

## 脚本映射

- `../../scripts/query/get-file-content.py`
