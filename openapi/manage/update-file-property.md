# POST /open-api/document-database/file/updateFileProperty

## 作用

更新文件属性，支持重命名和跨目录移动。同名冲突时有三种处理策略：静默覆盖、自动追加后缀、或报错。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 文件 ID |
| `newName` | String | 否 | 新文件名（仅重命名时传入） |
| `targetParentId` | Long | 否 | 目标父目录 ID（仅移动时传入） |
| `cover` | Boolean | 否 | 同名冲突时是否覆盖（与 autoRename 互斥，cover 优先级更高） |
| `autoRename` | Boolean | 否 | 同名冲突时是否自动追加数字后缀（如 文件名(1).pdf） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["fileId"],
  "properties": {
    "fileId": { "type": "integer", "description": "文件 ID" },
    "newName": { "type": "string", "description": "新文件名" },
    "targetParentId": { "type": "integer", "description": "目标父目录 ID" },
    "cover": { "type": "boolean", "description": "同名覆盖" },
    "autoRename": { "type": "boolean", "description": "同名自动重命名" }
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
    "data": { "type": "boolean" }
  }
}
```

## 脚本映射

- `../../scripts/manage/update-file-property.py`
