#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
from typing import Any
from urllib.error import URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import urlopen

SEARCH_URL = "https://radio.garden/api/search"
LISTEN_URL_TEMPLATE = "https://radio.garden/api/ara/content/listen/{station_id}/channel.mp3"


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "station"


def read_url(url: str) -> tuple[str, str]:
    """Returns (body, final_url) for JSON/text endpoints."""
    try:
        with urlopen(url, timeout=20) as response:
            return response.read().decode("utf-8"), str(getattr(response, "url", url))
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        insecure_ctx = ssl._create_unverified_context()
        with urlopen(url, timeout=20, context=insecure_ctx) as response:
            return response.read().decode("utf-8"), str(getattr(response, "url", url))


def fetch_json(url: str) -> dict[str, Any]:
    body, _ = read_url(url)
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Unexpected API response format.")
    return payload


def resolve_final_url(url: str) -> str:
    """
    Resolve redirects and return the final URL without reading the response body.
    This avoids hanging on endless streaming audio responses.
    """
    try:
        with urlopen(url, timeout=20) as response:
            return str(getattr(response, "url", url))
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        insecure_ctx = ssl._create_unverified_context()
        with urlopen(url, timeout=20, context=insecure_ctx) as response:
            return str(getattr(response, "url", url))


def search_station(station_query: str) -> dict[str, str]:
    query = urlencode({"q": station_query})
    payload = fetch_json(f"{SEARCH_URL}?{query}")
    hits = payload.get("hits", {}).get("hits", [])
    if not isinstance(hits, list) or not hits:
        raise ValueError(f"No station found for query: {station_query}")

    wanted = station_query.strip().lower()
    first: dict[str, Any] | None = None
    for item in hits:
        if not isinstance(item, dict):
            continue
        source = item.get("_source", {})
        if not isinstance(source, dict):
            continue
        page = source.get("page", {})
        if not isinstance(page, dict):
            continue
        if str(page.get("type", "")).strip().lower() != "channel":
            continue
        title = str(page.get("title", "")).strip()
        subtitle = str(page.get("subtitle", "")).strip()
        page_url = str(page.get("url", "")).strip()
        station_id = extract_station_id_from_path(page_url)
        if not title or not station_id:
            continue
        if first is None:
            first = source
        combined = f"{title} {subtitle}".lower()
        if wanted == title.lower() or wanted in combined:
            return {
                "id": station_id,
                "title": title,
                "subtitle": subtitle,
            }

    if first is None:
        raise ValueError(f"No usable station result for query: {station_query}")
    page = first.get("page", {}) if isinstance(first, dict) else {}
    page_url = str(page.get("url", "")).strip() if isinstance(page, dict) else ""
    station_id = extract_station_id_from_path(page_url)
    if not station_id:
        raise ValueError(f"No channel id found for query: {station_query}")
    return {
        "id": station_id,
        "title": str(page.get("title", "")).strip() or station_query,
        "subtitle": str(page.get("subtitle", "")).strip(),
    }


def extract_station_id_from_path(path_like: str) -> str:
    path = path_like.strip()
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        path = urlparse(path).path
    parts = [p for p in path.split("/") if p]
    if not parts:
        return ""
    # Expected: /listen/<slug>/<station_id>
    return parts[-1]


def resolve_stream_url(station_id: str) -> str:
    listen_url = LISTEN_URL_TEMPLATE.format(station_id=quote(station_id, safe=""))
    final_url = resolve_final_url(listen_url)
    if not final_url:
        raise ValueError("Unable to resolve stream URL from station ID.")
    return final_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve Radio Garden station to stream URL.")
    parser.add_argument("--station", help="Station name query")
    parser.add_argument("--station-id", help="Station id if you already have it")
    parser.add_argument("--station-url", help="Full Radio Garden station URL")
    args = parser.parse_args()

    if not args.station and not args.station_id and not args.station_url:
        print("ERROR: Provide --station, --station-id, or --station-url", file=sys.stderr)
        sys.exit(1)

    try:
        if args.station_id:
            station_id = args.station_id.strip()
            title = args.station.strip() if args.station else station_id
        elif args.station_url:
            station_id = extract_station_id_from_path(args.station_url)
            if not station_id:
                raise ValueError("Could not parse station id from --station-url")
            title = args.station.strip() if args.station else station_id
        else:
            station = search_station(args.station.strip())
            station_id = station["id"]
            title = station["title"] or args.station.strip()

        stream_url = resolve_stream_url(station_id)
        print(
            json.dumps(
                {
                    "id": station_id,
                    "title": title,
                    "slug": slugify(title),
                    "stream_url": stream_url,
                }
            )
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

