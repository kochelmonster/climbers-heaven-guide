import pickle
import requests
from bs4 import BeautifulSoup
from Levenshtein import ratio
from pathlib import Path
from urllib.parse import urlparse

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

try:
    import cfscrape
except Exception:
    cfscrape = None

CACHE_FILE = Path(__file__).parent / "route_cache.pickle"

DOMAIN = "https://www.8a.nu"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

cache = {}

CATEGORY_ID_TO_SLUG = {
    0: "sportclimbing",
    1: "bouldering",
}


def create_scraper_session():
    if cloudscraper is not None:
        scraper = cloudscraper.create_scraper()
    elif cfscrape is not None:
        scraper = cfscrape.create_scraper()
    else:
        scraper = requests.Session()

    scraper.headers.update(HEADERS)
    return scraper

def load_cache():
    global cache
    try:
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
    except FileNotFoundError:
        pass
    cache[None] = 1


def save_cache():
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)


def load_list(url):
    if not len(cache):
        load_cache()

    if url in cache and cache[url]:
        return cache[url]

    routes = []
    scraper = create_scraper_session()

    i = 1
    while True:
        purl = url + f"?page={i}"
        response = scraper.get(purl)
        if response.status_code == 200:
            data = response.content
            if not data:
                break
            soup = BeautifulSoup(data, 'html.parser')
        else:
            raise Exception(f"Could load page {purl}: {response.status_code}")

        table = soup.find("table", class_="main-table zlags-table")
        if table is None:
            break
        rows = table.find_all("tr")
        if len(rows) <= 1:
            break

        for r in rows:
            name = None
            href = None

            # Legacy 8a.nu markup.
            anchor = r.find(class_="name-link")
            if anchor is not None:
                anchor = anchor.find("a")
                if anchor is not None:
                    name = anchor.text.strip()
                    href = anchor.get('href')

            # Current 8a.nu markup.
            if not name or not href:
                row_link = r.find("a", class_="row-link")
                if row_link is not None:
                    href = row_link.get('href')

                name_line = r.find("div", class_="name-line")
                if name_line is not None:
                    name_tag = name_line.find(class_="body1-bold")
                    if name_tag is not None:
                        name = name_tag.get_text(strip=True)
                    else:
                        name = name_line.get_text(" ", strip=True)

            if not name or not href:
                continue

            routes.append((name, href))
            #print(name, href)

        i += 1

    cache[url] = routes
    save_cache()
    return routes


def _parse_crag_context(url):
    path = urlparse(url).path
    parts = [part for part in path.split("/") if part]

    # Expected path: /crags/<category>/<country>/<crag>/routes
    if len(parts) >= 5 and parts[0] == "crags":
        return {
            "category": parts[1],
            "country": parts[2],
            "crag": parts[3],
        }

    return {}


def _normalize_name(value):
    return " ".join(value.lower().split())


def _route_url_from_hit(hit, context):
    zlaggable_slug = hit.get("zlaggableSlug")
    sector_slug = hit.get("sectorSlug")
    crag_slug = hit.get("cragSlug")
    country_slug = hit.get("countrySlug")

    if not (zlaggable_slug and sector_slug and crag_slug and country_slug):
        return None

    category = context.get("category")
    if not category:
        category = CATEGORY_ID_TO_SLUG.get(hit.get("category"))
    if not category:
        return None

    return (
        DOMAIN
        + f"/crags/{category}/{country_slug}/{crag_slug}/sectors/{sector_slug}/routes/{zlaggable_slug}"
    )


def _search_route_url(name, context):
    scraper = create_scraper_session()
    endpoint = DOMAIN + "/api/dotnet/search/zlaggableautocomplete"
    base_params = {
        "query": name,
        "pageSize": 20,
    }

    if context.get("country"):
        base_params["countrySlug"] = context["country"]
    if context.get("category"):
        base_params["category"] = context["category"]

    attempts = [dict(base_params)]
    if context.get("crag"):
        attempts.insert(0, {**base_params, "cragSlug": context["crag"]})

    wanted = _normalize_name(name)
    for params in attempts:
        response = scraper.get(endpoint, params=params)
        if response.status_code != 200:
            continue

        try:
            hits = response.json().get("hits", [])
        except ValueError:
            continue

        exact_hits = [
            hit for hit in hits
            if _normalize_name(hit.get("zlaggableName", "")) == wanted
        ]
        if not exact_hits:
            continue

        hit = max(exact_hits, key=lambda item: item.get("score", 0))
        route_url = _route_url_from_hit(hit, context)
        if route_url:
            return route_url

    return None
    

def find_route_url(url, name):
    context = _parse_crag_context(url)
    routes = load_list(url)

    if not routes:
        return None

    # print("routes", routes)
    name = name.lower()
    distances = [
        (ratio(rname.lower(), name), i)
        for i, (rname, _) in enumerate(routes)]

    distances.sort(reverse=True)

    """    
    for i, (rname, _) in enumerate(routes):
        print(i, rname, ratio(rname.lower(), name))

    print()

    for d, i in distances[:10]:
        print(d, routes[i][0], routes[i][1])
    """
    
    if not distances or distances[0][0] <= 0.55:
        return _search_route_url(name, context)

    href = routes[distances[0][1]][1]
    if not href:
        return None

    if href.startswith("http"):
        return href

    return DOMAIN + href


if __name__ == "__main__":
    url = "https://www.8a.nu/crags/sportclimbing/montenegro/smokovac/routes"
    print(find_route_url(url, "Alerta Feminista!"))

