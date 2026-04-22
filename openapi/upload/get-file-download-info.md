# GET /open-api/cwork-file/getDownloadInfo

## 作用

根据 resourceId 获取文件的下载信息，包括临时下载 URL（有效期 1 小时）。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `resourceId` | Long | 是 | 文件资源 ID |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["resourceId"],
  "properties": {
    "resourceId": { "type": "integer", "description": "文件资源 ID" }
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
        "downloadUrl": { "type": "string", "description": "下载 URL（有效期 1 小时）" },
        "fileName": { "type": "string" },
        "resourceId": { "type": "integer" },
        "suffix": { "type": "string" },
        "size": { "type": "integer" }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/upload/get-file-download-info.py`
