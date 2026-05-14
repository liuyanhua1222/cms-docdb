# 脚本清单 — browse

## 鉴权前置条件

- **鉴权模式**：`appKey`
- **环境变量**：`XG_BIZ_API_KEY` 或 `XG_APP_KEY`
- **获取方式**：通过 `cms-auth-skills` 获取并设置环境变量

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `get-project-list.py` | `GET /open-api/document-database/project/list` | 获取有权限访问的所有空间列表 |
| `get-personal-project-id.py` | `GET /open-api/document-database/project/personal/getProjectId` | 获取当前用户的个人知识库空间 ID |
| `get-uploadable-list.py` | `GET /open-api/document-database/project/uploadableList` | 获取有上传/编辑权限的空间列表 |
| `get-level1-folders.py` | `GET /open-api/document-database/file/getLevel1Folders` | 拉取项目空间根目录下的所有内容 |
| `browse.py` | `GET /open-api/document-database/file/getChildFiles` | 浏览指定目录下的直接子项 |
| `get-recent-files.py` | `POST /open-api/document-database/project/personal/getRecentFiles` | 获取当前用户最近上传的文件列表 |

## 运行方式

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# 发现可用空间
python3 scripts/browse/get-project-list.py
python3 scripts/browse/get-personal-project-id.py
python3 scripts/browse/get-uploadable-list.py

# 浏览项目根目录
python3 scripts/browse/get-level1-folders.py <project_id>

# 浏览指定目录（parentId = 0 为绝对根目录）
python3 scripts/browse/browse.py <parent_id> [--type 1|2] [--order 1-6]

# 最近上传文件
python3 scripts/browse/get-recent-files.py [--limit 10] [--search-key "关键词"]
```

## 返回说明

所有脚本的输出均为 **JSON 格式**，包含以下字段：

- `resultCode`: 1 表示成功，非 1 表示失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据（具体结构见各脚本文档）

## 规范

1. **必须使用 Python** 编写
2. **鉴权遵循** `cms-auth-skills/SKILL.md` 规范
3. **入参定义以** `openapi/` 文档为准
