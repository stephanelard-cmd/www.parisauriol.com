#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "photos"
MANIFEST = OUTPUT / "manifest.json"

# Photos publiques de l’annonce Booking.com PARIS AURIOL.
# Les fichiers sont copiés dans le dépôt : le site ne les affiche pas par hotlink.
PHOTOS = [
    {
        "slug": "salon-fenetre",
        "image_id": "377064721",
        "key": "445bee5b5746f2a027382a61f417cc20eb2452366f1295f397300c57617c0a61",
        "captions": {
            "fr": "Salon lumineux avec canapé et grande fenêtre",
            "en": "Bright living room with sofa and large window",
            "de": "Helles Wohnzimmer mit Sofa und großem Fenster",
            "es": "Salón luminoso con sofá y gran ventana",
        },
    },
    {
        "slug": "immeuble-boulevard",
        "image_id": "606340575",
        "key": "905f9d696674f52df698e4a66e5ee10bff06a4e70e89dc521bf427ae84e7bbd8",
        "captions": {
            "fr": "Immeuble du 18 boulevard Vincent Auriol",
            "en": "Building at 18 Boulevard Vincent Auriol",
            "de": "Gebäude am Boulevard Vincent Auriol 18",
            "es": "Edificio del 18 Boulevard Vincent Auriol",
        },
    },
    {
        "slug": "espace-repas",
        "image_id": "377064292",
        "key": "40e1cdbe55067930e6dcc335e3e9a2d428fa553acc4e0ac82f70073d61ef9580",
        "captions": {
            "fr": "Espace repas intégré au séjour",
            "en": "Dining area adjoining the living room",
            "de": "Essbereich neben dem Wohnzimmer",
            "es": "Zona de comedor junto al salón",
        },
    },
    {
        "slug": "chambre-lit",
        "image_id": "379383001",
        "key": "788d411bc7301f8373c13da4e945094822cf5a20c648b4db3781214ab216f14d",
        "captions": {
            "fr": "Chambre avec grand lit et fenêtre",
            "en": "Bedroom with a large bed and window",
            "de": "Schlafzimmer mit großem Bett und Fenster",
            "es": "Dormitorio con cama grande y ventana",
        },
    },
    {
        "slug": "cuisine-equipee",
        "image_id": "377064355",
        "key": "ed034ca3e3ee598b2a636a62f2f9f2c900a30125e83dee091eeb2dfeeb2e3b51",
        "captions": {
            "fr": "Cuisine équipée et coin repas",
            "en": "Fully equipped kitchen and dining corner",
            "de": "Ausgestattete Küche mit Essplatz",
            "es": "Cocina equipada y rincón comedor",
        },
    },
    {
        "slug": "salon-miroir",
        "image_id": "377064818",
        "key": "df9e30b0f3a88bb6ff52b3997deb2e7c160adcd7e29c5fe66e7b4788a0f2ddcc",
        "captions": {
            "fr": "Salon, canapé et grand miroir",
            "en": "Living room with sofa and large mirror",
            "de": "Wohnzimmer mit Sofa und großem Spiegel",
            "es": "Salón con sofá y espejo grande",
        },
    },
    {
        "slug": "salle-de-bains",
        "image_id": "377064599",
        "key": "012a33c37ceb81fb58b64844c6c4a726436fc138b3efba32d2e36170240356a8",
        "captions": {
            "fr": "Salle de bains avec douche, lavabo et toilettes",
            "en": "Bathroom with shower, washbasin and toilet",
            "de": "Bad mit Dusche, Waschbecken und WC",
            "es": "Baño con ducha, lavabo e inodoro",
        },
    },
    {
        "slug": "vue-seine-bercy",
        "image_id": "379384074",
        "key": "c9f59e51755371e5d011e338725269ce7c628580853101cf1dffe8a6429a3bca",
        "captions": {
            "fr": "Vue urbaine vers la Seine et Bercy",
            "en": "City view towards the Seine and Bercy",
            "de": "Stadtblick in Richtung Seine und Bercy",
            "es": "Vista urbana hacia el Sena y Bercy",
        },
    },
]

SIZES = (480, 768, 1024)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"
)


def candidates(photo: dict[str, object]) -> list[str]:
    image_id = str(photo["image_id"])
    key = str(photo["key"])
    return [
        f"https://cf.bstatic.com/xdata/images/hotel/max1280x900/{image_id}.jpg?k={key}&o=",
        f"https://cf.bstatic.com/xdata/images/hotel/max1024x768/{image_id}.jpg?k={key}&o=",
        f"https://cf.bstatic.com/xdata/images/hotel/max500/{image_id}.jpg?k={key}&o=",
    ]


def download(photo: dict[str, object]) -> tuple[bytes, str]:
    errors: list[str] = []
    for url in candidates(photo):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": "https://www.booking.com/",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
            if len(body) < 10_000:
                raise RuntimeError(f"fichier trop petit ({len(body)} octets)")
            if not content_type.startswith("image/"):
                raise RuntimeError(f"type inattendu {content_type!r}")
            return body, url
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            errors.append(f"{url}: {exc}")
            time.sleep(1)
    raise RuntimeError("Téléchargement impossible :\n" + "\n".join(errors))


def save_variants(photo: dict[str, object], body: bytes, source_url: str) -> dict[str, object]:
    slug = str(photo["slug"])
    with Image.open(io.BytesIO(body)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        width, height = image.size
        if width < 600 or height < 400:
            raise RuntimeError(f"Résolution insuffisante pour {slug}: {width}x{height}")

        original_path = OUTPUT / f"{slug}.jpg"
        image.save(original_path, "JPEG", quality=91, optimize=True, progressive=True)

        variants: dict[str, str] = {}
        for target_width in SIZES:
            actual_width = min(target_width, width)
            ratio = actual_width / width
            resized = image.resize(
                (actual_width, max(1, round(height * ratio))),
                Image.Resampling.LANCZOS,
            )
            target = OUTPUT / f"{slug}-{target_width}.webp"
            resized.save(target, "WEBP", quality=84, method=6)
            variants[str(target_width)] = f"assets/photos/{target.name}"

    return {
        "slug": slug,
        "width": width,
        "height": height,
        "source": "Booking.com",
        "source_url": source_url,
        "original": f"assets/photos/{original_path.name}",
        "variants": variants,
        "captions": photo["captions"],
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for position, photo in enumerate(PHOTOS, start=1):
        print(f"[{position}/{len(PHOTOS)}] {photo['slug']}")
        body, source_url = download(photo)
        item = save_variants(photo, body, source_url)
        item["position"] = position
        manifest.append(item)
        print(f"  {item['width']}x{item['height']} — {len(body)} octets")

    MANIFEST.write_text(
        json.dumps(
            {
                "property": "PARIS AURIOL",
                "address": "18 boulevard Vincent Auriol, 75013 Paris",
                "source": "Booking.com public listing",
                "count": len(manifest),
                "photos": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(manifest)} photos importées dans {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
