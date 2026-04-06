#!/usr/bin/env python3
"""
Planificateur — lance scraper.run() selon SCHEDULE_MORNING et SCHEDULE_EVENING.
Tourne en boucle infinie (point d'entrée du conteneur Docker).
"""

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

MORNING = os.environ.get("SCHEDULE_MORNING", "10:00")
EVENING = os.environ.get("SCHEDULE_EVENING", "19:00")


def job():
    log.info("=== Lancement du scraper ===")
    try:
        run()
    except Exception as e:
        log.exception("Erreur inattendue : %s", e)
    log.info("=== Scraper terminé ===")


if __name__ == "__main__":
    log.info("Planificateur démarré — horaires : %s et %s", MORNING, EVENING)

    schedule.every().day.at(MORNING).do(job)
    schedule.every().day.at(EVENING).do(job)

    # Lancement immédiat au démarrage du conteneur
    log.info("Lancement initial au démarrage…")
    job()

    while True:
        schedule.run_pending()
        time.sleep(30)
