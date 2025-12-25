import argparse
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


# ---------------- INPUT ----------------
def get_urls():
    parser = argparse.ArgumentParser(description="Module Extraction Tool")
    parser.add_argument("--urls", nargs="+", required=True)
    return parser.parse_args().urls


# ---------------- FETCHING ----------------
def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc != ""


def fetch_page(url):
    if not is_valid_url(url):
        return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except:
        return None


# ---------------- CRAWLING ----------------
def extract_internal_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag["href"])
        if urlparse(full_url).netloc == base_domain:
            links.add(full_url)

    return links


def crawl_website(start_url, max_pages=5):
    visited = set()
    to_visit = [start_url]

    while to_visit and len(visited) < max_pages:
        current = to_visit.pop(0)
        if current in visited:
            continue

        html = fetch_page(current)
        if not html:
            continue

        print("Crawled:", current)
        visited.add(current)

        for link in extract_internal_links(start_url, html):
            if link not in visited and link not in to_visit:
                to_visit.append(link)

    return visited


# ---------------- MODULE EXTRACTION ----------------
def extract_modules_and_submodules(html):
    soup = BeautifulSoup(html, "html.parser")

    modules = {}
    current_module = None

    for tag in soup.find_all(["h1", "h2"]):
        text = tag.get_text(strip=True)

        if tag.name == "h1":
            current_module = text
            modules[current_module] = []
        elif tag.name == "h2" and current_module:
            modules[current_module].append(text)

    return modules


# ---------------- JSON FORMAT ----------------
def build_final_json(all_modules):
    result = []

    for module, submodules in all_modules.items():
        module_entry = {
            "module": module,
            "Description": f"Documentation related to {module}.",
            "Submodules": {}
        }

        for sub in submodules:
            module_entry["Submodules"][sub] = f"Details about {sub}."

        result.append(module_entry)

    return result


# ---------------- MAIN ----------------
if __name__ == "__main__":
    urls = get_urls()

    for url in urls:
        print("\nStarting crawl for:", url)
        pages = crawl_website(url)

        combined_modules = {}

        for page_url in pages:
            html = fetch_page(page_url)
            if not html:
                continue

            modules = extract_modules_and_submodules(html)

            for mod, subs in modules.items():
                if mod not in combined_modules:
                    combined_modules[mod] = set()
                combined_modules[mod].update(subs)

        combined_modules = {k: list(v) for k, v in combined_modules.items()}

        final_json = build_final_json(combined_modules)

        print("\nFINAL JSON OUTPUT:\n")
        print(json.dumps(final_json, indent=2))
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2)
