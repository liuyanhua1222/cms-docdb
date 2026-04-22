# query — 使用说明

## 什么时候使用

- 用户说"帮我找一下 xxx 文件"、"搜索 xxx"
- 用户想找到某个文件并获取其内容、下载链接或预览链接

## 标准流程

1. 鉴权预检（按 `cms-auth-skills/SKILL.md` 获取 appKey；如未安装先安装）
2. 调用 `scripts/query/search.py` 搜索文件
3. 根据搜索结果数量处理：
   - **多个结果**：返回文件列表，告知用户可以进一步操作
   - **单个结果**：直接提供操作选项
4. 用户确定目标文件后，根据需求调用：
   - `getFullFileContent` — 获取文件全文（AI 分析/总结）
   - `getDownloadInfo` — 获取下载/预览链接
   - `getFileContent` — 分页读取大文件内容
5. 输出结果摘要或链接

## 场景说明

| 用户意图 | 调用的接口 |
|---|---|
| 让 AI 总结/分析文件内容 | `getFullFileContent` |
| 下载文件到本地 | `getDownloadInfo` + `forceDownload=true` |
| 预览文件（在线打开） | `getDownloadInfo` + `forceDownload=false` |
| 分段读取大文件内容（仅 doc 类型） | `getFileContent` |

> ⚠️ **物理文件（fileType=file）内容读取**：物理文件的内容请使用 `getFullFileContent`，不要使用 `getFileContent`（后者对物理文件返回空）。

## 用户话术示例

- "帮我找一下周报 xxx"
- "搜索一下有没有这份文档"
- "找到这个文件后帮我总结一下"
- "帮我下载这个文件"
- "直接打开让我看看内容"
