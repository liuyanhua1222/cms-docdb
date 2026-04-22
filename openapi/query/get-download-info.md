# GET /open-api/document-database/file/getDownloadInfo

## 作用

获取文件的下载链接或在线预览凭据。用于获取文件的下载地址，或生成可嵌入预览的凭据。

**鉴权类型**
- `appKey`

**Headers**
- `appKey`
- `Content-Type: application/json`

**Query 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fileId` | Long | 是 | 文件 ID |
| `forceDownload` | Boolean | 否 | true 下载，false 在线预览（默认 false） |
| `seeOriginal` | Boolean | 否 | 预览是否查看原文 |
| `source` | String | 否 | 来源 |
| `versionNumber` | Integer | 否 | 版本号 |
| `bypassRisk` | Boolean | 否 | 是否绕过风险检查 |

## 请求 Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["fileId"],
  "properties": {
    "fileId": { "type": "integer", "description": "文件 ID" },
    "forceDownload": { "type": "boolean", "description": "true 下载，false 在线预览" },
    "seeOriginal": { "type": "boolean" },
    "source": { "type": "string" },
    "versionNumber": { "type": "integer" },
    "bypassRisk": { "type": "boolean" }
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
        "downloadUrl": { "type": "string", "description": "下载/预览 URL（临时签名，有时效性）" },
        "fileId": { "type": "integer" },
        "fileName": { "type": "string" },
        "suffix": { "type": "string" },
        "size": { "type": "integer" },
        "fileType": { "type": "string" },
        "openWith": { "type": "integer", "description": "打开方式：0 默认，1 WPS，2 PDF，3 畅写，4 HTML，5 工作协同，6 PDF-v5" },
        "lazyLoad": { "type": "boolean", "description": "是否按需加载（PDF 分页加载）" },
        "lastVersion": { "type": "boolean" },
        "projectId": { "type": "integer" }
      }
    }
  }
}
```

## 脚本映射

- `../../scripts/query/get-download-info.py`
