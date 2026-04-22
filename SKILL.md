---
name: cms-docdb
description: 知识库浏览器 — 浏览目录结构、搜索文件、上传文件到知识库、删除/重命名/移动文件
skillcode: cms-docdb
dependencies:
  - cms-auth-skills
---

# cms-docdb — 索引

本文件提供**能力宪章 + 能力树 + 按需加载规则**。详细参数与流程见各模块 `openapi/` 与 `examples/`。

**当前版本**: v0.1

**接口版本**: 所有业务接口统一使用 `/open-api/*` 前缀，鉴权类型全部为 `appKey`。

**能力概览（5 块能力）**：
- `browse`：发现可用空间、获取个人空间 ID、浏览目录结构、查看最近上传
- `query`：搜索文件，找到文件后获取内容、下载链接或预览链接
- `upload`：上传纯文本或物理文件到知识库
- `delete`：删除指定文件（高风险，需用户确认）
- `manage`：重命名/移动文件

统一规范：
- 认证与鉴权：`cms-auth-skills/SKILL.md`
- 通用约束：`cms-auth-skills/SKILL.md`

授权依赖：
- 当接口声明需要 `appKey` 时，先尝试读取 `cms-auth-skills/SKILL.md`
- 如果已安装，直接按 `cms-auth-skills/SKILL.md` 中的鉴权规则准备对应 `appKey`
- 如果未安装，先执行 `npx clawhub@latest install cms-auth-skills --force`
- 如果上面的安装方式不可用，再执行 `npx clawhub@latest install https://github.com/spzwin/cms-auth-skills.git --force`
- 安装完成后，再继续执行需要鉴权的操作

输入完整性规则（强制）：
1. 浏览目录必须提供 parentId（根目录传 0）或 projectId
2. 搜索文件必须提供关键词
3. 上传文件必须提供文件名和内容（纯文本）或 resourceId（物理文件）
4. 删除/重命名/移动文件必须提供 fileId

建议工作流（简版）：
1. 读取 `SKILL.md` 与 `cms-auth-skills/SKILL.md`，明确能力范围、鉴权与安全约束。
2. 识别用户意图并路由模块，先打开对应模块的 `openapi/browse/api-index.md` 等。
3. 确认具体接口后，加载对应接口文档（如 `openapi/query/search.md`）获取入参/出参/Schema。
4. 补齐用户必需输入，必要时先读取用户文件/URL 并确认摘要。
5. 参考 `examples/query/README.md` 等组织话术与流程。
6. **执行对应脚本**：调用对应脚本（如 `scripts/query/search.py`）执行接口调用，获取结果。**所有接口调用必须通过脚本执行，不允许跳过脚本直接调用 API。**

脚本使用规则（强制）：
1. **每个接口必须有对应脚本**：每个接口文档都必须有对应的脚本，不允许"暂无脚本"。
2. **脚本可独立执行**：所有 `scripts/` 下的脚本均可脱离 AI Agent 直接在命令行运行。
3. **先读文档再执行**：执行脚本前，**必须先阅读对应模块的 `api-index.md`**（如 `openapi/browse/api-index.md`）。
4. **入参来源**：脚本的所有入参定义与字段说明以 `openapi/` 文档为准，脚本仅负责编排调用流程。
5. **鉴权一致**：涉及 appKey 时，统一依赖 `cms-auth-skills/SKILL.md`。

意图路由与加载规则（强制）：
1. **先路由再加载**：必须先判定模块，再打开该模块的 `api-index.md`。
2. **先读文档再调用**：在描述调用或执行前，必须加载对应接口文档。
3. **脚本必须执行**：所有接口调用必须通过脚本执行，不允许跳过。
4. **不猜测**：若意图不明确，必须追问澄清。

宪章（必须遵守）：
1. **只读索引**：`SKILL.md` 只描述"能做什么"和"去哪里读"，不写具体接口参数。
2. **按需加载**：默认只读 `SKILL.md` + `cms-auth-skills/SKILL.md`，只有触发某模块时才加载该模块的 `openapi`、`examples` 与 `scripts`。
3. **对外克制**：对用户只输出"可用能力、必要输入、结果链接或摘要"，不暴露鉴权细节与内部字段。
4. **素材优先级**：用户给了文件或 URL，必须先提取内容再确认，确认后才触发生成或写入。
5. **生产约束**：仅允许生产域名与生产协议，不引入任何测试地址。
6. **接口拆分**：每个 API 独立成文档；模块内 `api-index.md` 仅做索引。
7. **危险操作**：删除文件等高风险操作应礼貌确认，不直接执行。
8. **脚本语言限制**：所有脚本**必须使用 Python 编写**。
9. **重试策略**：出错时**间隔 1 秒、最多重试 3 次**，超过后终止并上报。
10. **禁止无限重试**：严禁无限循环重试。
11. **输出规范**：脚本输出优先按 `resultCode`、`resultMsg`、`data` 读取，对用户输出最小必要信息：摘要/必要输入/链接，不回显完整 JSON 响应。

模块路由与能力索引（合并版）：

| 用户意图（示例） | 模块 | 能力摘要 | 接口文档 | 示例模板 | 脚本 |
|---|---|---|---|---|---|
| "帮我看看这个目录下有什么"、"浏览一下xxx文件夹"、"帮我看看知识库里有什么"、"查看某个目录的内容" | `browse` | 发现空间、浏览目录结构、查看最近上传 | `./openapi/browse/api-index.md` | `./examples/browse/README.md` | `./scripts/browse/` |
| "找一下xxx文件"、"搜索xxx"、"看看这个文件的内容"、"帮我读取xxx文件"、"获取xxx的文件内容"、"帮我总结一下xxx文件" | `query` | 搜索文件并读取内容、下载链接或预览链接 | `./openapi/query/api-index.md` | `./examples/query/README.md` | `./scripts/query/` |
| "帮我把这个存到知识库"、"上传xxx到知识库"、"把这份文档归档"、"帮我保存这个文件" | `upload` | 上传纯文本或物理文件到知识库 | `./openapi/upload/api-index.md` | `./examples/upload/README.md` | `./scripts/upload/` |
| "帮我把xxx删了"、"删除xxx文件"、"把xxx文件移除" | `delete` | 删除指定文件（高风险，需确认） | `./openapi/delete/api-index.md` | `./examples/delete/README.md` | `./scripts/delete/` |
| "帮我把xxx重命名"、"把xxx改名为yyy"、"把这个文件移到xxx文件夹"、"帮我移动这个文件" | `manage` | 重命名或移动文件 | `./openapi/manage/api-index.md` | `./examples/manage/README.md` | `./scripts/manage/` |

能力树（实际目录结构）：
```text
cms-docdb/
├── SKILL.md
├── openapi/
│   ├── browse/
│   │   ├── api-index.md
│   │   ├── browse.md
│   │   ├── get-level1-folders.md
│   │   ├── get-personal-project-id.md
│   │   ├── get-project-list.md
│   │   ├── get-recent-files.md
│   │   └── get-uploadable-list.md
│   ├── query/
│   │   ├── api-index.md
│   │   ├── search.md
│   │   ├── get-full-content.md
│   │   ├── get-download-info.md
│   │   ├── get-file-content.md
│   │   └── batch-get-content.md
│   ├── upload/
│   │   ├── api-index.md
│   │   ├── upload-content.md
│   │   ├── save-file-by-path.md
│   │   ├── save-file-by-parent-id.md
│   │   ├── upload-whole-file.md
│   │   ├── check-slice.md
│   │   ├── register-slice.md
│   │   ├── merge-resource.md
│   │   └── get-file-download-info.md
│   ├── delete/
│   │   ├── api-index.md
│   │   └── delete-file.md
│   └── manage/
│       ├── api-index.md
│       └── update-file-property.md
├── examples/
│   ├── browse/README.md
│   ├── query/README.md
│   ├── upload/README.md
│   ├── delete/README.md
│   └── manage/README.md
└── scripts/
    ├── browse/
    │   ├── README.md
    │   ├── browse.py
    │   ├── get-level1-folders.py
    │   ├── get-personal-project-id.py
    │   ├── get-project-list.py
    │   ├── get-recent-files.py
    │   └── get-uploadable-list.py
    ├── query/
    │   ├── README.md
    │   ├── search.py
    │   ├── get-full-content.py
    │   ├── get-download-info.py
    │   ├── get-file-content.py
    │   └── batch-get-content.py
    ├── upload/
    │   ├── README.md
    │   ├── upload-content.py
    │   ├── save-file-by-path.py
    │   ├── save-file-by-parent-id.py
    │   ├── upload-whole-file.py
    │   ├── check-slice.py
    │   ├── register-slice.py
    │   ├── merge-resource.py
    │   └── get-file-download-info.py
    ├── delete/
    │   ├── README.md
    │   └── delete-file.py
    └── manage/
        ├── README.md
        └── update-file-property.py
```
