#!/usr/bin/env python3
import logging
import os
import time

import schedule

from scraper import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

START_HOUR = int(os.environ.get("SCHEDULE_START", "7"))
END_HOUR   = int(os.environ.get("SCHEDULE_END",   "19"))
INTERVAL   = int(os.environ.get("SCHEDULE_INTERVAL_HOURS", "2"))


def job():
    log.info("=== Lancement du scraper ===")
    try:
        run()
    except Exception as e:
        log.exception("Erreur inattendue : %s", e)
    log.info("=== Scraper terminé ===")


def job_if_in_range():
    current_hour = time.localtime().tm_hour
    if START_HOUR <= current_hour <= END_HOUR:
        job()
    else:
        log.info("Hors plage horaire (%dh-%dh), scraping ignoré.", START_HOUR, END_HOUR)


if __name__ == "__main__":
    log.info(
        "Planificateur démarré — toutes les %dh entre %dh et %dh",
        INTERVAL, START_HOUR, END_HOUR,
    )

    schedule.every(INTERVAL).hours.do(job_if_in_range)

    # Lancement immédiat au démarrage si dans la plage
    log.info("Lancement initial au démarrage…")
    job_if_in_range()

    while True:
        schedule.run_pending()
        time.sleep(30)