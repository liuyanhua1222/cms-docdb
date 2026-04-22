# POST /open-api/document-database/file/saveFileByPath

## 作用

将物理文件保存到指定项目空间的指定逻辑目录路径下。路径不存在时系统自动递归创建文件夹。**纯文本内容（如 AI 生成的 Markdown）请使用 `uploadContent` 接口。**

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `projectId` | Long | 是 | 目标项目空间 ID |
| `name` | String | 是 | 保存的文件名 |
| `fileType` | String | 是 | 文件类型：仅支持 `file`（物理文件） |
| `path` | String | 否 | 逻辑目录路径（如 `AI生成/周报`），不传则存入根目录；路径不存在自动创建 |
| `resourceId` | Long | 是 | 资源 ID，需先通过 `upload-whole-file` 或分片上传获得 |
| `suffix` | String | 否 | 文件后缀（如 `pdf`、`md`），建议传入 |
| `size` | Long | 否 | 文件大小（字节），建议传入 |
| `isSensitive` | Integer | 否 | 是否跨境敏感文件（0 非敏感，默认；1 敏感） |

> **注意**：`fileContent` 字段已废弃，请勿传入。纯文本内容统一使用 `uploadContent` 接口。

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["projectId", "name", "fileType", "resourceId"],
  "properties": {
    "projectId": { "type": "integer", "description": "目标项目空间 ID" },
    "name": { "type": "string", "description": "保存的文件名" },
    "fileType": { "type": "string", "enum": ["file"], "description": "仅支持 file（物理文件）" },
    "path": { "type": "string", "description": "逻辑目录路径，不传则存根目录" },
    "resourceId": { "type": "integer", "description": "资源 ID（必须）" },
    "suffix": { "type": "string", "description": "文件后缀" },
    "size": { "type": "integer", "description": "文件大小（字节）" },
    "isSensitive": { "type": "integer", "description": "是否敏感文件（0 否，1 是）" }
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

- `../../scripts/upload/save-file-by-path.py`
