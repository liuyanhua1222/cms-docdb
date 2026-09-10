#!/usr/bin/env python3
"""权限白名单与自然语言映射（协同分享 / 目录授权共用）。

对外中文名对齐产品「权限设置」UI 八项。
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

# UI 标准用语（唯一对外名称）
PERMISSION_LABELS = {
    "read": "查看列表",
    "preview": "在线预览",
    "download": "下载",
    "delete": "删除",
    "upload": "上传/编辑",
    "fileshare": "分享",
    "permmanage": "权限管理",
    "admin": "管理员",
    "outsend": "外发",
    "create": "创建目录",
    "show": "展示",
}

SHARE_GRANT_ALLOWLIST = frozenset(
    {"read", "preview", "download", "upload", "delete", "fileshare"}
)

GRANT_ALLOWLIST = frozenset(
    {"read", "preview", "download", "upload", "delete", "fileshare", "create"}
)

FORBIDDEN_SHARE_GRANTS = frozenset(
    {"admin", "permmanage", "outsend", "show", "workreport", "workplan"}
)

DEFAULT_SHARE_PERMISSIONS = ["read", "preview"]


def parse_permission_csv(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def validate_share_permissions(perms: Sequence[str]) -> List[str]:
    if not perms:
        raise ValueError("permissions 不能为空")
    unknown = [p for p in perms if p not in PERMISSION_LABELS]
    if unknown:
        raise ValueError(f"未知权限值: {', '.join(unknown)}")
    forbidden = [p for p in perms if p in FORBIDDEN_SHARE_GRANTS]
    if forbidden:
        labels = "、".join(PERMISSION_LABELS.get(p, p) for p in forbidden)
        raise ValueError(f"协同分享禁止授予: {labels}（{', '.join(forbidden)}）")
    not_allowed = [p for p in perms if p not in SHARE_GRANT_ALLOWLIST]
    if not_allowed:
        raise ValueError(f"不在协同分享白名单: {', '.join(not_allowed)}")
    seen = set()
    out: List[str] = []
    for p in perms:
        if p not in seen:
            seen.add(p)
            out.append(p)
    if "read" not in out:
        out.insert(0, "read")
    return out


def validate_grant_permissions(perms: Sequence[str]) -> List[str]:
    if not perms:
        raise ValueError("permissions 不能为空")
    unknown = [p for p in perms if p not in PERMISSION_LABELS]
    if unknown:
        raise ValueError(f"未知权限值: {', '.join(unknown)}")
    if "admin" in perms or "permmanage" in perms:
        raise ValueError("目录授权禁止通过本脚本授予 admin / permmanage")
    bad = [p for p in perms if p not in GRANT_ALLOWLIST]
    if bad:
        raise ValueError(f"不在目录授权白名单: {', '.join(bad)}")
    seen = set()
    out: List[str] = []
    for p in perms:
        if p not in seen:
            seen.add(p)
            out.append(p)
    if "read" not in out:
        out.insert(0, "read")
    return out


def labels_for(perms: Sequence[str]) -> str:
    return "、".join(PERMISSION_LABELS.get(p, p) for p in perms)


def ensure_subset_of_ceiling(requested: Sequence[str], ceiling: Optional[Iterable]) -> None:
    """ceiling 为 None 表示未取到上限（应由调用方 fail-closed）；空集合表示无可分享权限。

    与服务端 ShareService 一致：上限含 admin 时跳过逐项子集校验
    （个人空间 Owner / 一级目录管理员等场景 getMySharePermissions 往往只返回 admin）。
    """
    if ceiling is None:
        raise ValueError(
            "无法校验可分享权限上限（getMySharePermissions 无有效数据）；"
            "请重试或仅在明确知情时使用 --skip-ceiling-check"
        )
    allowed = {str(x).strip() for x in ceiling if str(x).strip()}
    if not allowed:
        raise ValueError("调用方对该文件无可分享权限上限（空集合），拒绝授权")
    # 服务端 isAdmin 时不跑 checkPermission；Skill 侧对齐，避免误拒 read/preview
    if "admin" in allowed:
        return
    # 无 fileshare 且无 admin：通常服务端也会拒分享；此处提前明确失败原因
    if "fileshare" not in allowed:
        raise ValueError(
            "调用方不具备「分享」权限（上限无 fileshare/admin），无法授权他人；"
            f"上限={labels_for(sorted(allowed))}"
        )
    extra = [p for p in requested if p not in allowed]
    if extra:
        raise ValueError(
            "超出调用方可分享上限: "
            + labels_for(extra)
            + f"（{', '.join(extra)}）；上限={labels_for(sorted(allowed))}"
        )
