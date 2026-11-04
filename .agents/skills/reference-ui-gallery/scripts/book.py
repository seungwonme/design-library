"""Curated reading records; source reading never implies runtime verification."""
from datetime import date
import html
from urllib.parse import quote, urlsplit

CATEGORIES = {
    "reference": "디자인 레퍼런스",
    "library": "UI 컴포넌트/라이브러리",
    "asset": "아이콘/에셋",
    "design-system": "디자인 시스템",
    "guideline": "UX 규칙",
    "inbox": "수집함",
}
LEVELS = {"unread": "원문 미확인", "source-read": "문서 확인", "hands-on": "직접 검증"}


def web_source(value, api):
    api.source_location(value)
    parsed = urlsplit(value)
    api.require(parsed.scheme in {"http", "https"} and parsed.hostname, "Book sources must be public HTTP(S) URLs.")


def new_note(args, workspace, api):
    root = api.entry_root(workspace, args.slug)
    api.require(not root.exists(), "Entry already exists; read and merge it instead of overwriting.")
    web_source(args.source, api)
    data = api.load_json(api.ASSETS / "book-template.json")
    data.update(id=args.slug, title=args.title, category=args.category, platforms=[args.platform])
    data["sources"][0]["location"] = args.source
    root.mkdir(parents=True)
    (root / "reference.json").write_text(api.dump_json(data), encoding="utf-8")
    return {"created": str(root), "status": "draft", "verification": "unread"}


def validate(root, data, api, ready=False, public=False):
    require = api.require
    text = api.nonempty
    require(type(data.get("schema_version")) is int and data["schema_version"] == 2, "Book records require schema_version 2.")
    require(data.get("id") == root.name and api.SLUG.fullmatch(root.name), "Metadata id must match the entry folder.")
    require(text(data.get("title")), "Entry title is missing.")
    if data.get("url"):
        web_source(data["url"], api)
    require(api.choice(data.get("status"), {"draft", "ready"}), "Entry status must be draft or ready.")
    ready = ready or public or data["status"] == "ready"
    require(api.choice(data.get("category"), {*CATEGORIES, "flow"}), "Choose a library category.")
    for key in ("platforms", "tags"):
        require(isinstance(data.get(key), list) and all(text(x) for x in data[key]), f"{key} must be a string array.")
    require(data["platforms"] and all(x in {"web", "mobile", "desktop"} for x in data["platforms"]), "Choose valid platforms.")
    sources = data.get("sources")
    require(isinstance(sources, list) and sources, "At least one source is required.")
    ids, read_ids = set(), set()
    for source in sources:
        require(isinstance(source, dict) and text(source.get("id")), "Each source needs an id.")
        require(source["id"] not in ids, "Source ids must be unique.")
        ids.add(source["id"])
        web_source(source.get("location"), api)
        require(isinstance(source.get("method"), str), "Each source needs a method string, even when unread.")
        require("title" not in source or text(source["title"]), "Source titles must be non-empty text when present.")
        require(api.choice(source.get("access"), {"read", "unread", "blocked"}), "Each source needs an access status.")
        if source["access"] != "unread":
            require(text(source.get("method")), "Record how a source was read or blocked.")
        if source["access"] == "read":
            read_ids.add(source["id"])
    facts = data.get("evidence")
    require(isinstance(facts, list), "evidence must be an array.")
    for fact in facts:
        require(isinstance(fact, dict) and api.choice(fact.get("kind"), {"observed", "measured", "inferred", "proposed"}), "Evidence needs an explicit kind.")
        require(fact.get("source_id") in read_ids and text(fact.get("locator")) and text(fact.get("finding")), "Evidence needs a read source, locator, and finding.")
    assessment = data.get("assessment")
    require(isinstance(assessment, dict) and isinstance(assessment.get("why"), str), "assessment needs a why string.")
    for key in ("use_when", "avoid_when", "takeaways"):
        require(isinstance(assessment.get(key), list) and all(text(x) for x in assessment[key]), f"assessment.{key} must be a string array.")
        if ready:
            require(assessment[key], f"Ready book records need assessment.{key}.")
    details = data.get("details")
    require(isinstance(details, list) and all(isinstance(x, dict) and text(x.get("label")) and text(x.get("value")) for x in details), "details must contain label/value records.")
    flow = data.get("flow")
    require(isinstance(flow, list), "flow must be an array.")
    for step in flow:
        require(isinstance(step, dict) and all(text(step.get(key)) for key in ("state", "action", "feedback", "recovery")), "Flow steps need state, action, feedback, and recovery.")
    checks = data.get("verification")
    require(isinstance(checks, dict) and api.choice(checks.get("level"), LEVELS), "Record unread, source-read, or hands-on verification.")
    require(all(isinstance(checks.get(key), str) for key in ("checked_at", "scope")), "Verification needs checked_at and scope strings, even in drafts.")
    require(isinstance(checks.get("evidence"), list), "verification.evidence must be an array.")
    for path in checks["evidence"]:
        api.safe_path(root, path, exists=True)
    if checks["level"] != "unread":
        require(read_ids and facts and text(checks.get("scope")), "Verification needs source evidence and a precise scope.")
        require(len(checks["checked_at"]) == 10, "Use an ISO date: YYYY-MM-DD.")
        try:
            date.fromisoformat(checks.get("checked_at", ""))
        except (TypeError, ValueError):
            require(False, "Verification needs a valid checked_at date (YYYY-MM-DD).")
    if checks["level"] == "hands-on":
        require(checks["evidence"], "Hands-on verification needs a local evidence file.")
    publication = data.get("publication")
    require(isinstance(publication, dict) and api.choice(publication.get("review"), {"pending", "approved", "rejected"}) and api.choice(publication.get("rights"), {"unreviewed", "cleared", "blocked"}), "publication needs review and rights status.")
    require(isinstance(data.get("summary"), str), "summary must be text.")
    if ready:
        require(checks["level"] != "unread" and text(data["summary"]) and text(assessment["why"]), "Ready records need a read source, summary, and assessment.")
        require(details, "Ready records need category-specific details.")
        if data["category"] == "flow":
            require(len(flow) >= 2, "Ready flow records need a sequence, including recovery behavior.")
    if public:
        require(publication["review"] == "approved" and publication["rights"] == "cleared" and text(publication.get("notes")), "Public notes need approved review, cleared rights, and notes.")
    return data, {"id": root.name, "record_type": "note", "check": "ready-records" if ready else "draft-structure", "verification": checks["level"], "visual_quality": "not-automatically-assessed"}


def catalog_item(data, prefix):
    assessment = data["assessment"]
    searchable = [assessment["why"], *assessment["use_when"], *assessment["avoid_when"], *assessment["takeaways"]]
    searchable += [value for item in data["details"] for value in (item["label"], item["value"])]
    searchable += [value for step in data["flow"] for value in step.values() if isinstance(value, str)]
    searchable += [source.get("title", "") + " " + source["location"] for source in data["sources"]]
    return {"record_type": "note", "category": "reference" if data["category"] == "flow" else data["category"], "summary": data["summary"],
            "search_text": " ".join(searchable),
            "verification": data["verification"]["level"], "checked_at": data["verification"]["checked_at"],
            "source": data.get("url") or data["sources"][0]["location"], "preview": prefix + "index.html",
            "design": "", "tokens": "", "thumbnail": "", "metadata": prefix + "reference.json"}


def render(data, api, custom_style=False, drafts=False):
    esc = html.escape
    def section(title, values):
        return '<section><h2>' + esc(title) + '</h2><ul>' + ''.join('<li>' + esc(x) + '</li>' for x in values) + '</ul></section>' if values else ''
    assessment = data["assessment"]
    blocks = '<section><h2>왜 기록했나</h2><p>' + esc(assessment["why"] or "원문을 확인한 뒤 평가합니다.") + '</p></section>'
    blocks += section("가져올 원칙", assessment["takeaways"])
    blocks += section("이럴 때 사용", assessment["use_when"])
    blocks += section("피하거나 확인할 조건", assessment["avoid_when"])
    if data["details"]:
        blocks += '<section><h2>살펴볼 내용</h2><dl>' + ''.join('<div><dt>' + esc(x["label"]) + '</dt><dd>' + esc(x["value"]) + '</dd></div>' for x in data["details"]) + '</dl></section>'
    if data["flow"]:
        blocks += '<section><h2>사용자 흐름</h2><ol class="flow-steps">' + ''.join('<li><h3>' + esc(x["state"]) + '</h3><p><strong>행동</strong> ' + esc(x["action"]) + '</p><p><strong>피드백</strong> ' + esc(x["feedback"]) + '</p><p><strong>복귀 / 오류</strong> ' + esc(x["recovery"]) + '</p></li>' for x in data["flow"]) + '</ol></section>'
    source_map = {x["id"]: x for x in data["sources"]}
    kinds = {"observed": "원문 확인", "measured": "측정", "inferred": "해석", "proposed": "적용 제안"}
    facts = ['<li><span class="evidence-kind">' + kinds[x["kind"]] + '</span> ' + esc(x["finding"]) + ' <a href="' + esc(source_map[x["source_id"]]["location"], quote=True) + '">' + esc(x["locator"]) + '</a></li>' for x in data["evidence"]]
    blocks += '<section><h2>출처와 근거</h2><ul class="sources">' + ''.join(facts) + '</ul><ul>'
    access_labels = {"read": "원문 확인", "unread": "연결 원문 미확인", "blocked": "접근 불가"}
    for source in data["sources"]:
        blocks += '<li><a href="' + esc(source["location"], quote=True) + '">' + esc(source.get("title") or source["location"]) + '</a><p>' + access_labels[source["access"]] + ' / ' + esc(source["method"] or "아직 읽지 않았습니다.") + '</p></li>'
    blocks += '</ul></section>'
    if data["verification"]["evidence"]:
        blocks += '<section><h2>검증 자료</h2><ul>' + ''.join('<li><a href="' + esc(quote(path, safe="/"), quote=True) + '">' + esc(path) + '</a></li>' for path in data["verification"]["evidence"]) + '</ul></section>'
    template = (api.ASSETS / "book-note.html").read_text(encoding="utf-8")
    values = {"TITLE": esc(data["title"]), "CATEGORY": esc(CATEGORIES.get(data["category"], "디자인 레퍼런스")),
              "SUMMARY": esc(data["summary"]), "LEVEL": esc(LEVELS[data["verification"]["level"]]),
              "CHECKED": esc(data["verification"]["checked_at"] or "확인 전"), "SCOPE": esc(data["verification"]["scope"]),
              "CONTENT": blocks, "CUSTOM_STYLE": '<link rel="stylesheet" href="../../gallery.css">' if custom_style else '',
              "DRAFT": '<p class="draft-notice" data-build="DRAFT">로컬 보관 자료</p>' if drafts else ''}
    # Substitute only template markers; source strings never become template instructions.
    import re
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], template)
