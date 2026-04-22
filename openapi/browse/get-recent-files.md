# POST /open-api/document-database/project/personal/getRecentFiles

## 作用

获取当前用户最近上传的文件列表，支持数量限制和关键字搜索。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | Integer | 否 | 限制返回数量 |
| `searchKey` | String | 否 | 搜索关键字 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "limit": { "type": "integer" },
    "searchKey": { "type": "string" }
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
          "id": { "type": "integer" },
          "name": { "type": "string" },
          "type": { "type": "integer" },
          "parentId": { "type": "integer" },
          "resourceId": { "type": "integer" },
          "size": { "type": "integer" },
          "suffix": { "type": "string" }
        }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/browse/get-recent-files.py`
