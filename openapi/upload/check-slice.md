# GET /open-api/document-database/file/getSliceIdByMd5V2

## 作用

大文件分片上传前的 MD5 预检接口，用于：
1. **秒传判定**：若文件/分片已存在于服务端，直接返回 `sliceId`，跳过物理上传
2. **获取上传目标**：若未命中，返回 `uploadUrl`（MinIO 预签名 PUT 地址）和 `fullPath`

**鉴权类型**
- `appKey`

**Headers**
- `appKey`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `md5` | String | 是 | 文件/分片的 MD5（hex 字符串） |
| `size` | Long | 否 | 文件总大小（字节） |
| `suffix` | String | 否 | 文件后缀（如 `pdf`） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["md5"],
  "properties": {
    "md5": { "type": "string", "description": "文件/分片的 MD5（hex）" },
    "size": { "type": "integer" },
    "suffix": { "type": "string" }
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
        "sliceId": { "type": "integer", "description": "分片 ID（命中秒传时有值）" },
        "uploadUrl": { "type": "string", "description": "MinIO 预签名上传地址（未命中时返回）" },
        "fullPath": { "type": "string", "description": "服务端目标存储路径（供 register-slice 使用）" },
        "storageType": { "type": "string", "description": "存储类型（如 MINIO）" }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/upload/check-slice.py`
