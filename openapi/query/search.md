# GET /open-api/document-database/file/searchFile

## 作用

根据关键词搜索文件或目录，返回匹配的文件和文件夹列表。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `nameKey` | String | 是 | 搜索关键词。**中文必须 URL 编码（UTF-8）** |
| `projectId` | Long | 否 | 项目/空间 ID（不传则全局搜索） |
| `rootFileId` | Long | 否 | 指定根目录 ID（在此目录下搜索） |
| `startTime` | Long | 否 | 创建时间-开始时间戳（毫秒） |
| `endTime` | Long | 否 | 创建时间-结束时间戳（毫秒） |
| `isFileStorage` | Boolean | 否 | 是否为文件存储范围（默认 false） |
| `excludeFileTypes` | String | 否 | 排除的文件类型，逗号分隔 |
| `excludeFolderNames` | String | 否 | 排除的文件夹名称，逗号分隔 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["nameKey"],
  "properties": {
    "nameKey": { "type": "string", "description": "搜索关键词，中文需 URL 编码" },
    "projectId": { "type": "integer" },
    "rootFileId": { "type": "integer" },
    "startTime": { "type": "integer" },
    "endTime": { "type": "integer" },
    "isFileStorage": { "type": "boolean" },
    "excludeFileTypes": { "type": "string" },
    "excludeFolderNames": { "type": "string" }
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
        "folders": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "integer" },
              "name": { "type": "string" },
              "type": { "type": "integer" },
              "parentId": { "type": "integer" },
              "hasChild": { "type": "boolean" },
              "ancestorNames": { "type": "string" },
              "createTime": { "type": "integer" },
              "createTimeStr": { "type": "string" }
            }
          }
        },
        "files": {
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
  }
}
```

## 脚本映射

- `../../scripts/query/search.py`
