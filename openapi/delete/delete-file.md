# POST /open-api/document-database/file/deleteFile

## 作用

删除指定文件。支持逻辑删除（移入回收站）或物理彻底删除。高风险操作，执行前必须获得用户明确确认。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 要删除的文件 ID |
| `isPhysical` | Boolean | 否 | true 物理彻底删除，false/null 移入回收站（默认 false） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["fileId"],
  "properties": {
    "fileId": { "type": "integer", "description": "文件 ID" },
    "isPhysical": { "type": "boolean", "description": "true 彻底删除，false 移入回收站（默认 false）" }
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
    "data": { "type": "boolean", "description": "操作是否成功" }
  }
}
```

## 脚本映射

- `../../scripts/delete/delete-file.py`
