# 脚本清单 — upload

## 鉴权前置条件

- **鉴权模式**：`appKey`
- **环境变量**：`XG_BIZ_API_KEY` 或 `XG_APP_KEY`
- **获取方式**：通过 `cms-auth-skills` 获取并设置环境变量

## 共享依赖

无

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `upload-content.py` | `POST /open-api/document-database/file/uploadContent` | 一键保存纯文本到个人知识库 |
| `save-file-by-path.py` | `POST /open-api/document-database/file/saveFileByPath` | 按逻辑路径保存物理文件到项目空间 |
| `save-file-by-parent-id.py` | `POST /open-api/document-database/file/saveFileByParentId` | 已知父目录 ID 时保存物理文件 |
| `upload-whole-file.py` | `POST /open-api/cwork-file/uploadWholeFile` | 小文件整传（≤20MB），返回 resourceId |
| `check-slice.py` | `GET /open-api/document-database/file/getSliceIdByMd5V2` | 大文件分片预检，支持秒传判定 |
| `register-slice.py` | `POST /open-api/document-database/file/uploadFileSliceV2` | 注册分片元信息，换取 sliceId |
| `merge-resource.py` | `POST /open-api/document-database/file/saveResource` | 合并分片生成最终 resourceId |
| `get-file-download-info.py` | `GET /open-api/cwork-file/getDownloadInfo` | 根据 resourceId 获取下载 URL（有效期 1 小时） |

## 运行方式

> **提示**：系统会自动检测 Python 命令，优先使用 `python3`，如不存在则使用 `python`

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"

# === 纯文本上传（AI 内容入库首选）===
# 必填：内容、文件名
python scripts/upload/upload-content.py "内容" "文件名.md" [--file-suffix md] [--folder-name "AI生成/周报"]

# === 物理文件上传 ===
# 小文件（≤20MB）
# 必填：file_path
python scripts/upload/upload-whole-file.py <file_path>
#   → 获得 resourceId

# 大文件（>20MB）
# 必填：md5
python scripts/upload/check-slice.py <md5> [--size <size>] [--suffix <suffix>]
#   → 秒传命中用 sliceId；未命中需 PUT 上传
# 必填：full_path、md5、size、storage_type
python scripts/upload/register-slice.py <full_path> <md5> <size> MINIO
# 必填：文件名、slice_ids
python scripts/upload/merge-resource.py "文件名.pdf" "sliceId1,sliceId2,..." [--suffix pdf] [--size <size>]
#   → 获得 resourceId

# === 绑定到知识库 ===
# 已知父目录 ID（推荐，跳过路径解析）
# 必填：project_id、parent_id、resource_id、文件名
python scripts/upload/save-file-by-parent-id.py <project_id> <parent_id> <resource_id> "文件名.pdf" [--suffix pdf]

# 按逻辑路径（路径不存在自动创建）
# 必填：project_id、文件名、resource_id
python scripts/upload/save-file-by-path.py <project_id> "文件名.pdf" <resource_id> [--path "目录"] [--suffix pdf]

# === 获取下载链接 ===
# 必填：resource_id
python scripts/upload/get-file-download-info.py <resource_id>
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
