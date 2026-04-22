# POST /open-api/document-database/file/saveFileByParentId

## 作用

已知目标文件夹 ID 时，通过 `parentId` 直接将物理文件保存到项目知识库的指定目录。比 `saveFileByPath` 少一次路径解析。**纯文本内容请使用 `uploadContent` 接口。**

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `projectId` | Long | 是 | 目标项目空间 ID |
| `parentId` | Long | 是 | 目标文件夹 ID（根目录传 0） |
| `name` | String | 是 | 保存的文件名 |
| `fileType` | String | 是 | 文件类型：仅支持 `file`（物理文件） |
| `resourceId` | Long | 是 | 资源 ID，需先通过 `upload-whole-file` 或分片上传获得 |
| `suffix` | String | 否 | 文件后缀，建议传入 |
| `size` | Long | 否 | 文件大小（字节），建议传入 |
| `isSensitive` | Integer | 否 | 是否跨境敏感文件（0 非敏感，默认；1 敏感） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["projectId", "parentId", "name", "fileType", "resourceId"],
  "properties": {
    "projectId": { "type": "integer" },
    "parentId": { "type": "integer" },
    "name": { "type": "string" },
    "fileType": { "type": "string", "enum": ["file"] },
    "resourceId": { "type": "integer" },
    "suffix": { "type": "string" },
    "size": { "type": "integer" },
    "isSensitive": { "type": "integer" }
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
    "data": { "type": "integer", "description": "新建/更新的文件 ID" }
  }
}
```

## 脚本映射

- `../../scripts/upload/save-file-by-parent-id.py`
