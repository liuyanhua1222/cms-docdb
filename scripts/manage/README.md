# 脚本清单 — manage

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `update-file-property.py` | `POST /open-api/document-database/file/updateFileProperty` | 更新文件属性（重命名/移动） |

## 使用方式

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# 重命名文件
python3 scripts/manage/update-file-property.py <file_id> --new-name "新文件名.pdf"

# 移动文件到指定目录
python3 scripts/manage/update-file-property.py <file_id> --target-parent-id <parent_id>

# 移动并重命名
python3 scripts/manage/update-file-property.py <file_id> --new-name "新文件名.pdf" --target-parent-id <parent_id>

# 同名冲突策略
python3 scripts/manage/update-file-property.py <file_id> --new-name "同名文件.pdf" --auto-rename
# 或
python3 scripts/manage/update-file-property.py <file_id> --new-name "同名文件.pdf" --cover
```

## ⚠️ 高风险操作

移动/重命名文件前应确认用户意图。

## 输出说明

所有脚本的输出均为 **JSON 格式**。

## 规范

1. **必须使用 Python** 编写
2. **鉴权遵循** `cms-auth-skills/SKILL.md` 规范
3. **入参定义以** `openapi/` 文档为准
