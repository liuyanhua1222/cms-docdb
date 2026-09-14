# P2-02～08 对账关闭清单

日期：2026-09-14 · Wave7  
对照：审计 v1.1 / 挂账第三批

原则：每条「现状 → 关闭证据」；全部勾选后挂账改「已关」。

| ID | 主题 | 现状（Skill 3.4.2） | 关闭证据 |
|---|---|---|---|
| P2-02 | search projectId 可选 | `scripts/query/search.py` 支持可选 projectId；README 已写 | □ --help + dry 文档一致 |
| P2-03 | browse / 根目录规则 | `browse.py` / `get-level1-folders.py`；SKILL 禁 browse parentId=0 | □ |
| P2-04 | preview 路径说明 | references 已说明自渲染/KB 预览 | □ |
| P2-05 | 分页参数 | 各 list 脚本 pageIndex/pageSize | □ |
| P2-06 | 枚举单一来源 | `references/enums-and-defaults.md` | □ |
| P2-07 | dry-run 扫描 | 写脚本 + safety；pytest help/dry 覆盖 | □ pytest 全绿 |
| P2-08 | 下载分块/文档 | `download-file.py` 1MB chunk；batch-download 受控并发 | □ |

P2-01（listDescendant/listChanges/batchGetMeta）：**本波已补脚本**，关单条件改为带 AppKey 联调一次即可。
