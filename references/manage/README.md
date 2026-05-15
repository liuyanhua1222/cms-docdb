# manage — 模块说明

## 目录

- 适用场景
- 鉴权模式
- 脚本清单
- 输入要求
- 参数详细说明
- 动作列表
- 输出说明
- 版本更新决策流程
- 冲突处理
- 运行方式速查

## 适用场景

- 用户说"帮我把 xxx 文件重命名"、"把这个文件改个名字"
- 用户说"帮我把 xxx 文件移到 yyy 文件夹"
- 用户说"更新一下知识库里的 xxx"、"把最新内容存进去"（已有文件的内容更新）
- 用户说"查看 xxx 文件的历史版本"、"把这个版本定稿"

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/manage/update-file-property.py` | `POST /open-api/document-database/file/updateFileProperty` | 更新文件属性（重命名/移动） |
| `scripts/manage/update-file-version.py` | `POST /open-api/document-database/file/updateFileVersion` | 物理文件版本更新（绑定新资源产生新版本） |
| `scripts/manage/get-version-list.py` | `GET /open-api/document-database/file/getVersionList` | 获取文件完整版本历史列表 |
| `scripts/manage/get-last-version.py` | `GET /open-api/document-database/file/getLastVersion` | 获取文件最新版本信息 |
| `scripts/manage/finalize-version.py` | `POST /open-api/document-database/file/finalizeVersion` | 将指定版本标记为定稿 |

纯文本内容的版本更新使用 `scripts/upload/upload-content.py --update-file-id`。运行前先按 `cms-auth-skills/SKILL.md` 设置 `XG_BIZ_API_KEY` 或 `XG_APP_KEY`。系统会自动检测 Python 命令，优先使用 `python3`，如不存在则使用 `python`。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 重命名/移动文件 | fileId | newName, targetParentId, cover, autoRename |
| 纯文本版本更新 | updateFileId, content, fileName | fileSuffix, versionName, versionRemark |
| 物理文件版本更新 | id, projectId, resourceId | versionStatus, versionName, versionRemark, suffix, size |
| 查看版本历史 | fileId | — |
| 获取最新版本 | fileId | — |
| 版本定稿 | fileId | versionNumber |

## 参数详细说明

### update-file-property.py — 重命名/移动文件

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--new-name` | String | 否 | 新文件名 | 任意文件名，建议带扩展名 | 与 --target-parent-id 至少传一个 |
| `--target-parent-id` | Long | 否 | 目标父目录 ID | 有效文件夹 ID | 与 --new-name 至少传一个 |
| `--cover` | Boolean | 否 | 同名冲突时覆盖 | 无值标志，存在即为 true | 与 --auto-rename 互斥 |
| `--auto-rename` | Boolean | 否 | 同名冲突时自动重命名 | 无值标志，存在即为 true，自动追加数字后缀如 `(1)` | 与 --cover 互斥 |

### upload-content.py — 纯文本版本更新

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `content` | String | 是 | 新的文件内容 | 任意文本内容 | - |
| `file_name` | String | 是 | 文件名 | 建议带扩展名 | - |
| `--update-file-id` | Long | 是 | 目标文件 ID | 有效文件 ID（触发版本更新模式） | - |
| `--file-suffix` | String | 否 | 文件后缀 | 枚举：`md`、`html`、`txt`、`json` | - |
| `--version-name` | String | 否 | 版本名称 | 如 `V2.0` | - |
| `--version-remark` | String | 否 | 版本说明 | 任意文本 | - |

### update-file-version.py — 物理文件版本更新

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 要更新的文件 ID | 有效文件 ID | - |
| `project_id` | Long | 是 | 文件所在空间 ID | 有效项目 ID | - |
| `resource_id` | Long | 是 | 新上传的物理资源 ID | 通过 upload-whole-file.py 或 merge-resource.py 获取 | - |
| `--name` | String | 否 | 文件名 | 不传则保持原文件名 | - |
| `--version-status` | Integer | 否 | 版本行为 | 枚举：`1`（覆盖草稿）、`2`（强制新建）、`3`（新建并立即定稿，默认） | - |
| `--version-name` | String | 否 | 版本名称 | 如 `V2.0` | - |
| `--version-remark` | String | 否 | 版本说明 | 任意文本 | - |
| `--suffix` | String | 否 | 文件后缀 | 如 `pdf`、`docx` | - |
| `--size` | Long | 否 | 文件大小（字节） | 文件实际大小 | - |

### get-version-list.py — 查看版本历史

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |

### get-last-version.py — 获取最新版本信息

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |

### finalize-version.py — 版本定稿

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--version-number` | Integer | 否 | 指定版本号 | 有效版本号（可通过 get-version-list.py 获取） | 不传则定稿最新版本 |

## 动作列表

### 1. 重命名/移动文件
- **脚本**: `update-file-property.py`
- **用途**: 更新文件属性，支持重命名和跨目录移动
- **输出**: 返回 Boolean，表示操作是否成功

### 2. 纯文本版本更新
- **脚本**: `upload-content.py`（位于 scripts/upload/，通过 updateFileId 参数触发版本更新模式）
- **用途**: 将新的纯文本内容保存为已有文件的新版本，适合 AI 生成内容的迭代更新
- **注意**: 传入 updateFileId 时自动切换为版本更新模式，folderName 参数无效
- **输出**: 返回 `{ fileId, fileName }`（精简结果，不含 projectId/folderId/downloadUrl）

### 3. 物理文件版本更新
- **脚本**: `update-file-version.py`
- **用途**: 将新上传的物理文件资源绑定到已有文件，产生新版本记录
- **versionStatus 说明**: 1=覆盖当前草稿，2=强制新建版本，3=新建并立即定稿（推荐默认）
- **输出**: 返回文件 ID

### 4. 查看版本历史
- **脚本**: `get-version-list.py`
- **用途**: 获取指定文件的完整版本历史列表
- **输出**: 返回版本列表，每个版本包含 versionNumber、versionName、status、remark、creator、createTime、lastVersion

### 5. 获取最新版本信息
- **脚本**: `get-last-version.py`
- **用途**: 快速获取文件当前最新版本的详细信息
- **输出**: 返回单个版本对象

### 6. 版本定稿
- **脚本**: `finalize-version.py`
- **用途**: 将文件的某个版本标记为正式定稿状态（status 从 1 变为 2）
- **注意**: 不传 versionNumber 则定稿最新版本；定稿后再次更新会自动创建新版本
- **输出**: 返回 Boolean，表示操作是否成功

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

版本对象字段：
- `id`: 版本记录 ID
- `fileId`: 文件 ID
- `versionNumber`: 版本号（从 1 开始递增）
- `versionName`: 版本名称（如 V2.0）
- `status`: 1=未定稿（草稿），2=已定稿
- `remark`: 版本说明
- `creator`: 创建人姓名
- `createTime`: 创建时间戳
- `lastVersion`: 是否为最新版本

## 版本更新决策流程（强制）

```
用户发起保存/上传请求
  → 通过 searchFile 或 getChildFiles 检查目标文件是否已存在
    → 不存在：路由到 upload 模块走新建流程
    → 已存在：
        → 纯文本内容：upload-content.py（传 updateFileId）
        → 物理文件：update-file-version.py
        → 禁止：新建同名文件 / 直接覆盖已有文件
```

## 冲突处理（重命名/移动）

同名冲突时有三种策略：

| 策略 | 参数 | 说明 |
|---|---|---|
| 静默覆盖 | cover=true | 直接覆盖已有文件 |
| 自动重命名 | autoRename=true | 自动追加数字后缀，如 `文件名(1).pdf` |
| 报错 | 二者都不传 | 后端报错，Agent 需处理 |

## 用户话术示例

- "帮我把这份文档改个名"
- "把这个文件移到 AI 生成文件夹"
- "更新一下知识库里的那个报告"
- "这个文件改了，保留旧的，存成新版本"
- "查看这个文件有几个版本"
- "把最新版本定稿"

## 运行方式速查

```bash
python scripts/manage/update-file-property.py <file_id> --new-name "新文件名.pdf"
python scripts/manage/update-file-property.py <file_id> --target-parent-id <parent_id>
python scripts/manage/update-file-property.py <file_id> --new-name "同名文件.pdf" --auto-rename
python scripts/manage/update-file-property.py <file_id> --target-parent-id <parent_id> --cover
python scripts/manage/update-file-version.py <file_id> <project_id> <resource_id> [--name "新文件名.pdf"] --version-status 3 --version-name "V2.0" --version-remark "修订内容"
python scripts/manage/get-version-list.py <file_id>
python scripts/manage/get-last-version.py <file_id>
python scripts/manage/finalize-version.py <file_id>
python scripts/manage/finalize-version.py <file_id> --version-number 3
```
