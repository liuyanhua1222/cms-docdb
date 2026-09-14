# B-01～B-04 Skill 侧交付说明

对齐 `docdb/docs/cms-docdb-p0-B线与BP跟踪_2026-09-14.md`。

| ID | Skill 已做 | 仍依赖 |
|---|---|---|
| B-01 | `docdb_open_api.py` 区分 AUTH_CONTEXT_MISSING / INVALID / REDACTED；401 不换 Key 重试 | 登录过期 vs 无空间权限服务端文案分层（成伟） |
| B-02 | multipart/stdlib 客户端拒绝**跨源** 301/302/307/308（防带 AppKey 跟跳） | 正式同源上传入口或预签名（成伟网关） |
| B-03 | `scripts/query/batch-download-files.py` 默认并发 2，建议硬顶 8 | 正式并发上限契约数字 |
| B-04 | `upload-content.py` 默认 7500 字符软预检；`--skip-content-limit-check` / `CMS_DOCDB_CONTENT_SOFT_LIMIT` | 正式单篇上限契约 + 10/30/75KB 回读验收 |

升级：连续 3 工作日无进展 → 见 B 线跟踪文档 §3。
