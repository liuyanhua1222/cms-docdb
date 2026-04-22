# POST /open-api/cwork-file/uploadWholeFile

## 作用

上传本地完整文件（建议 20MB 以下的文件使用），直接返回 resourceId。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: multipart/form-data`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | binary | 是 | 要上传的文件 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["file"],
  "properties": {
    "file": { "type": "string", "format": "binary", "description": "文件二进制流" }
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
    "data": { "type": "integer", "description": "resourceId" }
  }
}
```

## 脚本映射

- `../../scripts/upload/upload-whole-file.py`
