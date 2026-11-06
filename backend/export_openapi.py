from pathlib import Path

import yaml

from app.main import app


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "docs" / "api" / "openapi.yaml"


def stories_for(path: str) -> list[str]:
    if path.endswith("/requests/{request_id}/decision"):
        return ["T100-19"]
    if path.endswith("/requests/{request_id}/withdraw"):
        return ["T100-22"]
    if path.endswith("/requests"):
        return ["T100-18", "T100-19", "T100-22"]
    if path.endswith("/relationships/{relationship_id}/close"):
        return ["T100-23"]
    if path.endswith("/relationships/{relationship_id}/sessions") or path.endswith("/sessions/{session_id}/decision"):
        return ["T100-24"]
    if path.endswith("/relationships/{relationship_id}/messages"):
        return ["T100-25"]
    if path.endswith("/sessions/{session_id}/notes"):
        return ["T100-26"]
    if path.endswith("/reports") or path.endswith("/admin/reports") or path.endswith("/admin/reports/{report_id}/review"):
        return ["T100-27"]
    if "/admin/users/" in path:
        return ["T100-28"]
    if path.endswith("/admin/analytics"):
        return ["US-21"]
    if path.endswith("/admin/alerts"):
        return ["US-22"]
    if path.endswith("/relationships"):
        return ["T100-20", "T100-21", "T100-23"]
    if path.endswith("/notifications") or "/notifications/" in path:
        return ["Milestone 1 notifications"]
    return []


def main() -> None:
    schema = app.openapi()
    schema["info"]["version"] = app.version
    for path, path_item in schema["paths"].items():
        story_ids = stories_for(path)
        if not story_ids:
            continue
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                operation["x-user-stories"] = story_ids
    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(
        yaml.safe_dump(schema, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {len(schema['paths'])} paths to {SPEC_PATH}")


if __name__ == "__main__":
    main()
