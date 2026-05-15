---
name: 官方企业知识库skill
description: 公司内部知识库—目录浏览与搜索，读全文或下载/预览；上传与归档；已存在文件用新版本与定稿更新（禁止覆盖），删除须确认；Open API 仅允许通过本仓库脚本执行。
skillcode: cms-docdb
github: https://github.com/liuyanhua1222/cms-docdb
dependencies:
  - cms-auth-skills
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - python
---

# cms-docdb — 索引

OpenClaw 技能 **`name`** 为 `cms-docdb`，与仓库目录名和 **`skillcode`** 保持一致。本技能用于访问公司内部知识库（康哲/玄关/德镁知识库）。

本文件提供能力边界与路由规则。详细说明见 `references/`，实际执行见 `scripts/`。

**当前版本**: 1.0.4

**接口版本**: 所有业务接口统一使用 `/open-api/*` 前缀，鉴权类型全部为 `appKey`。

**能力概览（5 块能力）**：
- `browse`：发现可用空间、获取个人空间 ID、浏览目录结构、查看最近上传
- `query`：搜索文件，找到文件后获取内容、下载链接或预览链接
- `upload`：新建文件——上传纯文本或物理文件到 **康哲/玄关/德镁知识库**（内部应用侧；仅用于新建）
- `delete`：删除指定文件（高风险，需用户确认）
- `manage`：重命名/移动文件；更新已有文件内容（版本管理）；查看历史版本；版本定稿

## 适用范围与歧义排除（技能门控，强制）

- **本 skill 唯一指向**：通过 **appKey** 访问内部知识库应用所对接的 **document-database** 开放接口（路径形态 **`/open-api/document-database/*`**，OpenClaw **`name`：`cms-docdb`**；**`skillcode` / 技术代号**：**cms-docdb** / **document-database**）。**对用户与内部沟通常用说法**：**「康哲知识库」「玄关知识库」「德镁知识库」**及 **「公司在线知识库」**（同一类内部知识库应用的不同称呼/环境）。
- **明确不使用本 skill 的典型场景**（应改走对应产品能力或追问用户）：**钉钉知识库/钉盘**、**企业微信微盘**、**飞书知识库/云文档**、**语雀**、**Notion**、**Confluence**、**SharePoint**、**石墨** 等。
- **OpenClaw 路由建议**：**只要提及「知识库」就触发本 skill**。
- **典型有效问法（内部真实话术）**：如「打开知识库」「打开公司在线知识库」「请查询知识库中某政策标题并总结」「请阅读知识库中某文件夹内的文件」「能读产品资料-慷彼申里的内容吗」等，均在本 skill 能力范围内（具体模块依动作是浏览、搜索还是读全文而定）。

统一规范：
- 鉴权依赖：`cms-auth-skills/SKILL.md`
- 运行日志：`.cms-log/log/cms-docdb/`
- 运行时状态：`.cms-log/state/cms-docdb/`

授权依赖：
- 需要鉴权时先读取 `cms-auth-skills/SKILL.md`
- 如果未安装，先安装依赖，再继续执行

输入完整性规则（强制）：
1. 浏览目录必须提供 parentId（根目录传 0）或 projectId
2. 搜索文件必须提供关键词 + projectId（限定搜索范围，避免返回无关结果）
3. 上传文件必须提供文件名和内容（纯文本）或 resourceId（物理文件）
4. 删除/重命名/移动文件必须提供 fileId
5. 版本更新必须提供目标文件的 fileId（纯文本）或文件 id + projectId + resourceId（物理文件）

版本管理强制规则（最高优先级）：
- **禁止直接覆盖已有文件内容**：对已存在文件的任何内容更新，必须通过版本管理接口保存为新版本，不得使用覆盖方式。直接覆盖无法溯源，违反本规则。
- **保存前必须判断文件是否已存在**：执行任何"保存/上传/更新"动作前，必须先通过 `searchFile` 或 `getChildFiles` 确认目标文件是否已存在。
  - 若**不存在**：路由到 `upload` 模块走新建流程
  - 若**已存在**：路由到 `manage` 模块走版本更新流程，禁止新建同名文件或覆盖
- **不得询问用户是否覆盖**：版本管理是默认且唯一的更新方式，无需向用户确认，直接执行版本更新。

建议工作流（简版）：
1. 先读取 `SKILL.md`，确认能力边界和限制
2. 根据用户意图定位模块，读取对应 `references/<module>/README.md`
3. 确认具体动作后，读取 `scripts/<module>/README.md` 了解脚本入参
4. **保存/上传前必须执行存在性检查**：通过 `search.py` 或 `browse.py` 确认目标文件是否已存在。已存在则切换为版本更新流程（manage 模块），不存在才新建（upload 模块）
5. 补齐用户必需输入
6. 执行对应脚本

脚本使用规则（强制）：
1. **每个动作必须有对应脚本**：不允许"暂无脚本"
2. **脚本可独立执行**：所有 `scripts/` 下的脚本均可脱离 AI Agent 直接在命令行运行
3. **先读模块说明再执行**：执行脚本前，必须先阅读对应模块的 `references/<module>/README.md`
4. **鉴权一致**：涉及 appKey 时，统一依赖 `cms-auth-skills`

意图路由与加载规则（强制）：
1. **先路由再加载**：必须先判定模块，再打开该模块的 `references/<module>/README.md`
2. **先读说明再调用**：在执行前，必须加载对应模块说明
3. **脚本必须执行**：所有接口调用必须通过脚本执行，不允许跳过
4. **不猜测**：若意图不明确，必须追问澄清
5. **歧义门控**：**只要提及「知识库」就触发本 skill**

宪章（必须遵守）：
1. **只读索引**：`SKILL.md` 只描述"能做什么"和"去哪里读"，不写具体接口参数
2. **按需加载**：默认只读 `SKILL.md` + `cms-auth-skills/SKILL.md`，只有触发某模块时才加载该模块的 `references` 与 `scripts`
3. **对外克制**：对用户只输出"可用能力、必要输入、结果链接或摘要"，不暴露鉴权细节与内部字段
4. **素材优先级**：用户给了文件或 URL，必须先提取内容再确认，确认后才触发生成或写入
5. **生产约束**：仅允许生产域名与生产协议，不引入任何测试地址
6. **危险操作**：删除文件等高风险操作应礼貌确认，不直接执行
7. **脚本语言限制**：调用 Open API 的业务脚本必须使用 Python
8. **重试策略**：出错时间隔 1 秒、最多重试 3 次，超过后终止并上报
9. **禁止无限重试**：严禁无限循环重试
10. **输出规范**：脚本输出优先按 `resultCode`、`resultMsg`、`data` 读取，对用户输出最小必要信息：摘要/必要输入/链接，不回显完整 JSON 响应
11. **直接执行**：所有脚本必须可直接通过 Python 执行，不依赖包装脚本

## 触发配置

### 意图触发词

下表为**常见**说法，**非穷举**。**只要提及「知识库」就触发本 skill**。

| 模块 | 触发词模式 |
|-----|-----------|
| `browse` | "知识库"、"打开知识库"、"打开公司在线知识库"、"打开康哲/玄关/德镁知识库"、"浏览文件夹"、"查看目录"、"知识库里有什么"、"目录结构"、"空间列表"、"项目列表" |
| `query` | "查询知识库中的…"、"搜索知识库里的…"、"搜索xxx"、"查询xxx"、"查找xxx"、"检索xxx"、"帮我找xxx"、"搜索一下xxx"、"读取xxx"、"阅读xxx"、"查看xxx内容"、"打开文件"、"总结文件"、"提取信息" |
| `upload` | "上传到康哲/玄关/德镁知识库"、"保存到康哲/玄关/德镁知识库"、"上传到知识库"、"保存到知识库"、"归档文件"、"新建文件" |
| `delete` | "删除文件"、"移除文件"、"删掉xxx" |
| `manage` | "重命名xxx"、"移动文件"、"更新内容"、"版本管理"、"历史版本"、"定稿" |

**意图标签与模块目录（强制）**：`intent-matcher.py` 输出的 `data.intent` 中，`browse`、`query`、`upload`、`delete`、`manage` 与同名 `references/<module>/`、`scripts/<module>/` 一致。`read` 仅为意图分类标签（匹配「读取/总结文件」等话术），**不存在** `references/read/`；一旦 `intent` 为 `read`，路由与加载必须与 **`query`** 相同，使用 `references/query/` 与 `scripts/query/`。

### 参数提取规则

1. **关键词提取**：自动识别引号、括号内内容及"xxx文件"格式
2. **路径解析**：支持"产品资料-慷彼申"格式的层级路径
3. **指代处理**：理解"这个文件"、"它"等指代，自动关联上下文
4. **数字提取**：识别版本号、页码等数字参数

### 上下文管理

- **会话历史**：保留最近10条对话记录
- **当前目录**：记录用户正在浏览的目录（id + name）
- **最后文件**：记录用户最后操作的文件（id + name）
- **当前项目**：记录用户当前操作的项目（id + name）

### 多轮对话支持

| 场景 | 示例 | 处理方式 |
|-----|------|---------|
| 指代解析 | "读取这个文件" | 自动补全最后操作的文件ID |
| 路径继承 | "查看上一级" | 使用当前目录上下文 |
| 连续操作 | "搜索xxx" → "读取它" → "保存新版本" | 上下文链式传递 |

### 触发脚本

| 脚本 | 功能 |
|-----|------|
| `intent-matcher.py` | 意图识别和关键词提取 |
| `context-manager.py` | 上下文管理和状态维护 |
| `parameter-extractor.py` | 参数提取和缺失提示生成 |

### 触发流程图

```text
用户输入
    ↓
意图识别 (intent-matcher.py)
    ↓
参数提取 (parameter-extractor.py)
    ↓
上下文补全 (context-manager.py)
    ↓
┌──────────────────────┐
│ 参数是否完整？       │
└──────────────────────┘
    ↓
    ├─ 是 → 路由到对应模块
    │         ↓
    │     执行脚本
    │         ↓
    │     更新上下文
    │         ↓
    │     返回结果
    │
    └─ 否 → 生成追问提示
              ↓
          返回追问
```

模块路由与能力索引：

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|---|---|---|---|---|
| "打开公司在线知识库"、"打开康哲/玄关/德镁知识库"、"浏览一下xxx文件夹"、"知识库里有什么"、"查看某个目录的内容"、"目录结构" | `browse` | 发现空间、浏览目录结构、查看最近上传 | `./references/browse/README.md` | `./scripts/browse/browse.py` |
| "查询知识库中的…"、"搜索知识库里的…"、"搜索xxx"、"查询xxx"、"查找xxx"、"看看这个文件的内容"、"帮我读取xxx文件"、"帮我总结一下xxx文件" | `query` | 搜索文件并读取内容、下载链接或预览链接 | `./references/query/README.md` | `./scripts/query/search.py` |
| "存到康哲/玄关/德镁知识库"、"上传到知识库"、"上传xxx到知识库"、"把这份文档归档"、"帮我保存这个文件" | `upload` | 新建文件到内部知识库（仅用于新建，已存在则路由到 manage 走版本更新） | `./references/upload/README.md` | `./scripts/upload/upload-content.py` |
| "帮我把xxx删了"、"删除xxx文件"、"把xxx文件移除" | `delete` | 删除指定文件（高风险，需确认） | `./references/delete/README.md` | `./scripts/delete/delete-file.py` |
| "帮我把xxx重命名"、"把xxx改名为yyy"、"把这个文件移到xxx文件夹"、"更新一下知识库里的xxx"、"把最新内容存进去"、"这个文档有更新，存一下"、"查看xxx文件的历史版本"、"把这个版本定稿" | `manage` | 重命名/移动文件；更新已有文件内容（版本管理）；查看历史版本；版本定稿 | `./references/manage/README.md` | 见 `./scripts/manage/README.md`（按意图选择对应脚本） |

能力树：

```text
cms-docdb/
├── SKILL.md
├── references/
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
        ├── update-file-property.py
        ├── update-file-version.py
        ├── get-version-list.py
        ├── get-last-version.py
        └── finalize-version.py
```
