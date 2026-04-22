# GET /open-api/document-database/project/personal/getProjectId

## 作用

获取当前用户的个人知识库空间 ID。用于快速获取个人专属空间标识。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `appCode` | String | 否 | 应用编码 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "appCode": { "type": "string" }
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
    "data": { "type": "integer", "description": "个人知识库空间 ID" }
  }
}
```

## 脚本映射

- `../../scripts/browse/get-personal-project-id.py`
