# GET /open-api/document-database/project/uploadableList

## 作用

获取当前账号有上传/编辑权限的空间列表。Agent 在执行保存、归档前应调用此接口确定目标空间。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `appCode` | String | 否 | 应用编码（默认 `kz_doc`） |
| `nameKey` | String | 否 | 空间名称模糊搜索关键词（中文需 URL 编码） |
| `bizCode` | String | 否 | 业务线编码过滤 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "appCode": { "type": "string" },
    "nameKey": { "type": "string", "description": "中文需 URL 编码" },
    "bizCode": { "type": "string" }
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
          "remark": { "type": "string" },
          "type": { "type": "string" },
          "role": { "type": "integer" },
          "canCreateAtRoot": { "type": "boolean" },
          "rawEnabled": { "type": "boolean" }
        }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/browse/get-uploadable-list.py`
