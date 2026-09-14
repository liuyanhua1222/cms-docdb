# 枚举与默认值单一来源（对齐 docdb MoveConflictStrategy）

## nameConflictStrategy（移动 / 同名冲突）

与后端 `com.xgjktech.document.enums.MoveConflictStrategy` 一致：

| 值 | 名称 | 行为 |
|---|---|---|
| 0 | RENAME | 自动重命名后移动 |
| 1 | COVER | 覆盖目标（fileId 可能变化） |
| 2 | ERROR | 遇冲突抛错，不移动 |
| 3 | SKIP | 跳过冲突节点（子树语义见服务端） |

**Skill `move-file.py` 默认 = 2（ERROR）**：对 Agent 更安全，避免静默覆盖/跳过。  
若请求体省略且走服务端 `MoveConflictStrategy.of(null)`，后端会回落到 **RENAME(0)**——故 Skill **必须显式传** `nameConflictStrategy`（已默认 2）。

## versionStatus（物理版本）

- Skill `update-file-version.py` **默认 3（定稿）**——2026-09-14 产品确认，不改为 2。

## 分享 dueDate

- 默认 `20991231`（永久）——2026-09-14 产品确认。

## 第三方文件类型

- 脚本与文档统一使用 `huiji`（慧记）；勿写 `huij`。
