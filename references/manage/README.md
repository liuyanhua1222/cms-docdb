# manage — 模块说明

## 适用场景

- 用户说"帮我把 xxx 文件重命名"、"把这个文件改个名字"
- 用户说"帮我把 xxx 文件移到 yyy 文件夹"
- 用户说"更新一下知识库里的 xxx"、"把最新内容存进去"（已有文件的内容更新）
- 用户说"查看 xxx 文件的历史版本"、"把这个版本定稿"

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 重命名/移动文件 | fileId | newName, targetParentId, cover, autoRename |
| 纯文本版本更新 | updateFileId, content, fileName | fileSuffix, versionName, versionRemark |
| 物理文件版本更新 | id, projectId, resourceId | versionStatus, versionName, versionRemark, suffix, size |
| 查看版本历史 | fileId | — |
| 获取最新版本 | fileId | — |
| 版本定稿 | fileId | versionNumber |

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
