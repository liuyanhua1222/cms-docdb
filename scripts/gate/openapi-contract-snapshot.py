#!/usr/bin/env python3
"""发布门禁：从 DocumentDatabaseController 粗提取 OpenAPI 映射快照（本地静态）。

不连网；输出 JSON 到 stdout。用于契约漂移对照。

路径解析顺序：
1. 环境变量 CMS_DOCDB_OPENAPI_CONTROLLER
2. 相对本脚本上溯常见 monorepo：../../../all-code/open-api/...
3. 相对 cwd：open-api/... 或 ../open-api/...
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_RELATIVE_CANDIDATES = [
    # cms-docdb/scripts/gate → ../../../../all-code/open-api/...
    os.path.join(_HERE, "..", "..", "..", "..", "all-code", "open-api",
                 "src", "main", "java", "com", "xgjktech", "openapi", "controller",
                 "DocumentDatabaseController.java"),
    # cms-docdb 与 open-api 同级（少见）
    os.path.join(_HERE, "..", "..", "..", "open-api",
                 "src", "main", "java", "com", "xgjktech", "openapi", "controller",
                 "DocumentDatabaseController.java"),
    os.path.join(os.getcwd(), "src", "main", "java", "com", "xgjktech", "openapi",
                 "controller", "DocumentDatabaseController.java"),
    os.path.join(os.getcwd(), "open-api", "src", "main", "java", "com", "xgjktech",
                 "openapi", "controller", "DocumentDatabaseController.java"),
    os.path.join(os.getcwd(), "..", "open-api", "src", "main", "java", "com", "xgjktech",
                 "openapi", "controller", "DocumentDatabaseController.java"),
]


def resolve_controller_path() -> str:
    env = (os.environ.get("CMS_DOCDB_OPENAPI_CONTROLLER") or "").strip()
    if env and os.path.isfile(env):
        return os.path.abspath(env)
    for cand in _RELATIVE_CANDIDATES:
        path = os.path.abspath(cand)
        if os.path.isfile(path):
            return path
    return env or os.path.abspath(_RELATIVE_CANDIDATES[0])


def main():
    path = resolve_controller_path()
    if not os.path.isfile(path):
        print(json.dumps({
            "resultCode": 0,
            "resultMsg": (
                f"controller not found: {path}; "
                "set CMS_DOCDB_OPENAPI_CONTROLLER to DocumentDatabaseController.java"
            ),
        }, ensure_ascii=False))
        sys.exit(2)
    text = open(path, encoding="utf-8").read()
    pattern = re.compile(
        r'@(Get|Post|Put|Delete)Mapping\s*\(\s*(?:value\s*=\s*)?"([^"]+)"',
        re.MULTILINE,
    )
    endpoints = []
    for m in pattern.finditer(text):
        endpoints.append({"method": m.group(1).upper(), "path": m.group(2)})
    required_snippets = [
        "/admin/isProjectMember",
        "/fileGrant/stripGrants",
        "/file/listDescendantFiles",
        "/file/listChanges",
        "/file/batchGetMeta",
        "OpenProjectMemberCheckVO",
    ]
    missing = [s for s in required_snippets if s not in text]
    out = {
        "resultCode": 1 if not missing else 0,
        "resultMsg": None if not missing else f"missing snippets: {missing}",
        "data": {
            "controller": path,
            "endpointCount": len(endpoints),
            "endpoints": endpoints,
            "requiredSnippetsOk": not missing,
            "missingSnippets": missing,
            "deployOrder": "document-database(openIsProjectMember) → open-api → Skill",
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if not missing else 1)


if __name__ == "__main__":
    main()
