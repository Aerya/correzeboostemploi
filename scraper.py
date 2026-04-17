#!/usr/bin/env python3
"""
CorrezeBoostEmploi — Scraper d'offres d'emploi avec notification Discord.
Configuration par variables d'environnement (voir .env.example).
"""

import json
import logging
import os
import sys
import time

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — variables d'environnement
# ---------------------------------------------------------------------------
BASE_URL    = "https://www.correzeboostemploi.fr"
SEARCH_URL  = (
    "https://www.correzeboostemploi.fr/offres"
    "?what%5Btype%5D=&what%5Bsearch%5D="
    "&where%5Bsearch%5D=Corr%C3%A8ze"
    "&where%5Bperimeter%5D="
    "&where%5Bdepartements%5D%5B0%5D=Correze-departement"
    "&contractTypes%5B%5D=CDI"
    "&contractTypes%5B%5D=CDD"
    "&publicationDateRange=OneWeek"
)

def get_config():
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        log.error("Variable DISCORD_WEBHOOK_URL manquante.")
        sys.exit(1)

    raw_banned = os.environ.get("BANNED_KEYWORDS", "")
    banned = [k.strip() for k in raw_banned.split(",") if k.strip()]

    max_pages = int(os.environ.get("MAX_PAGES", "10"))

    data_dir = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
    seen_file = os.path.join(data_dir, "seen_offers.json")

    return {
        "webhook":    webhook,
        "banned":     banned,
        "max_pages":  max_pages,
        "seen_file":  seen_file,
    }

# ---------------------------------------------------------------------------
# Persistance des offres déjà vues
# ---------------------------------------------------------------------------
def load_seen(path: str) -> set:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(path: str, seen: set) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def fetch_page(url: str, retries: int = 3) -> str | None:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            log.warning("Fetch échoué (%d/%d) : %s", attempt, retries, e)
            if attempt < retries:
                time.sleep(2)
    return None

def parse_offers(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    offers = []
    for link in soup.find_all("a", attrs={"data-testid": "offer-link"}):
        href = link.get("href", "")
        if not href.startswith("/offre/"):
            continue
        offer_id = href.rsplit("/", 1)[-1]
        url      = BASE_URL + href
        title    = link.get_text(strip=True)
        company = location = contract = salary = date = ""
        try:
            gtm     = json.loads(link.get("data-gtm-product-click-param", "{}"))
            product = gtm.get("product_data", [{}])[0]
            title    = product.get("product",          title)
            company  = product.get("product_company")  or ""
            location = product.get("product_city")     or ""
            contract = product.get("product_contract") or ""
            date     = product.get("product_date")     or ""
            sal      = product.get("product_salary")
            if sal:
                salary = f"{int(sal):,} €/an".replace(",", " ")
        except (json.JSONDecodeError, IndexError, KeyError, ValueError):
            pass
        offers.append({
            "id": offer_id, "title": title, "company": company,
            "location": location, "contract": contract,
            "salary": salary, "date": date, "url": url,
        })
    return offers

def has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return bool(soup.find("a", string=lambda t: t and "Suivant" in t))

# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------
def send_discord(webhook_url: str, offer: dict) -> bool:
    parts = [f"**{offer['title']}**"]
    if offer.get("company"):  parts.append(f"Entreprise : {offer['company']}")
    if offer.get("location"): parts.append(f"Lieu       : {offer['location']}")
    if offer.get("contract"): parts.append(f"Contrat    : {offer['contract']}")
    if offer.get("salary"):   parts.append(f"Salaire    : {offer['salary']}")
    if offer.get("date"):     parts.append(f"Publiée le : {offer['date']}")
    parts.append(f"Lien : {offer['url']}")
    try:
        r = requests.post(webhook_url, json={"content": "\n".join(parts)}, timeout=10)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        log.error("Erreur Discord : %s", e)
        return False

# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------
def run() -> None:
    cfg = get_config()
    seen = load_seen(cfg["seen_file"])

    log.info("Démarrage de la recherche — mots bannis : %s",
             ", ".join(cfg["banned"]) if cfg["banned"] else "(aucun)")

    new_count = banned_count = already_seen_count = 0
    page = 1

    try:
        while page <= cfg["max_pages"]:
            url = SEARCH_URL if page == 1 else f"{SEARCH_URL}&page={page}"
            log.info("Scraping page %d …", page)

            html = fetch_page(url)
            if not html:
                log.error("Impossible de récupérer la page %d, arrêt.", page)
                break

            offers = parse_offers(html)
            log.info("  %d offre(s) sur cette page.", len(offers))
            if not offers:
                break

            for offer in offers:
                if offer["id"] in seen:
                    already_seen_count += 1
                    continue
                seen.add(offer["id"])

                title_lower   = (offer["title"]   or "").lower()
                company_lower = (offer["company"] or "").lower()
                if any(kw.lower() in title_lower or kw.lower() in company_lower
                       for kw in cfg["banned"]):
                    log.info("  [FILTRE]  %s", offer["title"])
                    banned_count += 1
                    continue

                log.info("  [ENVOI]   %s — %s (%s)", offer["title"], offer["company"], offer["location"])
                send_discord(cfg["webhook"], offer)
                new_count += 1
                time.sleep(0.5)

            if not has_next_page(html):
                break
            page += 1
            time.sleep(1)
    finally:
        save_seen(cfg["seen_file"], seen)

    log.info(
        "Terminé : %d envoyée(s), %d filtrée(s), %d déjà vue(s).",
        new_count, banned_count, already_seen_count,
    )

if __name__ == "__main__":
    run()
