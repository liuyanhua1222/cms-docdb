# 脚本清单 — manage

## 共享依赖

无

## 鉴权前置条件

所有脚本统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取：

```bash
export XG_BIZ_API_KEY="your-app-key"
# 或
export XG_APP_KEY="your-app-key"
```

## 脚本列表

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `update-file-property.py` | `POST /open-api/document-database/file/updateFileProperty` | 更新文件属性（重命名/移动） |
| `update-file-version.py` | `POST /open-api/document-database/file/updateFileVersion` | 物理文件版本更新（绑定新资源产生新版本） |
| `get-version-list.py` | `GET /open-api/document-database/file/getVersionList` | 获取文件完整版本历史列表 |
| `get-last-version.py` | `GET /open-api/document-database/file/getLastVersion` | 获取文件最新版本信息 |
| `finalize-version.py` | `POST /open-api/document-database/file/finalizeVersion` | 将指定版本标记为定稿 |

## 使用方式

```bash
# === 重命名/移动 ===
python3 scripts/manage/update-file-property.py <file_id> --new-name "新文件名.pdf"
python3 scripts/manage/update-file-property.py <file_id> --target-parent-id <parent_id>
python3 scripts/manage/update-file-property.py <file_id> --new-name "同名文件.pdf" --auto-rename

# === 物理文件版本更新 ===
# versionStatus: 1=覆盖草稿, 2=强制新建, 3=新建并立即定稿（推荐）
python3 scripts/manage/update-file-version.py <file_id> <project_id> <resource_id> \
  --version-status 3 --version-name "V2.0" --version-remark "修订内容"

# === 查看版本历史 ===
python3 scripts/manage/get-version-list.py <file_id>

# === 获取最新版本 ===
python3 scripts/manage/get-last-version.py <file_id>

# === 版本定稿 ===
# 定稿最新版本
python3 scripts/manage/finalize-version.py <file_id>
# 定稿指定版本号
python3 scripts/manage/finalize-version.py <file_id> --version-number 3
```

## 返回说明

所有脚本输出均为 JSON 格式：
- `resultCode`: 1 成功，非 1 失败
- `resultMsg`: 错误信息（成功时为 null）
- `data`: 业务数据

版本对象关键字段：`versionNumber`、`versionName`、`status`（1草稿/2定稿）、`remark`、`creator`、`lastVersion`

## ⚠️ 注意事项

- 重命名/移动文件前应确认用户意图
- 纯文本内容的版本更新请使用 `scripts/upload/upload-content.py`（传 `--update-file-id`）
- 物理文件版本更新推荐使用 `--version-status 3`（新建并立即定稿）
