# POST /open-api/document-database/ai/batchGetContent

## 作用

批量获取多个文件的全文本内容，减少交互往返，提升 RAG 数据处理效率。走 Adapter 穿透引擎。建议单次不超过 10 个文件。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `files` | Array | 是 | 文件标识列表，每个元素含 fileId、fileType |

其中 `files` 数组元素：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 文件 ID |
| `relationId` | String | 否 | 业务关联 ID |
| `fileType` | String | 否 | 文件类型（不传则后端自动识别） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["files"],
  "properties": {
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["fileId"],
        "properties": {
          "fileId": { "type": "integer" },
          "relationId": { "type": "string" },
          "fileType": { "type": "string" }
        }
      }
    }
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
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "fileId": { "type": "integer" },
          "content": { "type": "string" },
          "status": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/query/batch-get-content.py`
