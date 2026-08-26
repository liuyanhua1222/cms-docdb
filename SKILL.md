---
name: cms-docdb
description: 公司企业知识库与资料库（用户单独说「知识库」，或说钉钉知识库、企业知识库、公司知识库、在线知识库；含康哲/玄关/德镁知识库与资料库、法务文档；非钉盘）。支持按文件夹或文件ID浏览与列目录、搜索、读全文或下载预览，以及上传归档、版本更新与删除。凡提及知识库相关请求用本技能调用 Open API，勿以无法访问钉钉云端为由拒绝。
skillcode: cms-docdb
openapi_auth: appKey
tools_provided:
  - name: add-member
    entry: scripts/admin/add-member.py
  - name: is-project-member
    entry: scripts/admin/is-project-member.py
  - name: get-approvers
    entry: scripts/apply/get-approvers.py
  - name: list-my-applies
    entry: scripts/apply/list-my-applies.py
  - name: list-pending-applies
    entry: scripts/apply/list-pending-applies.py
  - name: list-processed-applies
    entry: scripts/apply/list-processed-applies.py
  - name: review-apply
    entry: scripts/apply/review-apply.py
  - name: submit-apply
    entry: scripts/apply/submit-apply.py
  - name: browse
    entry: scripts/browse/browse.py
  - name: get-app-list
    entry: scripts/browse/get-app-list.py
  - name: get-file-basic-info
    entry: scripts/browse/get-file-basic-info.py
  - name: get-level1-folders
    entry: scripts/browse/get-level1-folders.py
  - name: get-my-recent-used
    entry: scripts/browse/get-my-recent-used.py
  - name: get-my-upload-records
    entry: scripts/browse/get-my-upload-records.py
  - name: get-personal-project-id
    entry: scripts/browse/get-personal-project-id.py
  - name: get-project-list
    entry: scripts/browse/get-project-list.py
  - name: get-recent-files
    entry: scripts/browse/get-recent-files.py
  - name: get-uploadable-list
    entry: scripts/browse/get-uploadable-list.py
  - name: context-manager
    entry: scripts/context-manager.py
  - name: delete-file
    entry: scripts/delete/delete-file.py
  - name: folder-navigator
    entry: scripts/folder-navigator.py
  - name: get-file-grants
    entry: scripts/grant/get-file-grants.py
  - name: revoke-file-grants
    entry: scripts/grant/revoke-file-grants.py
  - name: strip-grant-permissions
    entry: scripts/grant/strip-grant-permissions.py
  - name: upsert-file-grants
    entry: scripts/grant/upsert-file-grants.py
  - name: intent-matcher
    entry: scripts/intent-matcher.py
  - name: finalize-version
    entry: scripts/manage/finalize-version.py
  - name: get-last-version
    entry: scripts/manage/get-last-version.py
  - name: get-version-list
    entry: scripts/manage/get-version-list.py
  - name: move-file
    entry: scripts/manage/move-file.py
  - name: update-file-name
    entry: scripts/manage/update-file-name.py
  - name: update-file-property
    entry: scripts/manage/update-file-property.py
  - name: update-file-version
    entry: scripts/manage/update-file-version.py
  - name: parameter-extractor
    entry: scripts/parameter-extractor.py
  - name: project-matcher
    entry: scripts/project-matcher.py
  - name: batch-get-content
    entry: scripts/query/batch-get-content.py
  - name: download-file
    entry: scripts/query/download-file.py
  - name: get-download-info
    entry: scripts/query/get-download-info.py
  - name: get-file-content
    entry: scripts/query/get-file-content.py
  - name: get-full-content
    entry: scripts/query/get-full-content.py
  - name: search
    entry: scripts/query/search.py
  - name: get-file-shares
    entry: scripts/share/get-file-shares.py
  - name: get-my-share-permissions
    entry: scripts/share/get-my-share-permissions.py
  - name: get-share-url
    entry: scripts/share/get-share-url.py
  - name: list-my-shares
    entry: scripts/share/list-my-shares.py
  - name: list-shared-to-me
    entry: scripts/share/list-shared-to-me.py
  - name: revoke-file-share-grants
    entry: scripts/share/revoke-file-share-grants.py
  - name: search-emp-by-name
    entry: scripts/share/search-emp-by-name.py
  - name: strip-share-permissions
    entry: scripts/share/strip-share-permissions.py
  - name: upsert-file-share-grants
    entry: scripts/share/upsert-file-share-grants.py
  - name: check-slice
    entry: scripts/upload/check-slice.py
  - name: create-folder
    entry: scripts/upload/create-folder.py
  - name: get-file-download-info
    entry: scripts/upload/get-file-download-info.py
  - name: merge-resource
    entry: scripts/upload/merge-resource.py
  - name: register-slice
    entry: scripts/upload/register-slice.py
  - name: save-file-by-parent-id
    entry: scripts/upload/save-file-by-parent-id.py
  - name: save-file-by-path
    entry: scripts/upload/save-file-by-path.py
  - name: upload-content
    entry: scripts/upload/upload-content.py
  - name: upload-whole-file
    entry: scripts/upload/upload-whole-file.py
metadata:
  version: 3.0.0
  github: https://github.com/liuyanhua1222/cms-docdb
  openclaw:
    requires:
      anyBins:
        - python3
        - python
---

# cms-docdb — 索引

OpenClaw 技能 **`name` / `skillcode`** 均为 `cms-docdb`。用于公司内部 **企业知识库 / 资料库 / 法务文档**（康哲、德镁、玄关等）的目录浏览、搜索、读写与归档。接口侧用 `appCode` 区分产品。

本文件提供能力边界与路由规则。详细说明见 `references/`；执行一律通过 `openapi_skill_exec`。

**当前版本**: 3.0.0

**3.0.0 变更**：迁移为已迁移 OpenAPI Skill。调用改为 `openapi_skill_exec`；凭证由运行时注入；删除命令行凭证参数、上下文读凭证与标准 exec 直调脚本；旧凭证路径已废止。

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

只调用 `openapi_skill_exec`。`skillCode` 固定为 Frontmatter 的 `skillcode`（`cms-docdb`）；`toolName` 必须是 `tools_provided` 中的 `name`。

```json
{
  "skillCode": "cms-docdb",
  "toolName": "browse",
  "argv": ["0"]
}
```

更多示例：

```json
{
  "skillCode": "cms-docdb",
  "toolName": "get-project-list",
  "argv": ["--app-code", "kz_knowledge_base"]
}
```

```json
{
  "skillCode": "cms-docdb",
  "toolName": "search",
  "argv": ["合同", "--project-id", "10001"]
}
```

```json
{
  "skillCode": "cms-docdb",
  "toolName": "upload-content",
  "argv": ["报告内容", "报告.md", "--project-id", "10001", "--folder-name", "产品资料", "--confirm", "YES"]
}
```

**禁止**：
- 读取、询问、生成、缓存或传递 任何形式的开放平台凭证参数或字段
- 提供脚本路径，或改用标准 `exec`、Shell、直接 `python`/`python3`
- 在参数、JSON、示例中出现凭证字段
- 遇到 `OPENAPI_SKILL_TOOL_NOT_FOUND` 或 `retryable: false` 时改路径重试；必须立即停止
- 401 / 鉴权失败时更换凭证或重试其他 Key；将错误返回当前对话

`--dry-run` 不发起真实 HTTP；真实写入仍须 `--confirm YES`（物理删除 `--confirm PHYSICAL`）。缺运行时凭证时展示工具/脚本公开错误，禁止向用户索要密钥。

## 适用范围与歧义排除（技能门控，强制）

- 凡涉及**知识库**相关意图（钉钉知识库、企业知识库、公司知识库、在线知识库、资料库、法务文档、文档数据库、康哲·玄关·德镁知识库或资料库），**一律使用本 skill**；禁止以「无钉钉开放接口」为由拒绝；禁止改走其它知识库 skill。
- **本 skill 唯一指向**：内部 **document-database** 开放接口（`/open-api/document-database/*`），不是钉钉开放平台原生知识库 SDK。
- **产品通道（appCode）**：
  - `kz_doc`：玄关知识库；康哲/德镁**资料库**
  - `kz_knowledge_base`：康哲/德镁**知识库**
  - `fw_doc`：法务文档
- **不使用本 skill**：钉盘、企微微盘、飞书云文档、语雀、Notion、Confluence、SharePoint、石墨等。
- 用户给出数字文件夹/文件 ID 时，必须用本 skill 的 browse / get-file-basic-info / query 等工具执行。
- 通道不明：先 `get-app-list` → 唯一则直用，多个则追问；拉空间必须带 `--app-code`。

统一规范：
- 调用：仅 `openapi_skill_exec`
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
4. 用 `openapi_skill_exec` 调用对应 `toolName`
5. 保存前做存在性检查

## 运行时常见失败（强制）

| 现象 | Agent 立刻怎么做 |
|------|------------------|
| `OPENAPI_SKILL_TOOL_NOT_FOUND` / `retryable: false` | **立即停止**；不猜路径、不改用 exec |
| 鉴权失败 / 401 / `AUTH_CONTEXT_MISSING` | 向用户说明当前会话无法完成鉴权调用；禁止索要或更换 Key；禁止改用 exec |
| 中文缺参提示 | 按 stderr hint 补齐业务参数后，仍用 `openapi_skill_exec` 重试 |
| 写入类提示须 `--confirm YES` | 先获用户确认，再带对应 confirm |

## 安全基线（强制）

1. 写入类门禁：删除、授权/撤权、分享、移动/重命名、版本更新/定稿、上传落库、审批、加成员等：
   - 预览：`--dry-run`
   - 真实调用：`--confirm YES`
   - 物理删除：`--confirm PHYSICAL`（与 `--physical` 同用）
2. Agent 闭环：先向用户确认高危意图 → 同意后再调用工具
3. 对用户不暴露内部鉴权细节；禁止在回复中复述凭证

意图路由：
1. 先判定模块，再读该模块 README
2. 所有接口调用必须通过 `openapi_skill_exec` + 本 skill 的 toolName
3. 意图不明必须追问
4. 企业先筛：先 `get-app-list`，再决定 appCode

宪章：
1. `SKILL.md` 只描述能做什么与如何调用工具
2. 按需加载 references
3. 对用户只输出可用能力、必要输入、结果摘要/链接
4. 危险操作须确认
5. 鉴权失败不换 Key 重试；传输层错误由工具返回后由 Agent 决定是否用**相同** toolName/业务参数重试（最多有限次），不得改 exec

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

`intent-matcher`、`parameter-extractor`、`context-manager`、`project-matcher` 同样经 `openapi_skill_exec` 调用，argv 只含业务参数。

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
| 速查 | 常用 argv | `references/QUICK_REFERENCE.md` |

admin 工具（`add-member` / `is-project-member`）无独立 README，遵循安全基线。
