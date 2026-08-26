---
name: cms-docdb
description: 公司企业知识库与资料库（用户单独说「知识库」，或说钉钉知识库、企业知识库、公司知识库、在线知识库；含康哲/玄关/德镁知识库与资料库、法务文档；非钉盘）。支持按文件夹或文件ID浏览与列目录、搜索、读全文或下载预览，以及上传归档、版本更新与删除。凡提及知识库相关请求用本技能调用 Open API，勿以无法访问钉钉云端为由拒绝。
metadata:
  version: 3.1.3
  github: https://github.com/liuyanhua1222/cms-docdb
  openclaw:
    requires:
      anyBins:
        - python3
        - python
---

# cms-docdb — 索引

OpenClaw 技能 **`name`** 为 `cms-docdb`。用于公司内部 **企业知识库 / 资料库 / 法务文档**（康哲、德镁、玄关等；用户常说的「钉钉知识库」「企业知识库」即本 Open API 文档库，非钉盘）的目录浏览、搜索、读写与归档。接口侧用 `appCode` 区分产品。

本文件提供能力边界与路由规则。详细说明见 `references/`。脚本经标准 `exec` 以 `python3` 调用；命令只含业务参数。

**当前版本**: 3.1.3

**3.1.3 变更**：清理根路径/个人库同类教义歧义——upload 根目录示例强制 `--project-id`；去掉「默认个人库」含糊表述；列根/打开位置文案与 get-level1 hint 对齐。

**3.1.2 变更**：纠偏个人/空间根浏览路由——禁止 `browse.py 0`；列根须 `get-personal-project-id`（或已知 projectId）→ `get-level1-folders`；`browse.py` 仅用于非零 parentId 下钻。

**3.1.1 变更**：恢复并优化 2.0.3 业务导航（意图路由、能力树、触发流程、权限索引）；审查收紧智能导航为短要点+外链；鉴权仍对 Agent 透明。

**3.1.0 变更**：按 SessionKey 方案改回标准 `exec`；命令与文档不再出现鉴权参数或鉴权环境说明。

**3.0.0 变更（历史）**：去掉命令行凭证参数与从上下文读凭证。

**能力概览（8 块能力）**：
- `browse`：发现可用应用通道与空间、个人空间 ID、目录结构、最近使用/上传与全空间上传记录
- `query`：搜索、读全文或摘要、下载/预览链接
- `upload`：新建文件/文件夹、切片与整传（已存在文件内容更新走 manage 版本流）
- `delete`：删除（高风险，需确认）
- `manage`：重命名/移动、版本更新与定稿、历史版本
- `share`：协同分享与分享列表、单项减权
- `apply`：权限申请与审批
- `grant`：目录授权（空间成员；增量 upsert / 减权 / 收回）

## 调用方法（强制）

将 `<skill-dir>` 换成本 skill 根目录绝对路径。每个脚本单独一条命令；只传业务参数。禁止 `cd`/`&&`/管道/重定向/heredoc/`bash -lc`/`python3 -c`。优先 `python3 -B`（若无则 `python -B`）。

```bash
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py
python3 -B <skill-dir>/scripts/browse/get-level1-folders.py <projectId>
python3 -B <skill-dir>/scripts/browse/get-app-list.py
python3 -B <skill-dir>/scripts/browse/get-project-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/browse/browse.py 12345
python3 -B <skill-dir>/scripts/query/search.py "合同" --project-id 10001
python3 -B <skill-dir>/scripts/upload/upload-content.py "报告内容" "报告.md" --project-id 10001 --folder-name "产品资料" --confirm YES
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料"
```

更多模块示例见 `references/*/README.md` 与 `references/QUICK_REFERENCE.md`。

**禁止**：
- 在命令行、JSON 或对话中要求用户提供、拼接或更换任何开放平台凭证
- 缺业务参数时改跑无关脚本；应按 stderr 中文提示补齐后，用**同一 python 命令**重试
- 自造 `/tmp` 脚本或跳过本仓库 `scripts/` 调文档库接口

`--dry-run` 不发起真实 HTTP；真实写入须 `--confirm YES`（物理删除 `--confirm PHYSICAL`）。脚本返回公开错误时原样展示，不要引导用户提供密钥。

## 适用范围与歧义排除（技能门控，强制）

- 凡涉及**知识库**相关意图（钉钉知识库、企业知识库、公司知识库、在线知识库、资料库、法务文档、文档数据库、康哲·玄关·德镁知识库或资料库），**一律使用本 skill**；禁止以「无钉钉开放接口 / 无法访问钉钉云端」为由拒绝；禁止改走其它知识库 skill。
- **本 skill 唯一指向**：内部 **document-database** 开放接口（路径相对 `/open-api` 的 `document-database/*`），不是钉钉开放平台原生知识库 SDK。
- **产品通道（appCode，以 `t_doc_app` 为准，勿混用）**：
  - `kz_doc`：玄关知识库；康哲/德镁**资料库**（文档数据库）
  - `kz_knowledge_base`：康哲/德镁**知识库**
  - `fw_doc`：法务文档
  - （`gz_doc` 规章制度本次不接入）
- **不使用本 skill**：钉盘、企微微盘、飞书云文档、语雀、Notion、Confluence、SharePoint、石墨等；以及明确要求钉钉开放平台官方知识库/钉盘 API 的请求。
- 用户给出数字文件夹/文件 ID 并要求找到/列出/读取时，必须用本 skill 的 browse / get-file-basic-info / query 等执行。
- **OpenClaw 路由**：提及「钉钉知识库 / 企业知识库 / 知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill。
- **意图不明**：先 `get-app-list` 收敛选项 → 唯一则直用，多个则追问；选定后拉空间必须带 `--app-code`。不得因话术含「钉钉」而拒用本 skill。
- **典型有效问法**：「打开知识库」「打开钉钉知识库里这个文件夹」「读取企业知识库公共文档…」「打开康哲资料库」「打开法务文档」「搜索资料库里的合同」。

统一规范：
- 调用：标准 `exec` + 上节 `python3 -B <skill-dir>/scripts/...`
- 运行日志：`.cms-log/log/cms-docdb/`
- 运行时状态：`.cms-log/state/cms-docdb/`

输入完整性规则（强制）：
1. 列个人/空间根：先取 `projectId`（个人用 `get-personal-project-id`，共享空间用列表接口），再 `get-level1-folders.py <projectId>`。**禁止** `browse.py 0`。下钻已知非零文件夹（含空间 `rootFileId`）才用 `browse.py`
2. 搜索必须提供关键词；projectId 可选
3. 上传必须提供文件名和内容（纯文本）或 resourceId（物理文件）
4. 删除/重命名/移动必须提供 fileId
5. 版本更新必须提供目标 fileId（纯文本）或 fileId + resourceId（物理文件）

**projectId 自动补全**：
- saveFileByParentId / createFolder：`parentId > 0` 时可省略 projectId；**`parentId = 0`（空间根）必须显式 `--project-id`**
- updateFileVersion：可从文件反查，默认可省略
- saveFileByPath：**必须**提供 projectId（脚本位置参数必填）；path 非空时服务端可辅助路径解析
- upload-content：不传 `--project-id` 时走个人库写入捷径；传到指定空间则必须带 `--project-id`
- 推荐：非根目录优先省略 projectId；空间根写入勿把「仅传 parentId=0」当成个人库捷径

版本管理强制规则（最高优先级）：
- **禁止直接覆盖**已有文件内容；更新必须走版本管理
- 保存前须用 search 或列目录确认是否已存在：不存在 → `upload` 新建；已存在 → `manage` 版本流
- **不得询问用户是否覆盖**；版本更新是默认唯一方式

建议工作流：
1. 读本文件确认边界
2. 按意图加载 `references/<module>/README.md`
3. 确定 appCode（parameter-extractor / app_code_router / get-app-list / 追问）
4. 用标准 `exec` 执行对应脚本与业务参数
5. 保存前做存在性检查

脚本使用规则（强制）：
1. 每个动作须有对应脚本；不允许「暂无脚本」
2. 必须用 skill 根绝对路径单行直调；先读模块 README 再执行

## 运行时常见失败（强制）

| 现象 | Agent 立刻怎么做 |
|------|------------------|
| 脚本公开错误（含无法完成调用） | 展示公开错误；不索要或更换密钥；不改跑无关命令 |
| `exec preflight: complex interpreter…` | 改写为单行 `python3 -B <skill-dir>/scripts/... <业务参>` 后重试 |
| 重定向 / `Directory nonexistent` | 禁止 shell `>`；结果读 stdout；下载优先省略 `--output` |
| 中文缺参提示（exit 2） | 按 stderr hint 补齐后用**同一 python 命令**重试 |
| 误用 `browse.py 0`（exit 2） | 按 stderr：个人根用 `get-personal-project-id` → `get-level1-folders`；勿再传 0 |
| 根目录写入缺 `--project-id`（create-folder / save-file-by-parent-id 传 parentId=0） | 按 stderr 补 `--project-id`（个人空间先 get-personal-project-id）；勿仅传 0 |
| `Read-only` / `__pycache__` | 使用 `python3 -B`；勿在 skill 目录造文件 |
| 自造脚本 / 非 scripts 路径 | **停止**；只用本仓库 `scripts/` |
| 写入须 `--confirm YES` | 先获用户确认再带 confirm；可先 `--dry-run` |

## 安全基线（强制）

1. TLS 默认开启校验；禁止业务脚本自行关闭证书校验
2. 写入类门禁（删除、授权/撤权、分享、移动/重命名、版本更新/定稿、上传落库、审批、加成员等）：
   - 预览：`--dry-run`（不发 HTTP）
   - 真实调用：`--confirm YES`
   - 物理删除：`--confirm PHYSICAL`（与 `--physical` 同用）
3. Agent 闭环：先确认高危意图 → 同意后再执行
4. 对用户不暴露内部鉴权细节；禁止在回复中复述任何凭证原文
5. admin（`add-member` / `is-project-member`）无独立 README，遵循本基线

意图路由：
1. 先判定模块，再读该模块 README
2. 所有接口调用必须通过本 skill 目录下对应脚本（标准 `exec`）
3. 意图不明必须追问；企业先筛：先 `get-app-list`，再决定 appCode

宪章：
1. `SKILL.md` 只描述能做什么与如何调用脚本；按需加载 references
2. 对用户只输出可用能力、必要输入、结果摘要/链接
3. 危险操作须确认后再带 `--confirm`
4. 传输/业务错误可由脚本返回后，用**相同**脚本与业务参数有限次重试；禁止无限重试
5. 输出优先按 `resultCode` / `resultMsg` / `data` 读；不回显完整 JSON
6. 业务脚本须 Python 3，可直接 `python3`/`python` 执行

## 触发配置

### 意图触发词

下表为**常见**说法，**非穷举**。提及「钉钉知识库 / 企业知识库 / 知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill。

| 模块 | 触发词模式 |
|-----|-----------|
| `browse` | "钉钉知识库"、"企业知识库"、"知识库"、"资料库"、"法务文档"、"打开康哲资料库"、"打开法务文档"、"打开玄关/康哲/德镁知识库"、"文档数据库"、"空间列表"、"最近使用"、"这个文件夹ID" |
| `query` | "查询知识库/资料库/法务中的…"、"搜索xxx"、"查找xxx"、"读取xxx"、"总结文件"、"读取钉钉知识库里的文件" |
| `upload` | "上传到康哲资料库/法务文档/知识库"、"保存到文档数据库"、"归档"、"新建文件夹" |
| `delete` | "删除文件"、"移除文件"、"删掉xxx" |
| `manage` | "重命名xxx"、"移动文件"、"更新内容"、"版本管理"、"历史版本"、"定稿" |
| `share` | "分享文件给xxx"、"协同分享"、"分享给我的"、"我的分享" |
| `apply` | "申请权限"、"我的申请"、"待我审批"、"查询审批人" |
| `grant` | "目录授权"、"收回目录授权" |

**意图标签与模块目录（强制）**：`intent-matcher.py` 的 `data.intent` 中，`browse`/`query`/`upload`/`delete`/`manage`/`share`/`apply`/`grant` 与同名 `references/<module>/`、`scripts/<module>/` 一致。`read` 仅为意图分类标签，**不存在** `references/read/`；`intent=read` 时路由与加载必须与 **`query`** 相同。

### 参数提取规则

1. 关键词：引号、括号内及「xxx文件」格式
2. 路径：「产品资料-慷彼申」等层级路径
3. 指代：「这个文件」「它」关联上下文
4. 数字：版本号、页码等

### 上下文管理

- 会话历史：最近约 10 条
- 当前目录 / 最后文件 / 当前项目（id + name）
- 当前应用通道：`current_app_code`（及可选 name），多轮复用

### 多轮对话支持

| 场景 | 示例 | 处理 |
|-----|------|------|
| 指代解析 | "读取这个文件" | 补全最后操作的文件 ID |
| 路径继承 | "查看上一级" | 用当前目录上下文 |
| 连续操作 | 搜索 → 读取 → 保存新版本 | 上下文链式传递 |
| 通道复用 | 已选康哲资料库后继续搜索 | 复用 `current_app_code=kz_doc` |

### 触发脚本

| 脚本 | 功能 |
|-----|------|
| `intent-matcher.py` | 意图识别与关键词 |
| `context-manager.py` | 上下文（含 `set_app_code`） |
| `parameter-extractor.py` | 参数提取（含 `app_code` / `needs_app_list`） |
| `common/app_code_router.py` | 话术→appCode；可与企业 listAll 求交 |
| `browse/get-app-list.py` | 当前企业可用应用通道 |
| `project-matcher.py` | 智能空间名称匹配 |
| `folder-navigator.py` | 智能目录导航 |

### 触发流程图

```text
用户输入（如："打开法务文档" / "保存到康哲知识库的产品资料目录"）
    ↓
意图识别 (intent-matcher.py)
    ↓
参数提取 (parameter-extractor.py)
    → app_code / needs_app_list / 空间名与目录候选…
    ↓
步骤0: 企业应用先筛（get-app-list + app_code_router）
    • 唯一 → resolved_app_code，context set_app_code
    • 多个 → 仅列本企业选项追问
    ↓
步骤1: 空间匹配 — get-project-list / get-uploadable-list --app-code …
    → project-matcher.py
    ↓
步骤2: 目录导航 — folder-navigator.py（如需要）
    ↓
路由到对应模块 → 执行脚本 → 更新上下文 → 返回结果
```

### 智能导航（要点）

1. 企业先筛：`get-app-list` + `app_code_router` 确定 `appCode`
2. 空间匹配：带 `--app-code` 拉列表 → `project-matcher`
3. 目录：优先 `folder-navigator`（`--project-id` + `--folder-name` 或 `--folder-path`）

细则见 `references/SPACE_MATCHING_GUIDE.md`、`references/SMART_NAVIGATION_GUIDE.md`。

## 模块路由与能力索引

| 用户意图 | 模块 | 能力摘要 | 说明 | 代表脚本 |
|---|---|---|---|---|
| 打开知识库/资料库/法务、浏览目录、最近使用/上传、按 fileId 查空间 | `browse` | 应用/空间/目录/最近/元数据 | `references/browse/README.md` | `scripts/browse/browse.py`、`scripts/browse/get-app-list.py`、`scripts/browse/get-uploadable-list.py` |
| 搜索、查询、读取、总结文件 | `query` | 搜索与内容/下载预览 | `references/query/README.md` | `scripts/query/search.py`、`scripts/query/get-full-content.py` |
| 上传、保存、归档、新建文件夹 | `upload` | 新建（更新走 manage） | `references/upload/README.md` | `scripts/upload/upload-content.py`、`scripts/upload/create-folder.py` |
| 删除、移除文件 | `delete` | 删除（须确认） | `references/delete/README.md` | `scripts/delete/delete-file.py` |
| 重命名、移动、更新内容、历史版本、定稿 | `manage` | 重命名/移动/版本 | `references/manage/README.md` | `scripts/manage/update-file-name.py`、`scripts/manage/update-file-version.py`、`scripts/manage/finalize-version.py` |
| 协同分享、分享列表、取消协同 | `share` | 分享 upsert/列表/revoke | `references/share/README.md` | `scripts/share/upsert-file-share-grants.py` |
| 去掉某人分享某项权限（非整单撤销） | `share` | 单项减权 | 同上 | `scripts/share/strip-share-permissions.py` |
| 申请权限、我的申请、审批 | `apply` | 申请与审批 | `references/apply/README.md` | `scripts/apply/submit-apply.py`、`scripts/apply/review-apply.py` |
| 目录授权、收回目录授权 | `grant` | 目录授权 | `references/grant/README.md` | `scripts/grant/upsert-file-grants.py` |
| 去掉某人目录某项权限 | `grant` | 单项减权 | 同上 | `scripts/grant/strip-grant-permissions.py` |

速查：`references/QUICK_REFERENCE.md`。

**增量授权原则（强制）**：目录授权与协同分享均用 upsert + 定点 revoke；**禁止**调用全量 replace 接口（如 `updateFileShare`、`updateFileGrantV2`）。

### 分享/授权权限策略（强制）

| 场景 | 规则 | 脚本 |
|---|---|---|
| 协同分享 · 新分享 | 合并默认位 + 用户指定权限 | `upsert-file-share-grants.py` |
| 协同分享 · 去掉某项权限 | **禁止**整单 revoke；用 strip，**保留 read** | `strip-share-permissions.py` |
| 协同分享 · 完全取消 | 人从分享列表消失 | `revoke-file-share-grants.py` |
| 目录授权 · 新授权 | 须指定 permissions；合并 `read+preview` | `upsert-file-grants.py` |
| 目录授权 · 去掉某项 | **禁止**整单 revoke；用 strip，**保留 read** | `strip-grant-permissions.py` |
| 目录授权 · 完全收回 | 授权记录删除 | `revoke-file-grants.py` |

细则见 `references/share/README.md`、`references/grant/README.md`。

## 能力树

```text
cms-docdb/
├── SKILL.md
├── references/          # 各模块 README + SPACE/SMART/QUICK
└── scripts/
    ├── intent-matcher.py
    ├── parameter-extractor.py
    ├── context-manager.py
    ├── project-matcher.py
    ├── folder-navigator.py
    ├── common/          # 内部；除触发表点名外勿直调 cli_args / safety / docdb_open_api
    │   └── app_code_router.py
    ├── browse/
    │   ├── browse.py
    │   ├── get-app-list.py
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
    │   ├── update-file-property.py   # 废弃：改用 update-file-name / move-file
    │   ├── update-file-version.py
    │   ├── get-version-list.py
    │   ├── get-last-version.py
    │   └── finalize-version.py
    ├── share/
    │   ├── search-emp-by-name.py
    │   ├── get-my-share-permissions.py
    │   ├── upsert-file-share-grants.py
    │   ├── strip-share-permissions.py
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
    │   ├── get-file-grants.py
    │   ├── strip-grant-permissions.py
    │   └── revoke-file-grants.py
    └── admin/
        ├── add-member.py
        └── is-project-member.py
```

**文档对齐**：以各模块 README 与公司知识库 OpenAPI 契约为准。
