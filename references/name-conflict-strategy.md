# 名称冲突策略分轨（3.4.3）

| 入口 | 省略 `nameConflictStrategy` | 显式 0/1/2 | 显式 3 |
|---|---|---|---|
| 正文 uploadContent（后端历史） | 约等于覆盖（`null`/`1`→更新旧文件） | 0 改名 / 1 覆盖 / 2 失败 | 报错 |
| 新建 resolveCreateNameConflict（后端历史） | 约等于改名（`null`/`0`） | 同上 | 报错 |
| 移动 move | 服务端另有默认；Skill CLI 默认显式 2 | 0/1/2 + **3=合并子树删源** | 仅移动 |
| **Skill CLI upload-content / save-file-*** | **始终下发，默认 2（失败）** | 0/1/2 | **拒绝**（不套用移动语义） |

安全责任：旧 OpenAPI 客户端兼容靠后端历史省略；Agent/Skill 靠显式默认失败，避免静默覆盖。
