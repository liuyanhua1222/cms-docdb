# browse — 使用说明

## 什么时候使用

- 用户说"帮我看看知识库里有什么"、"列出我的空间"
- 用户想浏览某个目录下的内容
- 用户想了解可以访问哪些空间

## 标准流程

1. 鉴权预检（按 `cms-auth-skills/SKILL.md` 获取 appKey）
2. 获取个人空间 ID（`get-personal-project-id`）或列出所有可用空间（`get-project-list`）
3. 浏览目录内容：
   - 根目录：用 `get-level1-folders` 拉取项目顶层内容
   - 子目录：用 `browse` 翻页浏览指定目录的直属子项
4. 如有子目录，用户可继续下钻

## 空间发现

| 场景 | 调用的接口 |
|---|---|
| 快速获取个人知识库 ID | `get-personal-project-id` |
| 查看所有可访问空间 | `get-project-list` |
| 查看有上传权限的空间（保存文件前） | `get-uploadable-list` |

## 用户话术示例

- "帮我看看个人知识库里有什么"
- "浏览一下根目录"
- "查看 AI 研发中心这个空间"
