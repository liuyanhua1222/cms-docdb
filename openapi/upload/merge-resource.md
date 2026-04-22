# POST /open-api/document-database/file/saveResource

## 作用

在所有分片注册完成后，触发服务端合并分片，生成最终的 `resourceId`。获取 `resourceId` 后可继续调用知识库的 `saveFileByPath` 将文件绑定入库。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | String | 是 | 文件名称（含后缀） |
| `sliceIds` | Array[Long] | 是 | 所有分片对应的 `sliceId` 列表 |
| `suffix` | String | 否 | 文件后缀（如 `pdf`） |
| `size` | Long | 否 | 文件总大小（字节） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "sliceIds"],
  "properties": {
    "name": { "type": "string", "description": "文件名称（含后缀）" },
    "sliceIds": { "type": "array", "items": { "type": "integer" }, "description": "所有分片的 sliceId 列表" },
    "suffix": { "type": "string" },
    "size": { "type": "integer" }
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
    "data": { "type": "integer", "description": "最终的 resourceId" }
  }
}
```

## 脚本映射

- `../../scripts/upload/merge-resource.py`
