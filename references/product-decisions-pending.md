# 待产品确认清单（Skill 侧跟踪）

日期：2026-09-14 · 对齐 Wave6 全量清零  
原则：**产品未拍板前，Skill 不得伪造默认业务结论或伪造成功路径。**

| 项 | 现状 | 待确认问题 | 拍板后动作 |
|---|---|---|---|
| grant 默认话术 | 脚本**强制**显式 `--permissions`；不做隐式 `read,preview` | 目录授权是否与协同分享一样，对外默认「查看列表+在线预览」？ | 若确认默认：改 upsert 缺省值与 README 话术；若否：维持显式 |
| P1-09 有效权限矩阵 | 草案见 `effective-permission-matrix.md` 顶部选择题 | 成员 / grant / share / 继承叠加规则 | 固化矩阵 + 验收用例 |
| P1-16 OutSend | OpenAPI 未开放；`outsend-status.py` 固定 blocked + exit 2 | 创建外发 / 白名单 / 查询 / 撤销是否纳入 OpenAPI | 按 `outsend/README.md` 最小能力清单立项封装 |
| BP §六 四项业务关单 | 台账仍「未关」 | 3 PDF / 13↔37 / RUN-01·02 / 一二级引用开放 | 业务+欧倩关单；技术侧只跟踪，不代替业务验收 |

相关入口：

- 验收：`acceptance-runbook.md`
- OutSend：`outsend/README.md`
- 矩阵：`effective-permission-matrix.md`
- 目录授权：`grant/README.md`
