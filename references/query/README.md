# query — 模块说明

## 适用场景

- 用户说"帮我找一下 xxx 文件"、"搜索 xxx"
- 用户想找到某个文件并获取其内容、下载链接或预览链接
- AI Agent 需要读取文件内容进行分析、总结或 RAG 消费

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 搜索文件 | nameKey（关键词） | projectId, rootFileId, startTime, endTime, excludeFileTypes |
| 获取文件全文 | fileId | — |
| 获取下载/预览凭据 | fileId | forceDownload, versionNumber |
| 分页读取文件内容 | fileId | pageNumber |
| 批量获取文件全文 | files（fileId 列表） | — |

## 动作列表

### 1. 搜索文件
- **脚本**: `search.py`
- **用途**: 根据关键词搜索文件或目录，返回匹配的文件和文件夹列表
- **注意**: 中文关键词必须 URL 编码（UTF-8）
- **输出**: 返回 `{ folders: [...], files: [...] }`

### 2. 获取文件全文（AI 摘要/RAG 首选）
- **脚本**: `get-full-content.py`
- **用途**: 获取文件的全局提纯文本（Markdown 格式），面向 AI Agent 的智能全文提取
- **适用**: 所有文件类型（doc/file/work_report 等）
- **输出**: 返回 Markdown 格式全文字符串

### 3. 获取下载/预览凭据
- **脚本**: `get-download-info.py`
- **用途**: 获取文件的下载链接或在线预览凭据
- **注意**: 返回的 downloadUrl 为临时签名链接，有时效性
- **输出**: 返回 downloadUrl、openWith（打开方式）、lazyLoad 等

### 4. 分页读取文件内容
- **脚本**: `get-file-content.py`
- **用途**: 分页获取文件的排版文本内容，主要用于 UI 界面流式展示
- **注意**: 物理文件（fileType=file）请使用 `get-full-content.py`，本接口对物理文件返回空
- **输出**: 返回该页的排版文本字符串

### 5. 批量获取文件全文
- **脚本**: `batch-get-content.py`
- **用途**: 批量获取多个文件的全文内容，减少往返次数，提升 RAG 效率
- **注意**: 建议单次不超过 10 个文件
- **输出**: 返回每个文件的 `{ fileId, content, status, message }`

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

`openWith` 打开方式枚举：
- `0`: 默认/下载
- `1`: WPS
- `2`: PDF
- `3`: 畅写
- `4`: HTML
- `5`: 工作协同
- `6`: PDF-v5

## 标准流程

1. 鉴权预检（通过 `cms-auth-skills` 获取 appKey）
2. 调用 `search.py` 搜索文件
3. 根据搜索结果数量处理：
   - 多个结果：返回文件列表，告知用户可以进一步操作
   - 单个结果：直接提供操作选项
4. 用户确定目标文件后，根据需求调用：
   - AI 分析/总结 → `get-full-content.py`
   - 下载/预览 → `get-download-info.py`
   - 分页读取大文件 → `get-file-content.py`
   - 批量读取多文件 → `batch-get-content.py`

## 用户话术示例

- "帮我找一下周报 xxx"
- "搜索一下有没有这份文档"
- "找到这个文件后帮我总结一下"
- "帮我下载这个文件"
- "直接打开让我看看内容"
