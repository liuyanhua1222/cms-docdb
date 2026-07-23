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

所有动作统一使用 `appKey` 鉴权，运行时从小龙虾上下文变量 `appkey` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/manage/update-file-name.py` | `POST .../updateFileName` | 同目录改名（同步 Open API） |
| `scripts/manage/move-file.py` | `POST .../moveFile` | 移动文件或文件夹；可选移动后改名 |
| `scripts/manage/update-file-property.py` | `POST .../updateFileProperty` | **已废弃**；兼容旧命令行，转发到上述两脚本 |
| `scripts/manage/update-file-version.py` | `POST /open-api/document-database/file/updateFileVersion` | 物理文件版本更新（绑定新资源产生新版本） |
| `scripts/manage/get-version-list.py` | `GET /open-api/document-database/file/getVersionList` | 获取文件完整版本历史列表 |
| `scripts/manage/get-last-version.py` | `GET /open-api/document-database/file/getLastVersion` | 获取文件最新版本信息 |
| `scripts/manage/finalize-version.py` | `POST /open-api/document-database/file/finalizeVersion` | 将指定版本标记为定稿 |

纯文本内容的版本更新使用 `scripts/upload/upload-content.py --update-file-id`。运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 同目录改名 | fileId, newName | projectId, nameConflictStrategy, rootFileId |
| 移动节点 | fileId, targetParentId | newName, projectId, nameConflictStrategy, rootFileId |
| 纯文本版本更新 | updateFileId, content, fileName | fileSuffix, versionName, versionRemark |
| 物理文件版本更新 | id, projectId, resourceId | versionStatus, versionName, versionRemark, suffix, size |
| 查看版本历史 | fileId | — |
| 获取最新版本 | fileId | — |
| 版本定稿 | fileId | versionNumber |

## 参数详细说明

### update-file-name.py — 同目录改名

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件或文件夹 ID | 有效 ID | - |
| `--new-name` | String | 是 | 新名称 | 建议带扩展名 | - |
| `--project-id` | Long | 否 | 空间 ID | 有效 projectId | - |
| `--name-conflict-strategy` | Integer | 否 | 同名策略 | `0`=自动重命名，`1`=失败（默认） | - |
| `--root-file-id` | Long | 否 | 映射根 | 与同步 state 根一致 | 用于响应 `relativePath` |

### move-file.py — 移动节点

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 被移动节点 ID | 有效 ID | - |
| `--target-parent-id` | Long | 是 | 目标父目录 ID | 有效文件夹 ID | - |
| `--new-name` | String | 否 | 移动后名称 | 省略则保留原名 | 单次调用内完成 move+rename |
| `--project-id` | Long | 否 | 目标空间 ID | - | - |
| `--name-conflict-strategy` | Integer | 否 | 同名策略 | `0`/`1`/`2`（默认）/`3` | 默认 `2`=失败 |
| `--root-file-id` | Long | 否 | 映射根 | - | 用于响应 `relativePath` |

### update-file-property.py — [已废弃] 兼容转发

| 参数 | 说明 |
|------|------|
| `--new-name` / `--target-parent-id` | 转发到 `update-file-name.py` 或 `move-file.py` |
| `--cover` | 映射为 move 的 `nameConflictStrategy=1`（覆盖） |
| `--auto-rename` | rename 用 `0`，move 用 `0`；否则 rename 默认 `1`、move 默认 `2` |

直接调用 Open API 时 **勿再使用** `updateFileProperty`（返回 400）。

## 动作列表

### 1. 同目录改名
- **脚本**: `update-file-name.py`
- **用途**: 仅改名称，不换父目录
- **输出**: 富响应 `data`（fileId、type、name、parentId、updateTime 等）

### 2. 移动节点
- **脚本**: `move-file.py`
- **用途**: 换父目录；可选 `--new-name` 在移动后改名
- **输出**: 富响应；`idChanged=true` 时关注 `idMappings`

### 3. 纯文本版本更新
- **脚本**: `upload-content.py`（位于 scripts/upload/）
- **用途**: 将新的纯文本内容保存为已有文件的新版本
- **输出**: 返回 `{ fileId, fileName }`

### 4. 物理文件版本更新
- **脚本**: `update-file-version.py`
- **用途**: 将新上传的物理文件资源绑定到已有文件
- **输出**: 返回文件 ID

**projectId 自动补全（v2.5）**：
- **默认行为**: 脚本默认不传 `--project-id` 参数，docdb 自动从文件 ID 反查
- **显式传入**: 仅在需要覆盖或调试时传入
- **失败处理**: 反查失败时 docdb 抛异常，脚本返回错误信息

**示例**：
```bash
# 推荐：省略 projectId（v2.5 自动补全）
python3 -B <skill-dir>/scripts/manage/update-file-version.py --file-id 12345 --resource-id 987654321 --version-status 3 --version-name "V2.0" --version-remark "修正了第三章内容" --confirm YES

# 旧方式（仍然支持，但非必需）
python3 -B <skill-dir>/scripts/manage/update-file-version.py --file-id 12345 --project-id 2025001 --resource-id 987654321 --confirm YES
```

### 5–7. 版本历史 / 最新版本 / 定稿
- 见原 `get-version-list.py`、`get-last-version.py`、`finalize-version.py`

## 输出说明

重命名/移动脚本输出统一为 JSON：
- `resultCode`: 1 表示成功
- `resultMsg`: 错误信息
- `data`: 富 VO（非 Boolean）

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

| 场景 | 脚本 | 参数 |
|---|---|---|
| 改名冲突自动后缀 | `update-file-name.py` | `--name-conflict-strategy 0` |
| 改名冲突失败 | `update-file-name.py` | 默认 `1` |
| 移动冲突覆盖 | `move-file.py` | `--name-conflict-strategy 1` |
| 移动冲突失败 | `move-file.py` | 默认 `2` |

> 现网自动重命名后缀为 `_1` 等形式，与文档 `(1)` 表述可能不一致。

## 运行方式速查

**重要说明**：以下示例使用相对路径以便阅读，实际执行时必须替换为绝对路径。例如：
- 文档示例：`python3 -B <skill-dir>/scripts/manage/update-file-name.py <file_id>`
- 实际执行：`python3 -B <skill-dir>/scripts/manage/update-file-name.py <file_id>`（将 `<skill-dir>` 换成 skill 根目录绝对路径）

禁止使用 `cd`、`&&`、管道等 shell 构造。每个脚本必须在单独的命令中使用绝对路径执行。

```bash
# 推荐：新接口（写入须 --confirm YES；可先 --dry-run）
python3 -B <skill-dir>/scripts/manage/update-file-name.py <file_id> --new-name "B.md" --confirm YES [--project-id <pid>]
python3 -B <skill-dir>/scripts/manage/move-file.py <file_id> --target-parent-id <parent_id> --confirm YES [--new-name "X.md"]

# 兼容：旧命令（stderr 警告后转发；须带 --confirm YES）
python3 -B <skill-dir>/scripts/manage/update-file-property.py <file_id> --new-name "新文件名.pdf" --confirm YES
python3 -B <skill-dir>/scripts/manage/update-file-property.py <file_id> --target-parent-id <parent_id> --cover --confirm YES

python3 -B <skill-dir>/scripts/manage/update-file-version.py <file_id> <project_id> <resource_id> --version-status 3 --confirm YES
python3 -B <skill-dir>/scripts/manage/get-version-list.py <file_id>
python3 -B <skill-dir>/scripts/manage/finalize-version.py <file_id> --confirm YES
```
