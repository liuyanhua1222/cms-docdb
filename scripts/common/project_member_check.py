"""空间成员预检公共逻辑（P1-06）。

正式 OpenAPI 成功时 data 为 { projectId, employeeId, isMember }。
查他人时若仍返回裸 Boolean，视为旧网关忽略了 query employeeId，不可信，须回退 listMembers。

注意：listMembers 仅含「人员授权」，不含「仅组织加入」成员；正式关单以结构化 isProjectMember 为准。
"""
from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional, Tuple

from docdb_open_api import request_open_api

MEMBER_PATH = "/document-database/admin/isProjectMember"
LIST_PATH = "/document-database/admin/listMembers"
ORG_FALLBACK_NOTE = (
    "listMembers 回退仅覆盖人员授权成员，不含仅组织加入；"
    "正式环境请部署支持 employeeId 的 isProjectMember（返回含 employeeId 的对象）"
)


def via_list_members(project_id: int, employee_id: int) -> Dict[str, Any]:
    url = f"{LIST_PATH}?{urllib.parse.urlencode({'projectId': str(project_id)})}"
    listed = request_open_api(url, method="GET")
    data = listed.get("data") if isinstance(listed, dict) else None
    found = False
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            eid = row.get("employeeId") or row.get("empId") or row.get("id")
            if eid is not None and int(eid) == int(employee_id):
                found = True
                break
    return {
        "resultCode": listed.get("resultCode", 1) if isinstance(listed, dict) else 1,
        "resultMsg": listed.get("resultMsg") if isinstance(listed, dict) else None,
        "data": {
            "projectId": project_id,
            "employeeId": employee_id,
            "isMember": found,
            "checkMode": "listMembers_fallback",
            "note": ORG_FALLBACK_NOTE,
        },
    }


def _trusted_target_payload(data: Any, project_id: int, target_employee_id: int) -> Optional[Dict[str, Any]]:
    """仅当能证明「查的是目标人」时返回规范化 data；否则 None（须回退）。"""
    if isinstance(data, dict):
        eid = data.get("employeeId")
        if eid is None:
            return None
        try:
            if int(eid) != int(target_employee_id):
                return None
        except (TypeError, ValueError):
            return None
        is_member = data.get("isMember")
        if not isinstance(is_member, bool):
            return None
        return {
            "projectId": data.get("projectId", project_id),
            "employeeId": int(target_employee_id),
            "isMember": is_member,
            "checkMode": data.get("checkMode") or "isProjectMember",
        }
    # 裸 Boolean：旧网关可能忽略 query，返回的是「调用人」结果 → 查他人时不可信
    return None


def check_other_member(project_id: int, employee_id: int) -> Dict[str, Any]:
    """预检指定人是否空间成员。优先正式 API；不可信或失败则 listMembers 回退。"""
    url = (
        f"{MEMBER_PATH}?"
        f"{urllib.parse.urlencode({'projectId': str(project_id), 'employeeId': str(employee_id)})}"
    )
    try:
        result = request_open_api(url, method="GET", fatal=False)
    except Exception:
        return via_list_members(project_id, employee_id)

    if not isinstance(result, dict) or result.get("resultCode") != 1:
        return via_list_members(project_id, employee_id)

    trusted = _trusted_target_payload(result.get("data"), project_id, employee_id)
    if trusted is None:
        return via_list_members(project_id, employee_id)

    return {
        "resultCode": 1,
        "resultMsg": result.get("resultMsg"),
        "data": trusted,
    }


def ensure_project_member(project_id: int, emp_id: int) -> None:
    """供 upsert 等写入前调用；非成员或不明确时 sys.exit(2)。"""
    import sys

    out = check_other_member(project_id, emp_id)
    data = out.get("data") if isinstance(out, dict) else None
    is_member = data.get("isMember") if isinstance(data, dict) else None
    if is_member is True:
        return
    if is_member is False:
        print(
            f"错误: employeeId={emp_id} 不是空间 projectId={project_id} 的成员；"
            "请先 add-member 或改用协同分享。可用 --skip-member-check 跳过（不推荐）。"
            f" checkMode={(data or {}).get('checkMode')}",
            file=sys.stderr,
        )
        if (data or {}).get("checkMode") == "listMembers_fallback":
            print(f"提示: {ORG_FALLBACK_NOTE}", file=sys.stderr)
        sys.exit(2)
    msg = out.get("resultMsg") if isinstance(out, dict) else "未知错误"
    print(f"错误: 预检空间成员失败: {msg}", file=sys.stderr)
    sys.exit(2)
