# GET /open-api/document-database/file/getChildFiles

## 作用

浏览指定目录下的直接子项（文件和文件夹），用于展示"某目录下有什么"。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `parentId` | Long | 是 | 父目录 ID（根目录传 0） |
| `type` | Integer | 否 | 过滤资源类型：空为所有，1 只查文件夹，2 只查文件 |
| `order` | Integer | 否 | 排序规则：1 倒序更新，2 顺序更新，3 倒序创建，4 顺序创建，5 倒序名字，6 顺序名字 |
| `excludeFileTypes` | String | 否 | 排除的文件业务分类，多个用逗号分隔 |
| `excludeFolderNames` | String | 否 | 排除的文件夹名称，多个用逗号分隔 |
| `returnFileDesc` | Boolean | 否 | 是否带回文件描述摘要（建议传 true） |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["parentId"],
  "properties": {
    "parentId": { "type": "integer", "description": "父目录 ID，根目录传 0" },
    "type": { "type": "integer", "description": "过滤类型：1 文件夹，2 文件，空为所有" },
    "order": { "type": "integer", "description": "排序规则" },
    "excludeFileTypes": { "type": "string", "description": "排除的文件类型" },
    "excludeFolderNames": { "type": "string", "description": "排除的文件夹名称" },
    "returnFileDesc": { "type": "boolean", "description": "是否返回文件描述" }
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
          "type": { "type": "integer" },
          "parentId": { "type": "integer" },
          "hasChild": { "type": "boolean" },
          "size": { "type": "integer" },
          "suffix": { "type": "string" },
          "fileType": { "type": "string" },
          "ancestorNames": { "type": "string" },
          "fileDescription": { "type": "string" },
          "createTime": { "type": "integer" },
          "createTimeStr": { "type": "string" }
        }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/browse/browse.py`
