"""Lightweight saved links and local-only image previews."""
from datetime import date
import html
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

import book
import gallery

PREVIEWS = ".reference-previews"
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def save_image(workspace, slug, source, api):
    source = Path(source).expanduser().resolve()
    api.require(source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES, "Preview must be an existing PNG, JPEG, WebP, or GIF file.")
    api.require(source.stat().st_size <= 20 * 1024 * 1024, "Preview exceeds 20 MiB; resize it before collecting.")
    cache = gallery.managed_path(workspace, PREVIEWS, api)
    target = api.safe_path(cache, slug + source.suffix.lower())
    for suffix in IMAGE_SUFFIXES:
        existing = api.safe_path(cache, slug + suffix)
        if existing.exists():
            api.require(existing.read_bytes() == source.read_bytes(), "A different preview already exists; review it before replacing the local file.")
            return str(existing)
    ignore = gallery.managed_path(workspace, ".gitignore", api)
    current = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if f"/{PREVIEWS}/" not in current.splitlines() and f"{PREVIEWS}/" not in current.splitlines():
        ignore.write_text(current.rstrip("\n") + f"\n/{PREVIEWS}/\n", encoding="utf-8")
    cache.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return str(target)


def collect(args, workspace, api):
    api.require(args.source or args.image or (args.title and args.note), "Supply a URL, image, or a title with a short note.")
    if args.source:
        book.web_source(args.source, api)
    root = api.entry_root(workspace, args.slug)
    image = Path(args.image).expanduser().resolve() if args.image else None
    if image:
        api.require(image.is_file() and image.suffix.lower() in IMAGE_SUFFIXES, "Preview must be an existing PNG, JPEG, WebP, or GIF file.")
        api.require(image.stat().st_size <= 20 * 1024 * 1024, "Preview exceeds 20 MiB; resize it before collecting.")
    # An exact source match reuses the record, retaining prior notes and categorization.
    directory = workspace / "references"
    for existing in sorted(directory.iterdir()) if directory.exists() else []:
        if not existing.is_dir() or existing.name.startswith("."):
            continue
        existing = api.entry_root(workspace, existing.name)
        data = api.load_json(api.safe_path(existing, "reference.json", exists=True))
        sources = data.get("sources", [])
        urls = [data.get("url") or (sources[0].get("location") if sources else None)]
        if args.source and args.source in urls:
            preview = save_image(workspace, existing.name, image, api) if image else ""
            return {"id": existing.name, "record": str(existing / "reference.json"), "created": False, "preview": preview}
    api.require(not root.exists(), "Entry id already exists with another source; choose a different id.")
    data = api.load_json(api.ASSETS / "bookmark-template.json")
    data.update(id=args.slug, title=args.title or (urlsplit(args.source).hostname if args.source else image.stem), category=args.category,
                url=args.source or "", note=args.note, tags=list(dict.fromkeys(args.tag)),
                platforms=[args.platform], saved_at=date.today().isoformat(),
                source_kind="link" if args.source else "image" if image else "note")
    validate(root, data, api)
    root.mkdir(parents=True)
    (root / "reference.json").write_text(api.dump_json(data), encoding="utf-8")
    preview = save_image(workspace, args.slug, image, api) if image else ""
    return {"id": args.slug, "record": str(root / "reference.json"), "created": True, "category": args.category, "preview": preview}


def validate(root, data, api, public=False):
    require = api.require
    require(type(data.get("schema_version")) is int and data["schema_version"] == 3, "Saved links require schema_version 3.")
    require(data.get("id") == root.name and api.SLUG.fullmatch(root.name), "Metadata id must match the entry folder.")
    require(api.nonempty(data.get("title")) and data.get("status") == "saved", "Saved links need a title and status=saved.")
    require(api.choice(data.get("category"), book.CATEGORIES), "Choose a library category or inbox.")
    require(isinstance(data.get("url"), str), "url must be text; local images may leave it empty.")
    if data["url"]:
        book.web_source(data["url"], api)
    require(isinstance(data.get("note"), str), "note must be text; an empty note is allowed.")
    kind = data.get("source_kind", "link" if data["url"] else "image")
    require(api.choice(kind, {"link", "image", "note"}), "source_kind must be link, image, or note.")
    require((kind == "link") == bool(data["url"]), "Link records need a URL; local images and notes leave it empty.")
    require(kind != "note" or api.nonempty(data["note"]), "A text-only record needs a note.")
    require(isinstance(data.get("tags"), list) and all(api.nonempty(x) for x in data["tags"]), "tags must be a string array.")
    platforms = data.get("platforms")
    require(isinstance(platforms, list) and platforms and all(api.choice(x, {"web", "mobile", "desktop"}) for x in platforms), "Choose valid platforms.")
    try:
        date.fromisoformat(data.get("saved_at", ""))
    except (TypeError, ValueError):
        require(False, "saved_at needs an ISO date.")
    publication = data.get("publication")
    require(isinstance(publication, dict) and api.choice(publication.get("review"), {"pending", "approved", "rejected"}) and api.choice(publication.get("rights"), {"unreviewed", "cleared", "blocked"}), "publication needs review and rights status.")
    if public:
        require(kind != "image", "Image-only records stay local until packaged with explicitly approved assets.")
        require(publication["review"] == "approved" and publication["rights"] == "cleared" and api.nonempty(publication.get("notes")), "Public links need an explicit publication review.")
    return data, {"id": root.name, "record_type": "bookmark", "check": "saved-link", "visual_quality": "not-assessed"}


def catalog_item(data, prefix):
    return {"record_type": "bookmark", "category": data["category"], "summary": data["note"],
            "search_text": data["url"], "verification": "saved", "checked_at": data["saved_at"],
            "source": data["url"], "preview": prefix + "index.html", "design": "", "tokens": "",
            "thumbnail": "", "metadata": prefix + "reference.json"}


def local_preview(workspace, slug, output, api):
    cache = gallery.managed_path(workspace, PREVIEWS, api)
    if not cache.exists():
        return ""
    for suffix in IMAGE_SUFFIXES:
        image = api.safe_path(cache, slug + suffix)
        if image.is_file():
            destination = output / "previews" / image.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image, destination)
            return "previews/" + image.name
    return ""


def render(data, api, custom_style=False, thumbnail=""):
    esc = html.escape
    image = '<img class="saved-preview" src="../../' + esc(thumbnail, quote=True) + '" alt="' + esc(data["title"], quote=True) + ' 미리보기">' if thumbnail else ''
    target = data["url"] or ("../../" + thumbnail if thumbnail else "")
    source_button = '<a class="source-button" href="' + esc(target, quote=True) + '" target="_blank" rel="noopener noreferrer">' + ("원본 열기" if data["url"] else "이미지 열기") + '</a>' if target else ''
    values = {"TITLE": esc(data["title"]), "CATEGORY": esc(book.CATEGORIES[data["category"]]),
              "SOURCE_BUTTON": source_button, "DOMAIN": esc(urlsplit(data["url"]).hostname or ("메모" if data.get("source_kind") == "note" else "로컬 이미지")),
              "NOTE": esc(data["note"] or "메모 없이 저장한 자료입니다."), "DATE": esc(data["saved_at"]),
              "TAGS": ''.join('<span class="tag">' + esc(tag) + '</span>' for tag in data["tags"]),
              "IMAGE": image, "CUSTOM_STYLE": '<link rel="stylesheet" href="../../gallery.css">' if custom_style else ''}
    template = (api.ASSETS / "bookmark.html").read_text(encoding="utf-8")
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], template)
