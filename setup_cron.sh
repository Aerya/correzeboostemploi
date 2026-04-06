#!/bin/bash
# setup_cron.sh — Installe les crons pour CorrezeBoostEmploi
# Usage : bash setup_cron.sh

set -e

# Option --remove : supprime les crons
if [ "${1:-}" = "--remove" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    CURRENT_CRON=$(crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR/scraper.py" || true)
    echo "$CURRENT_CRON" | crontab -
    echo "Crons supprimés."
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3)"
SCRIPT="$SCRIPT_DIR/scraper.py"
LOG="$SCRIPT_DIR/scraper.log"

if [ -z "$PYTHON" ]; then
    echo "Erreur : python3 introuvable. Installe-le avec : sudo apt install python3"
    exit 1
fi

echo "Répertoire du script : $SCRIPT_DIR"
echo "Python utilisé       : $PYTHON"
echo "Log                  : $LOG"
echo ""

# Installe les dépendances Python si besoin
echo "Vérification des dépendances Python..."
$PYTHON -m pip install --quiet requests beautifulsoup4

# Lignes cron à ajouter
CRON_10H="0 10 * * * $PYTHON $SCRIPT >> $LOG 2>&1"
CRON_19H="0 19 * * * $PYTHON $SCRIPT >> $LOG 2>&1"

# Récupère le crontab actuel et supprime les éventuelles anciennes entrées
CURRENT_CRON=$(crontab -l 2>/dev/null | grep -v "$SCRIPT" || true)

# Ajoute les nouvelles entrées
NEW_CRON=$(printf "%s\n%s\n%s\n" "$CURRENT_CRON" "$CRON_10H" "$CRON_19H")
echo "$NEW_CRON" | crontab -

echo ""
echo "Crons installés avec succès !"
echo ""
crontab -l | grep "$SCRIPT"
echo ""
echo "Les logs seront dans : $LOG"
echo ""
echo "Commandes utiles :"
echo "  Voir les crons actifs  : crontab -l"
echo "  Supprimer les crons    : bash $SCRIPT_DIR/setup_cron.sh --remove"
echo "  Voir les logs          : tail -f $LOG"
echo "  Tester maintenant      : $PYTHON $SCRIPT"
