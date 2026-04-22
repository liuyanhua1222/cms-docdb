# POST /open-api/document-database/file/uploadFileSliceV2

## 作用

在分片二进制流物理上传到 MinIO 完成后，在服务端注册该分片的元信息，换取 `sliceId`。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `filePath` | String | 是 | 预检接口返回的 `fullPath` |
| `md5` | String | 是 | 分片的 MD5 值（hex） |
| `size` | Long | 是 | 单个分片大小（字节） |
| `storageType` | String | 是 | 存储类型（如 `MINIO`） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["filePath", "md5", "size", "storageType"],
  "properties": {
    "filePath": { "type": "string", "description": "预检接口返回的 fullPath" },
    "md5": { "type": "string", "description": "分片的 MD5（hex）" },
    "size": { "type": "integer", "description": "分片大小（字节）" },
    "storageType": { "type": "string", "description": "存储类型，如 MINIO" }
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
    "data": { "type": "integer", "description": "分片对应的 sliceId" }
  }
}
```

## 脚本映射

- `../../scripts/upload/register-slice.py`
