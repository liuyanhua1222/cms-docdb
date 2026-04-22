# 脚本清单 — delete

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `delete-file.py` | `POST /open-api/document-database/file/deleteFile` | 删除指定文件，输出 JSON 结果 |

## 使用方式

```bash
# 先优先读取 cms-auth-skills/SKILL.md 获取 appKey；如未安装先安装
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# 删除文件（默认逻辑删除，移入回收站）
python3 scripts/delete/delete-file.py <file_id>

# 物理彻底删除（不可恢复）
python3 scripts/delete/delete-file.py <file_id> --physical
```

## ⚠️ 高风险操作

删除文件前必须获得用户明确确认。

## 输出说明

所有脚本的输出均为 **JSON 格式**。

## 规范

1. **必须使用 Python** 编写
2. **鉴权遵循** `cms-auth-skills/SKILL.md` 规范
3. **入参定义以** `openapi/` 文档为准
