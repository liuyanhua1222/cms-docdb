# 验收 Runbook（Wave2）

## 1. 物理文件闭环（PDF）

固定测空间后依次：

1. `upload-whole-file.py` / 分片上传 → 得 resourceId  
2. `save-file-by-parent-id.py` 或 `save-file-by-path.py` 入库  
3. `get-download-info.py`（预览，不 force-download）  
4. `download-file.py`  
5. `update-file-version.py`（默认 versionStatus=3）

记录：projectId、path、fileId、resourceId、预览是否成功、下载哈希。

## 2. 根目录语义（P2-3）

- 负向：`browse.py --parent-id 0` 应失败并提示用 get-level1-folders  
- 正向：`create-folder.py --parent-id 0 --project-id <pid> --name ... --dry-run` 应打印合法请求

## 3. 目录定位（B-05）

`resolve-path.py --project-id ... --path ...` 输出四元组；多命中须确认；exists=false 不得上传。

## 4. 长正文边界

对 10KB / 30KB / 75KB（或契约上限）各一次 `upload-content` + 回读；失败则记录错误码。

## 5. OutSend

当前 **未封装** 外部协作 OutSend 路由；产品未定前 Agent 不得伪造成功。见挂账 P1-16。
