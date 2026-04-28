# 🦊 CorrezeBoostEmploi — Scraper Discord

Surveille automatiquement les offres **CDI/CDD** publiées dans la semaine sur [correzeboostemploi.fr](https://www.correzeboostemploi.fr) et envoie chaque nouvelle offre dans un salon Discord.

---

## Fonctionnement

- Scrape les offres toutes les 2h entre 7h et 19h par défaut (soit 7 passages/jour)
- Mémorise les offres déjà envoyées → **aucun doublon** entre les lancements
- Filtre les offres contenant des mots bannis (titre ou nom d'entreprise)
- Un message Discord par offre, avec titre, entreprise, ville, contrat, salaire et lien

<div align="center">
  <img src="https://i.imgur.com/D743soX.png" alt="Aperçu Discord" />
</div>

---

## Démarrage rapide

### 1. Créer le webhook Discord

1. Ouvre le salon Discord où tu veux recevoir les offres
2. **Paramètres du salon → Intégrations → Webhooks → Nouveau webhook**
3. Copie l'URL générée

### 2. Configurer les variables dans le compose

Édite `docker-compose.yml` et remplis les valeurs dans le bloc `environment` :

```yaml
environment:
  DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/..."
  BANNED_KEYWORDS: "comptable,ménage,cuisine,cuisinier,plongeur"
  SCHEDULE_START: "7"
  SCHEDULE_END: "19"
  SCHEDULE_INTERVAL_HOURS: "2"
  MAX_PAGES: "10"
```

### 3. Lancer avec Docker Compose

```bash
docker compose up -d
```

Les offres déjà vues sont persistées dans un volume monté sur l'hôte.

---

## Variables d'environnement

| Variable                   | Obligatoire | Défaut   | Description                                              |
|----------------------------|-------------|----------|----------------------------------------------------------|
| `DISCORD_WEBHOOK_URL`      | ✅           | —        | URL du webhook Discord                                   |
| `BANNED_KEYWORDS`          | ❌           | _(vide)_ | Mots à bannir, séparés par des virgules                  |
| `SCHEDULE_START`           | ❌           | `7`      | Heure de début de la plage de scraping (entier, 0–23)    |
| `SCHEDULE_END`             | ❌           | `19`     | Heure de fin de la plage de scraping (entier, 0–23)      |
| `SCHEDULE_INTERVAL_HOURS`  | ❌           | `2`      | Intervalle en heures entre chaque scraping               |
| `MAX_PAGES`                | ❌           | `10`     | Nombre max de pages à scraper (15 offres/page)           |

> Avec les valeurs par défaut, le scraper tourne à : **7h, 9h, 11h, 13h, 15h, 17h et 19h**.  
> Un lancement immédiat est aussi effectué au démarrage du conteneur (si dans la plage horaire).

---

## Commandes utiles

```bash
# Démarrer en arrière-plan
docker compose up -d

# Voir les logs en direct
docker compose logs -f

# Lancer un scraping immédiat (sans attendre l'horaire)
docker compose exec scraper python scraper.py

# Arrêter
docker compose down

# Arrêter et supprimer les données persistées
docker compose down -v
```

---

## Build local

```bash
# Build amd64
docker build -t correzeboostemploi .

# Lancer avec les variables inline
docker run -d \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." \
  -e BANNED_KEYWORDS="comptable,ménage" \
  -e SCHEDULE_START="7" \
  -e SCHEDULE_END="19" \
  -e SCHEDULE_INTERVAL_HOURS="2" \
  -v /home/aerya/docker/correzeboostemploi:/data \
  correzeboostemploi
```

---

## Image Docker pré-buildée

L'image **amd64** est automatiquement buildée et publiée sur GitHub Container Registry à chaque push sur `main`.

L'image **arm64** est buildée uniquement sur les tags ou via un déclenchement manuel (`workflow_dispatch`).

```bash
docker pull ghcr.io/aerya/correzeboostemploi:latest
```

---

## Structure du projet

```
.
├── scraper.py          # Logique de scraping et envoi Discord
├── scheduler.py        # Planificateur (point d'entrée Docker)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/
        └── docker.yml  # CI/CD — build et push GHCR
```

---

## Licence

MIT
