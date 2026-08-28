#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "photos" / "manifest.json"
HTML_FILES = sorted(ROOT.glob("*.html"))
MAIN_IMAGE = "assets/photos/salon-fenetre.jpg"
MAIN_IMAGE_ABSOLUTE = f"https://parisauriol.com/{MAIN_IMAGE}"
MAIN_IMAGE_CSS = "/assets/photos/salon-fenetre.jpg"
SECOND_IMAGE_CSS = "/assets/photos/cuisine-equipee.jpg"
LANGUAGES = ("fr", "en", "de", "es")


def add_query(url: str, language: str) -> str:
    parts = urlsplit(url)
    query: dict[str, str] = {}
    if parts.query:
        for entry in parts.query.split("&"):
            if "=" in entry:
                key, value = entry.split("=", 1)
                query[key] = value
    if language != "fr":
        query["lang"] = language
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def add_stylesheet(text: str) -> str:
    if 'href="assets/enhancements.css"' in text:
        return text
    return text.replace(
        '<link rel="stylesheet" href="assets/style.css">',
        '<link rel="stylesheet" href="assets/style.css">\n  <link rel="stylesheet" href="assets/enhancements.css">',
        1,
    )


def add_hreflang(text: str) -> str:
    text = re.sub(r'\n?\s*<link rel="alternate" hreflang="[^"]+" href="[^"]+">', '', text)
    match = re.search(r'<link rel="canonical" href="([^"]+)">', text)
    if not match:
        return text
    canonical = match.group(1)
    links = [
        f'<link rel="alternate" hreflang="{language}" href="{add_query(canonical, language)}">'
        for language in LANGUAGES
    ]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{canonical}">')
    return text.replace(match.group(0), match.group(0) + "\n  " + "\n  ".join(links), 1)


def update_social_image(text: str) -> str:
    text = re.sub(
        r'(<meta property="og:image" content=")[^"]+(">)',
        rf'\1{MAIN_IMAGE_ABSOLUTE}\2',
        text,
    )
    if 'property="og:image:width"' not in text:
        text = text.replace(
            f'<meta property="og:image" content="{MAIN_IMAGE_ABSOLUTE}">',
            f'<meta property="og:image" content="{MAIN_IMAGE_ABSOLUTE}">\n  '
            '<meta property="og:image:width" content="1280">\n  '
            '<meta property="og:image:height" content="576">',
            1,
        )
    return text


def picture_markup(photo: dict[str, object], css_class: str) -> str:
    captions = photo["captions"]
    variants = photo["variants"]
    original = photo["original"]
    position = int(photo["position"])
    width = int(photo["width"])
    height = int(photo["height"])
    caption_fr = str(captions["fr"])
    caption_attrs = " ".join(
        f'data-caption-{language}="{html.escape(str(captions[language]), quote=True)}"'
        for language in LANGUAGES
    )
    sizes = (
        "(max-width: 480px) 100vw, (max-width: 760px) 50vw, 66vw"
        if position == 1
        else "(max-width: 480px) 100vw, (max-width: 760px) 50vw, 33vw"
    )
    loading = "eager" if position == 1 else "lazy"
    return (
        f'<a class="gallery-item {css_class}" href="{html.escape(str(original), quote=True)}" '
        f'data-lightbox {caption_attrs}>'
        f'<picture><source type="image/webp" '
        f'srcset="{variants["480"]} 480w, {variants["768"]} 768w, {variants["1024"]} 1024w" '
        f'sizes="{sizes}">'
        f'<img src="{original}" alt="{html.escape(caption_fr, quote=True)}" '
        f'width="{width}" height="{height}" loading="{loading}" decoding="async"></picture>'
        f'<span class="gallery-caption">{html.escape(caption_fr)}</span></a>'
    )


def build_gallery(manifest: dict[str, object]) -> str:
    items: list[str] = []
    for photo in manifest["photos"]:
        position = int(photo["position"])
        ratio = int(photo["width"]) / int(photo["height"])
        if position == 1:
            css_class = "gallery-item-main"
        elif ratio < 0.85:
            css_class = "gallery-item-tall"
        elif position in {5, 8}:
            css_class = "gallery-item-wide"
        else:
            css_class = ""
        items.append(picture_markup(photo, css_class))
    return (
        '<div class="gallery real-gallery" aria-label="Photographies originales du logement">\n      '
        + "\n      ".join(items)
        + "\n    </div>"
    )


def update_photos_page(text: str, manifest: dict[str, object]) -> str:
    text = text.replace(
        "La structure de la galerie est prête. Pour éviter toute image trompeuse, seules les photos originales du logement seront publiées ici.",
        "Découvrez l’appartement, ses équipements et ses différentes vues grâce aux photographies réelles de l’annonce.",
    )
    start = text.find('<div class="notice notice-info">', text.find('<section class="section">'))
    end = text.find('<div class="actions center">', start)
    if start == -1 or end == -1:
        raise RuntimeError("Zone de galerie introuvable dans photos.html")
    notice = (
        '<div class="notice notice-info"><b>Photographies réelles du logement.</b> '
        'Cliquez sur une image pour l’agrandir.</div>\n    '
    )
    return text[:start] + notice + build_gallery(manifest) + "\n    " + text[end:]


def update_json_ld(text: str, manifest: dict[str, object]) -> str:
    pattern = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
    match = pattern.search(text)
    if not match:
        return text
    try:
        payload = json.loads(match.group(2))
    except json.JSONDecodeError:
        return text
    payload["image"] = [
        f"https://parisauriol.com/{photo['original']}" for photo in manifest["photos"]
    ]
    payload["inLanguage"] = "fr"
    payload["availableLanguage"] = ["fr", "en", "de", "es"]
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return text[:match.start()] + match.group(1) + compact + match.group(3) + text[match.end():]


def update_index_page(text: str, manifest: dict[str, object]) -> str:
    text = re.sub(
        r"--hero-image:url\('[^']+'\)",
        f"--hero-image:url('{MAIN_IMAGE_CSS}')",
        text,
        count=1,
    )
    text = re.sub(
        r"--frame-image:url\('[^']+'\)",
        f"--frame-image:url('{SECOND_IMAGE_CSS}')",
        text,
        count=1,
    )
    text = text.replace(
        "Paris — image d’ambiance. Les photos originales du logement seront ajoutées à la galerie.",
        "Vue réelle du logement Paris Auriol Austerlitz Arena.",
    )
    if f'rel="preload" as="image" href="{MAIN_IMAGE}"' not in text:
        text = text.replace(
            '<link rel="stylesheet" href="assets/style.css">',
            f'<link rel="preload" as="image" href="{MAIN_IMAGE}">\n  '
            '<link rel="stylesheet" href="assets/style.css">',
            1,
        )
    return update_json_ld(text, manifest)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("count") != 8:
        raise RuntimeError("Le manifeste doit contenir exactement huit photographies.")
    changed: list[str] = []
    for path in HTML_FILES:
        original = path.read_text(encoding="utf-8")
        text = add_stylesheet(original)
        text = add_hreflang(text)
        text = update_social_image(text)
        if path.name == "index.html":
            text = update_index_page(text, manifest)
        elif path.name == "photos.html":
            text = update_photos_page(text, manifest)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(path.name)
    print("Pages mises à jour :", ", ".join(changed) if changed else "aucune")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
