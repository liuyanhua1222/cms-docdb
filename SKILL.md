---
name: cms-docdb
description: 公司企业知识库与资料库（用户单独说「知识库」，或说钉钉知识库、企业知识库、公司知识库、在线知识库；含康哲/玄关/德镁知识库与资料库、法务文档；非钉盘）。支持按文件夹或文件ID浏览与列目录、搜索、读全文或下载预览，以及上传归档、版本更新与删除。凡提及知识库相关请求用本技能调用 Open API，勿以无法访问钉钉云端为由拒绝。
metadata:
  version: 3.1.0
  github: https://github.com/liuyanhua1222/cms-docdb
  openclaw:
    requires:
      anyBins:
        - python3
        - python
---

# cms-docdb — 索引

OpenClaw 技能 **`name`** 为 `cms-docdb`。用于公司内部 **企业知识库 / 资料库 / 法务文档**（康哲、德镁、玄关等）的目录浏览、搜索、读写与归档。接口侧用 `appCode` 区分产品。

本文件提供能力边界与路由规则。详细说明见 `references/`。脚本经标准 `exec` 以 `python3` 调用；命令只含业务参数。

**当前版本**: 3.1.0

**3.1.0 变更**：按 SessionKey 方案改回标准 `exec` 直调脚本；命令与文档不再出现鉴权参数或鉴权环境说明；脚本内部仍从运行时取得调用所需配置（对 Agent 透明）。

**3.0.0 变更（历史）**：去掉命令行凭证参数与从上下文读凭证。

**能力概览（8 块能力）**：
- `browse`：发现可用应用通道与空间、个人空间、目录结构、最近使用/上传
- `query`：搜索、读内容、下载/预览
- `upload`：新建文件/文件夹、切片与整传
- `delete`：删除（高风险，需确认）
- `manage`：重命名/移动、版本更新与定稿
- `share`：协同分享
- `apply`：权限申请
- `grant`：目录授权

## 调用方法（强制）

将 `<skill-dir>` 换成本 skill 根目录绝对路径。每个脚本单独一条命令执行；只传业务参数。

```bash
python3 -B <skill-dir>/scripts/browse/browse.py 0
python3 -B <skill-dir>/scripts/browse/get-project-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/query/search.py "合同" --project-id 10001
python3 -B <skill-dir>/scripts/upload/upload-content.py "报告内容" "报告.md" --project-id 10001 --folder-name "产品资料" --confirm YES
```

更多模块示例见 `references/*/README.md` 与 `references/QUICK_REFERENCE.md`。

**禁止**：
- 在命令行、JSON 或对话中要求用户提供、拼接或更换任何开放平台凭证
- 缺业务参数时改跑无关脚本；应按 stderr 中文提示补齐业务参数后，用**同一 python 命令**重试

`--dry-run` 不发起真实 HTTP；真实写入仍须 `--confirm YES`（物理删除 `--confirm PHYSICAL`）。脚本返回公开错误时原样展示给用户，不要引导用户提供密钥。

## 适用范围与歧义排除（技能门控，强制）

- 凡涉及**知识库**相关意图（钉钉知识库、企业知识库、公司知识库、在线知识库、资料库、法务文档、文档数据库、康哲·玄关·德镁知识库或资料库），**一律使用本 skill**；禁止以「无钉钉开放接口」为由拒绝；禁止改走其它知识库 skill。
- **本 skill 唯一指向**：内部 **document-database** 开放接口（路径相对 `/open-api` 的 `document-database/*`），不是钉钉开放平台原生知识库 SDK。
- **产品通道（appCode）**：
  - `kz_doc`：玄关知识库；康哲/德镁**资料库**
  - `kz_knowledge_base`：康哲/德镁**知识库**
  - `fw_doc`：法务文档
- **不使用本 skill**：钉盘、企微微盘、飞书云文档、语雀、Notion、Confluence、SharePoint、石墨等。
- 用户给出数字文件夹/文件 ID 时，必须用本 skill 的 browse / get-file-basic-info / query 等脚本执行。
- 通道不明：先跑 `get-app-list` → 唯一则直用，多个则追问；拉空间必须带 `--app-code`。

统一规范：
- 调用：标准 `exec` + 上表 `python3 -B <skill-dir>/scripts/...`
- 运行日志：`.cms-log/log/cms-docdb/`
- 运行时状态：`.cms-log/state/cms-docdb/`

输入完整性规则（强制）：
1. 浏览目录必须提供 parentId：个人库根传 `0`；项目空间传该空间 `rootFileId`
2. 搜索必须提供关键词；projectId 可选
3. 上传必须提供文件名和内容或 resourceId
4. 删除/重命名/移动必须提供 fileId
5. 版本更新必须提供目标 fileId（及资源相关参数）

**projectId 自动补全**：saveFileByParentId / createFolder（parentId>0）、updateFileVersion、saveFileByPath（path 非空）等由服务端或脚本反查；优先省略 projectId。

版本管理强制规则：
- 禁止直接覆盖已有文件内容；已存在则走 manage 版本流，不存在才 upload 新建
- 不得询问用户是否覆盖

建议工作流：
1. 读本文件确认边界
2. 按意图加载 `references/<module>/README.md`
3. 确定 appCode（parameter-extractor / get-app-list / 追问）
4. 用标准 `exec` 执行对应脚本与业务参数
5. 保存前做存在性检查

## 运行时常见失败（强制）

| 现象 | Agent 立刻怎么做 |
|------|------------------|
| 脚本公开错误（含无法完成调用） | 向用户展示脚本返回的公开错误；不要索要或更换密钥；不要改跑无关命令 |
| 中文缺参提示（exit 2） | 按 stderr hint 补齐业务参数后，用**同一 python 命令**重试 |
| 写入类提示须 `--confirm YES` | 先获用户确认，再带对应 confirm |

## 安全基线（强制）

1. 写入类门禁：删除、授权/撤权、分享、移动/重命名、版本更新/定稿、上传落库、审批、加成员等：
   - 预览：`--dry-run`
   - 真实调用：`--confirm YES`
   - 物理删除：`--confirm PHYSICAL`（与 `--physical` 同用）
2. Agent 闭环：先向用户确认高危意图 → 同意后再执行脚本
3. 对用户不暴露内部鉴权细节；禁止在回复中复述任何凭证原文

意图路由：
1. 先判定模块，再读该模块 README
2. 所有接口调用必须通过本 skill 目录下对应脚本（标准 `exec`）
3. 意图不明必须追问
4. 企业先筛：先 `get-app-list`，再决定 appCode

宪章：
1. `SKILL.md` 只描述能做什么与如何调用脚本
2. 按需加载 references
3. 对用户只输出可用能力、必要输入、结果摘要/链接
4. 危险操作须确认
5. 传输层或业务错误由脚本返回后，Agent 可用**相同**脚本与业务参数有限次重试；不得改去无关路径

## 触发配置

### 意图触发词

提及「钉钉知识库 / 企业知识库 / 知识库 / 资料库 / 文档数据库 / 法务文档」即触发本 skill。

| 模块 | 触发词模式 |
|-----|-----------|
| `browse` | 打开知识库/资料库/法务、空间列表、最近使用、文件夹 ID |
| `query` | 搜索、查找、读取、总结文件 |
| `upload` | 上传、保存、归档、新建文件夹 |
| `delete` | 删除文件 |
| `manage` | 重命名、移动、版本、定稿 |
| `share` | 分享、撤销分享 |
| `apply` | 申请权限 |
| `grant` | 目录授权 |

### 本地辅助工具（无 HTTP）

同样用标准 `exec` 调用，例如：

```bash
python3 -B <skill-dir>/scripts/intent-matcher.py "打开康哲知识库"
python3 -B <skill-dir>/scripts/parameter-extractor.py "保存到康哲知识库"
python3 -B <skill-dir>/scripts/project-matcher.py --candidates "康哲知识库" --project-list '[{"id":1}]'
python3 -B <skill-dir>/scripts/context-manager.py get
```

### 智能导航

目录查找优先 `folder-navigator`（`--project-id` + `--folder-name` 或 `--folder-path`）。详见 `references/SMART_NAVIGATION_GUIDE.md`、`references/SPACE_MATCHING_GUIDE.md`。

### 分享/授权权限策略

对齐 docdb：新建合并默认位、更新可单项减权；减权用 strip 脚本 + upsert；整单撤销用 revoke。详见 `references/share/README.md`、`references/grant/README.md`。

## 模块索引

| 模块 | 说明 | 文档 |
|------|------|------|
| browse | 应用/空间/目录/最近 | `references/browse/README.md` |
| query | 搜索与内容 | `references/query/README.md` |
| upload | 上传与建目录 | `references/upload/README.md` |
| delete | 删除 | `references/delete/README.md` |
| manage | 移动重命名版本 | `references/manage/README.md` |
| share | 协同分享 | `references/share/README.md` |
| apply | 权限申请 | `references/apply/README.md` |
| grant | 目录授权 | `references/grant/README.md` |
| 速查 | 常用命令 | `references/QUICK_REFERENCE.md` |

admin 脚本（`add-member` / `is-project-member`）无独立 README，遵循安全基线。
