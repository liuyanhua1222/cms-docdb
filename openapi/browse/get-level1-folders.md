# GET /open-api/document-database/file/getLevel1Folders

## 作用

拉取指定项目空间的绝对顶层（根目录）下的所有文件夹及文件。用于浏览项目根目录全景。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `projectId` | Long | 是 | 项目/空间 id |
| `order` | Integer | 否 | 排序规则：1 更新倒序，2 更新顺序，5 名字倒序，6 名字顺序 |
| `permissionQuery` | String | 否 | 权限查询条件 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["projectId"],
  "properties": {
    "projectId": { "type": "integer", "description": "项目/空间 ID" },
    "order": { "type": "integer", "description": "排序规则" },
    "permissionQuery": { "type": "string" }
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

- `../../scripts/browse/get-level1-folders.py`
