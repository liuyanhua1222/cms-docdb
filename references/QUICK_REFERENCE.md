# 速查：常用标准 exec 调用

> 强制：将 `<skill-dir>` 换成本 skill 根目录绝对路径；只传业务参数。缺参按 stderr 中文提示补齐后用同一 python 命令重试。写入须 `--confirm YES`（可先 `--dry-run`）。

## browse

```bash
python3 -B <skill-dir>/scripts/browse/get-app-list.py
python3 -B <skill-dir>/scripts/browse/get-uploadable-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/browse/get-project-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py
python3 -B <skill-dir>/scripts/browse/get-level1-folders.py <projectId>
python3 -B <skill-dir>/scripts/browse/browse.py 12345
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料"
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申"
```

## query

```bash
python3 -B <skill-dir>/scripts/query/search.py "合同" --project-id 10001
python3 -B <skill-dir>/scripts/query/get-file-content.py 12345
python3 -B <skill-dir>/scripts/query/get-full-content.py 12345
python3 -B <skill-dir>/scripts/query/get-download-info.py 12345
```

## upload / manage / delete（写入须确认）

```bash
python3 -B <skill-dir>/scripts/upload/create-folder.py 0 "新建目录" --project-id 10001 --dry-run
python3 -B <skill-dir>/scripts/upload/upload-content.py "内容" "报告.md" --project-id 10001 --confirm YES
python3 -B <skill-dir>/scripts/delete/delete-file.py 12345 --confirm YES
python3 -B <skill-dir>/scripts/manage/move-file.py 12345 --target-parent-id 0 --confirm YES
```

## 失败处理

| 现象 | 做法 |
|------|------|
| 脚本公开错误 | 展示给用户；不索要密钥 |
| 缺业务参数 | 按 stderr 补齐后重试同一命令 |
| 须 `--confirm YES` | 先获用户确认再执行 |

详见各模块 `references/*/README.md` 与根目录 `SKILL.md`。
