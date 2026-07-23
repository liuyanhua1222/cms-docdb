---
name: cms-docdb
description: 公司内部知识库/资料库/法务文档—目录浏览与搜索，读全文或下载/预览；上传与归档；已存在文件用新版本与定稿更新（禁止覆盖），删除须确认；Open API 仅允许通过本仓库脚本执行。
metadata:
  skillcode: cms-docdb
  github: https://github.com/liuyanhua1222/cms-docdb
  openclaw:
    requires:
      bins:
        - python3
        - python
---

# cms-docdb — 索引

OpenClaw 技能 **`name`** 为 `cms-docdb`，与仓库目录名和 **`skillcode`** 保持一致。用于公司内部 **知识库 / 资料库 / 法务文档**（康哲、德镁、玄关等产品入口）的目录浏览、搜索、读写与归档。接口侧用 `appCode` 区分产品；明细见下节「产品通道」。

本文件提供能力边界与路由规则。详细说明见 `references/`，实际执行见 `scripts/`。

**当前版本**: 1.3.0

**接口版本**: 所有业务接口统一使用 `/open-api/*` 前缀，鉴权类型全部为 `appKey`。对齐 API v2.5+（含 `app/listAll`）。

**能力概览（8 块能力）**：
- `browse`：发现可用**应用通道**与空间、获取个人空间 ID、浏览目录结构、最近使用、最近上传与全空间上传记录
- `query`：搜索文件，找到文件后获取内容、下载链接或预览链接
- `upload`：新建文件或文件夹——上传纯文本/物理文件、显式创建目录到目标通道下的空间（仅用于新建）
- `delete`：删除指定文件（高风险，需用户确认）
- `manage`：重命名/移动文件；更新已有文件内容（版本管理）；查看历史版本；版本定稿
- `share`：协同分享（`t_file_share`）；分享/撤销；分享列表（分享给我、我的分享）
- `apply`：权限申请（先查审批人，再 submit）
- `grant`：目录授权（`t_file_grant`，空间成员；增量 upsert/revoke）

## 适用范围与歧义排除（技能门控，强制）

- **本 skill 唯一指向**：通过 **appKey** 访问内部 **document-database** 开放接口（**`/open-api/document-database/*`**）。常用说法：**知识库**、**资料库**、**文档数据库**、**法务文档**、**康哲/玄关/德镁知识库**、**康哲/德镁资料库**、**在线知识库**、**公司知识库**。
- **产品通道（appCode，以 `t_doc_app` 为准，勿混用）**：
  - `kz_doc`：玄关知识库；康哲/德镁**资料库**（文档数据库）
  - `kz_knowledge_base`：康哲/德镁**知识库**
  - `fw_doc`：法务文档
  - （`gz_doc` 规章制度本次不接入）
- **明确不使用本 skill**：钉钉知识库/钉盘、企微微盘、飞书云文档、语雀、Notion、Confluence、SharePoint、石墨等。
- **OpenClaw 路由建议**：提及「知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill。
- **意图不明时（强制）**：先 `get-app-list.py`（企业可用应用）收敛选项 → 唯一则直用，多个则追问；**禁止**未筛就抛外企业产品。选定后拉空间必须带 `--app-code`。
- **不猜测**：意图或通道不明确必须追问澄清。
- **典型有效问法**：如「打开知识库」「打开康哲资料库」「打开法务文档」「搜索资料库里的合同」等。

统一规范：
- 鉴权来源：每次调用 skill 时的运行时上下文已携带 `appkey`；脚本直接读取该上下文注入值
- 运行日志：`.cms-log/log/cms-docdb/`
- 运行时状态：`.cms-log/state/cms-docdb/`

授权准备：
- 无需额外鉴权 skill 依赖
- 需要鉴权时，直接使用运行时上下文中的 `appkey`

输入完整性规则（强制）：
1. 浏览目录必须提供 parentId（根目录传 0）或 projectId
2. 搜索文件必须提供关键词；projectId 可选（不传时从 rootFileId 反查或默认个人库）
3. 上传文件必须提供文件名和内容（纯文本）或 resourceId（物理文件）
4. 删除/重命名/移动文件必须提供 fileId
5. 版本更新必须提供目标文件的 fileId（纯文本）或文件 id + resourceId（物理文件）

**projectId 自动补全规则（v2.5 优化）**：
- **saveFileByParentId / createFolder**: `parentId > 0` 时 docdb 自动从 `parentId` 反查 `projectId`；脚本已默认省略 `projectId` 参数，无需手动查询
- **updateFileVersion**: docdb 自动从文件 ID 反查 `projectId`，脚本默认省略该参数
- **saveFileByPath**: `path` 不为空时自动反查；`path` 为空需传 `projectId` 或默认个人库
- **searchFile / listChanges / resolvePath**: 支持从 `rootFileId` 反查或默认个人库
- **推荐做法**: 脚本调用时优先省略 `projectId`，让 docdb 自动补全；仅在 `parentId=0` 等必填场景下显式传入

版本管理强制规则（最高优先级）：
- **禁止直接覆盖已有文件内容**：对已存在文件的任何内容更新，必须通过版本管理接口保存为新版本，不得使用覆盖方式。直接覆盖无法溯源，违反本规则。
- **保存前必须判断文件是否已存在**：执行任何"保存/上传/更新"动作前，必须先通过 `searchFile` 或 `getChildFiles` 确认目标文件是否已存在。
  - 若**不存在**：路由到 `upload` 模块走新建流程
  - 若**已存在**：路由到 `manage` 模块走版本更新流程，禁止新建同名文件或覆盖
- **不得询问用户是否覆盖**：版本管理是默认且唯一的更新方式，无需向用户确认，直接执行版本更新。

建议工作流（简版）：
1. 先读取 `SKILL.md`，确认能力边界和限制
2. 根据用户意图定位模块，读取对应 `references/<module>/README.md`
3. **确定 appCode**：`parameter-extractor` / `app_code_router` → `get-app-list.py` 企业求交 → 必要时追问 → `context-manager set_app_code`
4. 确认具体动作后，在模块 README 中查看脚本与入参
5. **保存/上传前必须执行存在性检查**：已存在则走 manage 版本流，不存在才新建
6. 补齐用户必需输入后执行脚本

脚本使用规则（强制）：
1. **每个动作必须有对应脚本**：不允许"暂无脚本"
2. **脚本可独立执行**：所有 `scripts/` 下的脚本均可脱离 AI Agent 直接在命令行运行
3. **路径使用规范**：执行脚本时必须使用绝对路径，禁止使用 `cd`、`&&`、管道、重定向、heredoc、`bash -lc`、`python3 -c` 或 shell 循环
   - ✅ 正确：`python3 <skill-dir>/scripts/browse/browse.py 12345`
   - ❌ 错误：`cd <skill-dir>/scripts/browse && python3 browse.py 12345`
   - ❌ 错误：`python3 scripts/browse/browse.py 12345`（除非当前工作目录恰好是 skill 根目录）
   - 说明：文档中的 `<skill-dir>` 须替换为当前 skill 根目录的绝对路径；相对路径仅便于阅读
4. **先读模块说明再执行**：执行脚本前，必须先阅读对应模块的 `references/<module>/README.md`
5. **鉴权一致**：涉及 appKey 时，统一从小龙虾运行时上下文获取 `appkey`
6. **运行命令统一**：文档与示例统一写 `python3`；执行时优先 `python3`，若命令不存在（常见于部分 Windows 仅提供 `python`）则改用 `python` 等价替换

## 安全基线（强制，v1.3.0+）

1. **TLS 默认开启校验**：所有脚本经 `scripts/common/docdb_open_api.ssl_context()` 访问 HTTPS；禁止在业务脚本内自行 `CERT_NONE`。
2. **临时排障**：仅当证书链路异常时，可设环境变量 `CMS_DOCDB_INSECURE_SSL=1` 临时关闭校验；排障后必须撤销，不得写回脚本。
3. **写入类门禁**：删除、授权/撤权、分享授权/撤销、移动/重命名、版本更新/定稿、上传落库、审批、加成员等脚本：
   - 预览：`--dry-run`（stdout JSON，含 `dryRun:true`，不发 HTTP，无需 appkey）
   - 真实调用：必须 `--confirm YES`
   - 物理删除：必须 `--confirm PHYSICAL`（与 `--physical` 同用）
4. **Agent 闭环**：先向用户确认高危意图 → 用户明确同意后 → 再执行脚本并带上对应 `--confirm`；禁止无确认静默写入。
5. **admin**：`add-member` 等同属写入门禁；无独立 `references/admin/`，以本基线为准。

意图路由与加载规则（强制）：
1. **先路由再加载**：必须先判定模块，再打开该模块的 `references/<module>/README.md`
2. **先读说明再调用**：在执行前，必须加载对应模块说明
3. **脚本必须执行**：所有接口调用必须通过脚本执行，不允许跳过
4. **不猜测**：若意图不明确，必须追问澄清
5. **歧义门控**：提及「知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill
6. **企业先筛**：通道不明时必须先 `get-app-list`，再决定 `appCode` / 追问；拉空间列表必须带对应 `--app-code`

宪章（必须遵守）：
1. **只读索引**：`SKILL.md` 只描述"能做什么"和"去哪里读"，不写具体接口参数
2. **按需加载**：默认只读 `SKILL.md`，只有触发某模块时才加载该模块的 `references` 与 `scripts`
3. **对外克制**：对用户只输出"可用能力、必要输入、结果链接或摘要"，不暴露鉴权细节与内部字段
4. **素材优先级**：用户给了文件或 URL，必须先提取内容再确认，确认后才触发生成或写入
5. **生产约束**：仅允许生产域名与生产协议，不引入任何测试地址
6. **危险操作**：删除/授权/上传等高风险操作须先获得用户明确确认，再执行脚本并传入 `--confirm YES`（物理删除用 `--confirm PHYSICAL`）；禁止仅口头确认后无门禁调用
7. **脚本语言限制**：调用 Open API 的业务脚本必须使用 Python 3（`python3`）
8. **重试策略**：出错时间隔 1 秒、最多重试 3 次，超过后终止并上报
9. **禁止无限重试**：严禁无限循环重试
10. **输出规范**：脚本输出优先按 `resultCode`、`resultMsg`、`data` 读取，对用户输出最小必要信息：摘要/必要输入/链接，不回显完整 JSON 响应
11. **直接执行**：所有脚本必须可直接通过 `python3`（或 `python`）执行，不依赖包装脚本

## 触发配置

### 意图触发词

下表为**常见**说法，**非穷举**。提及「知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill。

| 模块 | 触发词模式 |
|-----|-----------|
| `browse` | "知识库"、"资料库"、"法务文档"、"打开康哲资料库"、"打开法务文档"、"打开玄关/康哲/德镁知识库"、"文档数据库"、"空间列表"、"最近使用" |
| `query` | "查询知识库/资料库/法务中的…"、"搜索xxx"、"查找xxx"、"读取xxx"、"总结文件" |
| `upload` | "上传到康哲资料库/法务文档/知识库"、"保存到文档数据库"、"归档"、"新建文件夹" |
| `delete` | "删除文件"、"移除文件"、"删掉xxx" |
| `manage` | "重命名xxx"、"移动文件"、"更新内容"、"版本管理"、"历史版本"、"定稿" |
| `share` | "分享文件给xxx"、"协同分享"、"撤销分享"、"分享给我的"、"我的分享" |
| `apply` | "申请权限"、"我的申请"、"待我审批"、"查询审批人" |
| `grant` | "目录授权"、"收回目录授权" |

**意图标签与模块目录（强制）**：`intent-matcher.py` 输出的 `data.intent` 中，`browse`、`query`、`upload`、`delete`、`manage`、`share`、`apply`、`grant` 与同名 `references/<module>/`、`scripts/<module>/` 一致。`read` 仅为意图分类标签（匹配「读取/总结文件」等话术），**不存在** `references/read/`；一旦 `intent` 为 `read`，路由与加载必须与 **`query`** 相同，使用 `references/query/` 与 `scripts/query/`。

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
- **当前应用通道**：`current_app_code`（及可选 `current_app_name`），多轮复用

### 多轮对话支持

| 场景 | 示例 | 处理方式 |
|-----|------|---------|
| 指代解析 | "读取这个文件" | 自动补全最后操作的文件ID |
| 路径继承 | "查看上一级" | 使用当前目录上下文 |
| 连续操作 | "搜索xxx" → "读取它" → "保存新版本" | 上下文链式传递 |
| 通道复用 | 已选康哲资料库后继续搜索 | 复用 `current_app_code=kz_doc` |

### 触发脚本

| 脚本 | 功能 |
|-----|------|
| `intent-matcher.py` | 意图识别和关键词提取 |
| `context-manager.py` | 上下文管理（含 `set_app_code`） |
| `parameter-extractor.py` | 参数提取（含 `app_code` / `needs_app_list`） |
| `common/app_code_router.py` | 话术→appCode；可与企业 listAll 求交 |
| `browse/get-app-list.py` | 当前企业可用应用通道列表 |
| `project-matcher.py` | 智能空间名称匹配 |
| `folder-navigator.py` | 智能目录导航 |

### 触发流程图

```text
用户输入（如："打开法务文档" / "打开知识库" / "保存到康哲知识库的产品资料目录"）
    ↓
意图识别 (intent-matcher.py)
    ↓
参数提取 (parameter-extractor.py)
    → app_code / product_label / needs_app_list
    → 空间名候选、目录候选…
    ↓
步骤0: 企业应用先筛（get-app-list + app_code_router 求交）
    • 唯一 → resolved_app_code，context set_app_code
    • 多个 → 仅列本企业选项追问
    ↓
步骤1: 空间匹配 — get-project-list.py --app-code <resolved>（或 uploadableList）
    → project-matcher.py
    ↓
步骤2: 目录导航 — folder-navigator.py（如需要）
    ↓
路由到对应模块 → 执行脚本 → 更新上下文 → 返回结果
```

### 智能导航优化说明（重要）

**问题背景**：
1. **空间匹配失败**："保存到康哲知识库" → 分词错误 → "找不到空间"
2. **目录匹配失败**："放到产品资料目录" → 盲目搜索
3. **通道错误**："打开康哲资料库" 未传 `appCode=kz_doc` → 落到知识库池

**优化方案**：企业应用先筛 + 分层智能导航。拉空间列表**必须**带 `--app-code`。

#### 层级0️⃣ / 1️⃣：应用通道与空间

```text
用户："打开知识库" / "打开康哲资料库" / "打开法务文档" / "保存到康哲知识库"
  ↓
app_code_router + get-app-list（企业求交）→ appCode
  ↓
get-uploadable-list.py --app-code … 或 get-project-list.py --app-code …
  ↓
project-matcher.py → 精确/包含/组合/模糊匹配
```

详见 [references/SPACE_MATCHING_GUIDE.md](./references/SPACE_MATCHING_GUIDE.md)

#### 层级2️⃣：目录智能导航

```text
用户："放到产品资料目录"
  ↓
提取目录名：["产品资料"]
  ↓
调用 folder-navigator.py → 在空间内递归搜索
  → 精确匹配：目录名完全匹配
  → 包含匹配：目录名包含关键词
  → 模糊匹配：相似度 > 0.6
  → 递归搜索：最多3层深度
  ↓
匹配结果处理：
  • 唯一匹配 → 直接使用该目录
  • 多个匹配 → 展示完整路径让用户选择
  • 无匹配 → 建议创建新目录或浏览目录结构
```

**支持的目录格式**：
- 单层目录："放到产品资料目录"
- 多级路径："上传到产品资料/慷彼申"
- 混合分隔符："产品资料-慷彼申" → 自动转为 "产品资料/慷彼申"

详见 [references/SMART_NAVIGATION_GUIDE.md](./references/SMART_NAVIGATION_GUIDE.md)

#### 完整示例

**用户输入**：
```
"把这份报告保存到康哲知识库的产品资料目录"
```

**AI 执行流程**：
```bash
# 1. 参数提取
parameter-extractor.py "..."
# → project_name_candidates: ["康哲", "知识库"]
# → folder_name_candidates: ["产品资料"]
# → needs_project_list: true
# → needs_folder_navigation: true

# 2. 空间匹配
get-uploadable-list.py  # 获取可上传空间列表
project-matcher.py --candidates "康哲,知识库" --project-list '[...]'
# → project_id: 10001, project_name: "康哲知识库", match_type: "exact"

# 3. 目录导航
folder-navigator.py --project-id 10001 --folder-name "产品资料"
# → folder_id: 20001, folder_name: "产品资料", match_type: "exact"

# 4. 执行上传
upload-content.py "报告内容" "报告.md" \
  --project-id 10001 \
  --folder-name "产品资料"
```

**AI 输出**：
```
已保存到知识库 ✅

文件：报告.md
空间：康哲知识库
位置：康哲知识库 / 产品资料

你继续让我修改这份文档时，我会更新到同一个知识库文件（通过版本管理生成新版本）。
```

模块路由与能力索引：

| 用户意图 | 模块 | 能力摘要 | 模块说明 | 脚本 |
|---|---|---|---|---|
| "打开公司在线知识库"、"打开康哲/玄关/德镁知识库"、"浏览一下xxx文件夹"、"知识库里有什么"、"查看某个目录的内容"、"目录结构"、"我最近上传了什么"、"最近使用/最近看过哪些文件"、"查文件信息/根据fileId查projectId/这个文件在哪个空间" | `browse` | 发现空间、浏览目录、最近使用、上传记录、轻量元数据反查 | `./references/browse/README.md` | `./scripts/browse/browse.py` 等 |
| "查询知识库中的…"、"搜索知识库里的…"、"搜索xxx"、"查询xxx"、"查找xxx"、"看看这个文件的内容"、"帮我读取xxx文件"、"帮我总结一下xxx文件" | `query` | 搜索文件并读取内容、下载链接或预览链接 | `./references/query/README.md` | `./scripts/query/search.py` |
| "存到康哲/玄关/德镁知识库"、"上传到知识库"、"上传xxx到知识库"、"把这份文档归档"、"帮我保存这个文件"、"在知识库里建个文件夹" | `upload` | 新建文件/文件夹（已存在文件内容更新走 manage 版本流） | `./references/upload/README.md` | `./scripts/upload/upload-content.py` 等 |
| "帮我把xxx删了"、"删除xxx文件"、"把xxx文件移除" | `delete` | 删除指定文件（高风险，需确认） | `./references/delete/README.md` | `./scripts/delete/delete-file.py` |
| "帮我把xxx重命名"、"把xxx改名为yyy"、"把这个文件移到xxx文件夹"、"更新一下知识库里的xxx"、"把最新内容存进去"、"这个文档有更新，存一下"、"查看xxx文件的历史版本"、"把这个版本定稿" | `manage` | 重命名/移动文件；更新已有文件内容（版本管理）；查看历史版本；版本定稿 | `./references/manage/README.md` | 见 `./references/manage/README.md`（按意图选择对应脚本） |
| "把这个文件分享给张三"、"授权给李四预览"、"给王五开查看权限"、"协同分享这个文件夹"、"取消张三的分享"、"分享给我的文件"、"我的分享列表" | `share` | 协同分享与分享列表 | `./references/share/README.md` | `./scripts/share/upsert-file-share-grants.py` 等 |
| "申请这个文件的权限"、"我的申请"、"待我审批的申请"、"同意/拒绝权限申请" | `apply` | 权限申请与审批 | `./references/apply/README.md` | `./scripts/apply/get-approvers.py` 等 |
| "给空间成员开目录权限"、"目录授权"、"收回某人的目录授权" | `grant` | 目录授权（t_file_grant，须空间成员） | `./references/grant/README.md` | `./scripts/grant/upsert-file-grants.py` 等 |

**增量授权原则（强制）**：目录授权与协同分享均使用 upsert + 定点 revoke；**禁止**调用全量 replace 接口（`updateFileShare`、`updateFileGrantV2`）。

能力树：

```text
cms-docdb/
├── SKILL.md
├── references/
│   ├── browse/README.md
│   ├── query/README.md
│   ├── upload/README.md
│   ├── delete/README.md
│   ├── manage/README.md
│   ├── share/README.md
│   ├── apply/README.md
│   └── grant/README.md
└── scripts/
    ├── common/
    │   └── docdb_open_api.py
    ├── browse/
    │   ├── browse.py
    │   ├── get-level1-folders.py
    │   ├── get-personal-project-id.py
    │   ├── get-project-list.py
    │   ├── get-recent-files.py
    │   ├── get-my-upload-records.py
    │   ├── get-my-recent-used.py
    │   ├── get-file-basic-info.py
    │   └── get-uploadable-list.py
    ├── query/
    │   ├── search.py
    │   ├── get-full-content.py
    │   ├── get-download-info.py
    │   ├── download-file.py
    │   ├── get-file-content.py
    │   └── batch-get-content.py
    ├── upload/
    │   ├── upload-content.py
    │   ├── save-file-by-path.py
    │   ├── save-file-by-parent-id.py
    │   ├── upload-whole-file.py
    │   ├── check-slice.py
    │   ├── register-slice.py
    │   ├── merge-resource.py
    │   ├── create-folder.py
    │   └── get-file-download-info.py
    ├── delete/
    │   └── delete-file.py
    ├── manage/
    │   ├── update-file-name.py
    │   ├── move-file.py
    │   ├── update-file-property.py
    │   ├── update-file-version.py
    │   ├── get-version-list.py
    │   ├── get-last-version.py
    │   └── finalize-version.py
    ├── share/
    │   ├── search-emp-by-name.py
    │   ├── get-my-share-permissions.py
    │   ├── upsert-file-share-grants.py
    │   ├── get-file-shares.py
    │   ├── get-share-url.py
    │   ├── revoke-file-share-grants.py
    │   ├── list-shared-to-me.py
    │   └── list-my-shares.py
    ├── apply/
    │   ├── get-approvers.py
    │   ├── submit-apply.py
    │   ├── list-my-applies.py
    │   ├── list-pending-applies.py
    │   ├── list-processed-applies.py
    │   └── review-apply.py
    ├── grant/
    │   ├── upsert-file-grants.py
    │   └── revoke-file-grants.py
    └── admin/
        ├── add-member.py
        └── is-project-member.py
```

**文档对齐**：Open API 契约以 `dev-guide/02.产品业务AI文档/知识库/`（v2.4+）为准；**1.16** 最近使用、**06** 分享列表、**07** 目录授权、**08** 权限申请均已提供对应脚本。
