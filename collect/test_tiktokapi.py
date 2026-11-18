"""Premier test de collecte avec TikTokApi.

Récupère des vidéos (trending ou par hashtag) et enregistre un relevé horodaté
dans data/raw/. Lancer ce script régulièrement (ex. chaque jour) permet ensuite
de calculer Growth, Acceleration, SpreadRate, etc.

Usage :
    # ms_token (cookie msToken de tiktok.com) est lu dans le fichier .env
    python3 collect/test_tiktokapi.py                 # vidéos trending
    python3 collect/test_tiktokapi.py --hashtag dance # vidéos d'un hashtag
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from TikTokApi import TikTokApi

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

load_dotenv(ROOT / ".env")  # lit ms_token depuis le fichier .env à la racine


def flatten(video: dict, snapshot_at: str) -> dict:
    """Garde uniquement les champs utiles aux critères de trend."""
    stats = video.get("stats", {})
    author = video.get("author", {})
    music = video.get("music", {})
    return {
        "video_id": video.get("id"),
        "snapshot_at": snapshot_at,
        "created_at": video.get("createTime"),
        "author": author.get("uniqueId"),
        "description": video.get("desc"),
        "hashtags": [c.get("title") for c in video.get("challenges", [])],
        "music_id": music.get("id"),
        "music_title": music.get("title"),
        "region": video.get("locationCreated"),
        "views": stats.get("playCount"),
        "likes": stats.get("diggCount"),
        "shares": stats.get("shareCount"),
        "comments": stats.get("commentCount"),
    }


async def main(hashtag: str | None, count: int, headless: bool, browser: str) -> None:
    ms_token = os.environ.get("ms_token")
    if not ms_token or ms_token == "colle_ton_msToken_ici":
        raise SystemExit("ms_token manquant : renseigne-le dans le fichier .env à la racine du repo.")
    snapshot_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            headless=headless,
            browser=browser,
        )
        source = api.hashtag(name=hashtag).videos(count=count) if hashtag else api.trending.videos(count=count)
        async for video in source:
            rows.append(flatten(video.as_dict, snapshot_at))

    if not rows:
        raise SystemExit(
            "0 vidéo reçue : TikTok bloque la requête. Essaie un msToken frais "
            "(pris en étant connecté), --show-browser, ou un autre réseau."
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{hashtag or 'trending'}_{snapshot_at.replace(':', '-')}.json"
    out = RAW_DIR / name
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))

    print(f"{len(rows)} vidéos enregistrées dans {out}")
    for r in rows[:5]:
        print(f"- @{r['author']} | {r['views']} vues | son: {r['music_title']} | {r['hashtags']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hashtag", help="ex: dance, recette, meme")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--show-browser", action="store_true", help="ouvre le navigateur (moins bloqué par TikTok)")
    parser.add_argument("--browser", default="chromium", choices=["chromium", "webkit", "firefox"])
    args = parser.parse_args()
    asyncio.run(main(args.hashtag, args.count, headless=not args.show_browser, browser=args.browser))
