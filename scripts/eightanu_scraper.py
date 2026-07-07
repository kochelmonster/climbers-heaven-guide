#import requests
import pickle
import cfscrape
from bs4 import BeautifulSoup
from Levenshtein import ratio
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "route_cache.pickle"

DOMAIN = "https://www.8a.nu"

cache = {}

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

    if url in cache:
        return cache[url]

    routes = []
    headers = {
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

    scraper = cfscrape.create_scraper()

    i = 1
    while True:
        purl = url + f"?page={i}"
        response = scraper.get(purl)
        # response = requests.get(purl, headers=headers)
        if response.status_code == 200:
            data = response.content
            if not data:
                break
            soup = BeautifulSoup(data, 'html.parser')
        else:
            raise Exception(f"Could load page {purl}: {response.status_code}")

        table = soup.find("table", class_="main-table zlags-table")
        rows = table.find_all("tr")
        if len(rows) <= 1:
            break

        for r in rows:
            try:
                anchor = r.find(class_="name-link").find("a")
            except AttributeError:
                continue
            
            routes.append((anchor.text.strip(), anchor.get('href')))
            #print(anchor.text.strip(), anchor.get('href'))

        i += 1

    cache[url] = routes
    save_cache()
    return routes
    

def find_route_url(url, name):
    routes = load_list(url)

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
    
    if distances[0][0] > 0.55:
        return DOMAIN + routes[distances[0][1]][1]


if __name__ == "__main__":
    url = "https://www.8a.nu/crags/sportclimbing/montenegro/smokovac/routes"
    print(find_route_url(url, "Svetog Save"))

