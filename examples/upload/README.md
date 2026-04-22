# upload — 使用说明

## 什么时候使用

- 用户说"帮我把这个文档存到知识库"、"上传 xxx 到知识库"、"把这份报告归档"
- 用户想让 AI 分析完某个内容后自动保存结果

## 上传模式对比

| 场景 | 接口 | fileType | 必填参数 |
|---|---|---|---|
| **纯文本上传**（Markdown/HTML/纯文本） | `uploadContent` | — | `content` + `fileName` |
| **物理文件上传**（PDF/DOCX/MD 等二进制） | `saveFileByPath` | `file` | `resourceId`（需先上传文件服务） |

## 标准流程

### 纯文本上传（推荐用于 AI 生成内容）

1. 鉴权预检（按 `cms-auth-skills/SKILL.md` 获取 appKey）
2. 确认文件名（建议带扩展名）和内容
3. 调用 `scripts/upload/upload-content.py`
4. 自动归档至个人空间"和AI的对话"目录（或指定目录）
5. 返回 fileId

### 物理文件上传（PDF/DOCX/MD 等）

1. 鉴权预检
2. 调用 `scripts/upload/upload-whole-file.py`，传入本地文件路径 → 获得 `resourceId`
3. 调用 `scripts/upload/save-file-by-path.py` + `resourceId` 绑定到知识库
4. 返回 fileId

## 用户话术示例

- "帮我把这段总结存到知识库" → `uploadContent`
- "上传这份 PDF 到 AI 生成文件夹" → `upload-whole-file` + `saveFileByPath`
- "把这份 Markdown 文档归档" → 优先 `uploadContent`，或走物理文件路径
