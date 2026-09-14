# outsend — 外部协作外发（P1-16 · 待产品）

> **当前状态：OpenAPI 未开放。禁止伪造成功。**

后台（document-database）侧已有外发相关能力，但 **OpenAPI 未对 Skill/Agent 封装路由**。在产品确认范围与契约之前：

| 允许 | 禁止 |
|---|---|
| 告知用户「外发能力待产品定范围，暂不可用」 | 伪造 `resultCode=1` / 假装已创建外发任务 |
| 调用 `scripts/outsend/outsend-status.py` 取得明确 blocked 信号 | 用 share/grant/upload 冒充「外发」闭环 |
| 记录产品确认结论后再立项封装 | 猜测参数自行调未文档化后台接口 |

## 脚本

| 脚本 | 行为 |
|---|---|
| `scripts/outsend/outsend-status.py` | 打印 blocked JSON，**exit 2**（非成功） |

输出固定为：

```json
{
  "resultCode": 0,
  "resultMsg": "OutSend OpenAPI 未开放，待产品确认范围",
  "data": {"status": "blocked_pending_product"}
}
```

说明：`resultCode=0` **不是**业务成功（知识库成功一般为 `1`）；配合 exit 2 防止 Agent 误判。

## 待产品确认的最小能力清单（占位）

产品拍板前不下沉实现。请确认是否纳入 OpenAPI / Skill：

1. **创建外发**：目标对象（外部邮箱/组织/链接？）、有效期、可下载/仅预览、审批流是否必走
2. **白名单 / 合规**：允许外发的空间/文件类型、敏感标拦截、审计日志字段
3. **查询外发状态**：按任务 id / 文件 id 查询进行中/已完成/已过期
4. **撤销外发**：撤销后链接是否立即失效；是否通知接收方
5. **与协同分享边界**：OutSend 与 `t_file_share` 是否互斥、是否可并存、话术如何区分

确认后更新本 README，再补真实脚本与 `acceptance-runbook` 用例。
