# Changelog

All notable changes to this skill will be documented in this file.

## [1.1.3] - 2026-05-14

### Changed
- **[规范修正]** 统一命名：将 `name` 从 `cms-docdb-knowledge-base` 改为 `cms-docdb`，与 `skillcode` 和目录名保持完全一致
- **[规范修正]** 明确日志路径：在统一规范中明确声明运行日志路径为 `.cms-log/log/cms-docdb/`
- **[规范修正]** 明确状态路径：在统一规范中明确声明运行时状态路径为 `.cms-log/state/cms-docdb/`
- **[文档优化]** 简化索引章节标题和说明，移除冗余的命名解释

### Fixed
- 修复 YAML 头中 description 字段末尾多余的引号

### Documentation
- 添加 `SKILL_CHECK_REPORT.md`：完整的规范检查报告
- 添加 `CHANGELOG.md`：版本变更记录

## [1.1.2] - 之前版本

### Features
- 完整的 5 个模块能力：browse、query、upload、delete、manage
- 版本管理强制规则
- 完整的鉴权依赖和安全规范
- Windows PowerShell 兼容性支持
- 意图识别和上下文管理
