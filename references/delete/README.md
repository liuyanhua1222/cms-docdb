# delete — 模块说明

## 适用场景

- 用户说"帮我把 xxx 文件删了"、"删除这个文件"
- 用户明确要求移除某个文件

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，运行时从小龙虾上下文变量 `appkey` 获取。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/delete/delete-file.py` | `POST /open-api/document-database/file/deleteFile` | 删除指定文件，输出 JSON 结果 |

运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 删除文件 | fileId | physical |

## 参数详细说明

### delete-file.py — 删除文件

| 参数 | 类型 | 必填 | 用途 | 取值范围/枚举 | 依赖关系 |
|------|------|------|------|---------------|----------|
| `file_id` | Long | 是 | 文件 ID | 有效文件 ID | - |
| `--physical` | Boolean | 否 | 物理彻底删除（不可恢复） | 无值标志，存在即为 true | - |
| `--dry-run` | Flag | 否 | 仅打印拟发请求 JSON，不发 HTTP | - | 无需 appkey |
| `--confirm` | String | 条件 | 真实调用必填 | 逻辑删除=`YES`；物理删除=`PHYSICAL` | 与 `--physical` 联动 |

## 动作列表

### 1. 删除文件
- **脚本**: `delete-file.py`
- **用途**: 删除指定文件，支持逻辑删除（移入回收站）或物理彻底删除
- **⚠️ 高风险操作**：执行前必须获得用户明确确认，并传入 `--confirm`
- **输出**: 返回 Boolean，表示操作是否成功

## 输出说明

所有脚本输出统一为 JSON 格式，包含：
- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: true 表示删除成功

## 删除模式

| 模式 | 参数 | 说明 |
|---|---|---|
| 逻辑删除（默认） | 不传 isPhysical | 文件移入回收站，可从回收站恢复 |
| 物理彻底删除 | `--physical` | 从回收站彻底抹除，**不可恢复** |

## 危险操作确认流程

1. **先向用户确认**："确认要删除文件 [文件名] 吗？此操作[可/不可]撤销。"
2. 用户明确确认后，调用 `delete-file.py` 并带上 `--confirm YES`（物理删除用 `--confirm PHYSICAL`）
3. 可选先 `--dry-run` 预览拟发请求
4. 返回删除结果

## 用户话术示例

- "帮我把这份文档删了"
- "删除周报 xxx"
- "彻底删除这个文件"

## 运行方式速查

**重要说明**：以下示例使用相对路径以便阅读,实际执行时必须替换为绝对路径。例如：
- 文档示例：`python3 -B <skill-dir>/scripts/delete/delete-file.py <file_id>`
- 实际执行：`python3 -B <skill-dir>/scripts/delete/delete-file.py <file_id>`（将 `<skill-dir>` 换成 skill 根目录绝对路径）

禁止使用 `cd`、`&&`、管道等 shell 构造。每个脚本必须在单独的命令中使用绝对路径执行。

```bash
python3 -B <skill-dir>/scripts/delete/delete-file.py <file_id> --dry-run
python3 -B <skill-dir>/scripts/delete/delete-file.py <file_id> --confirm YES
python3 -B <skill-dir>/scripts/delete/delete-file.py <file_id> --physical --confirm PHYSICAL
```
