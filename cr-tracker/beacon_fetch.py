#!/usr/bin/env python3
"""
Fetch a Beacon.tv series/collection's full episode list via the public
GetContentGrid GraphQL endpoint.

How this was found: beacon.tv's own sitemap-content.xml (which would list
every /content/... episode page directly) currently 500s server-side, and
the sitemap's /collection/<slug> URLs are stale - the live route is
/series/<slug>, which is server-rendered. A plain GET to /series/<slug>
embeds a Next.js __NEXT_DATA__ script with an Apollo cache containing a
getSingleCollectionPage(...) result; that gives the show's internal Mongo
collection id but only the first ~12 episodes. The full list comes from
POSTing to /api/graphql with the GetContentGrid operation and a high
`limit`, which returns everything in one page. No authentication was
needed for any of this - Beacon gates video playback by membership tier,
not this metadata.

fetch_collection_episodes('weird-kids') ->
    [{'id':..., 'title':..., 'slug':..., 'episodeNumber':..., 'releaseDate': '2026-09-01'}, ...]

vod_url for a given episode is https://beacon.tv/content/{slug}.
"""
import json
import re
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

GET_CONTENT_GRID_QUERY = """
query GetContentGrid($category: String, $tag: String, $collection: String, $sort: String, $idsToRemove: [String!], $season: Int, $page: Int, $limit: Int, $previewDate: String, $preview: Boolean) {
  search(category: $category, collection: $collection, tag: $tag, sort: $sort, idsToRemove: $idsToRemove, season: $season, page: $page, limit: $limit, previewDate: $previewDate, preview: $preview) {
    totalPages
    totalDocs
    page
    docs {
      id
      title
      slug
      episodeNumber
      releaseDate
      __typename
    }
    __typename
  }
}
""".strip()


def _fetch(url, method="GET", data=None):
    headers = {"User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def get_collection_id(series_slug):
    """GET /series/<slug> and pull the Collection's Mongo id out of __NEXT_DATA__."""
    html = _fetch(f"https://beacon.tv/series/{series_slug}")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        raise RuntimeError(f"no __NEXT_DATA__ found for series/{series_slug}")
    data = json.loads(m.group(1))
    apollo = data["props"]["pageProps"]["__APOLLO_STATE__"]
    root = apollo.get("ROOT_QUERY", {})
    for key, val in root.items():
        if key.startswith("getSingleCollectionPage(") and val and val.get("docs"):
            ref = val["docs"][0]["__ref"]  # e.g. "Collection:67c4212a45894204e65efaf0"
            return ref.split(":", 1)[1]
    raise RuntimeError(f"no getSingleCollectionPage ref found for series/{series_slug}")


def fetch_collection_episodes(series_slug, page_size=100):
    """Returns (collection_id, [episode dicts]) - every episode in the collection, unpaginated."""
    collection_id = get_collection_id(series_slug)
    episodes = []
    page = 1
    while True:
        body = {
            "operationName": "GetContentGrid",
            "variables": {
                "collection": collection_id,
                "sort": "-aggregateEpisodeNumber",
                "season": None,
                "preview": False,
                "page": page,
                "limit": page_size,
                "idsToRemove": [],
            },
            "query": GET_CONTENT_GRID_QUERY,
        }
        raw = _fetch("https://beacon.tv/api/graphql", method="POST", data=body)
        result = json.loads(raw)
        search = result["data"]["search"]
        for doc in search["docs"]:
            episodes.append({
                "id": doc["id"],
                "title": doc["title"],
                "slug": doc["slug"],
                "episodeNumber": doc.get("episodeNumber"),
                "releaseDate": (doc.get("releaseDate") or "")[:10],
            })
        if page >= search["totalPages"]:
            break
        page += 1
    return collection_id, episodes


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "weird-kids"
    cid, eps = fetch_collection_episodes(slug)
    print(f"{slug} -> collection id {cid}, {len(eps)} episodes")
    for e in eps[:5]:
        print(" ", e)
