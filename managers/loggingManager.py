import logging
import os

# Crée le dossier logs s'il n'existe pas
if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)


def setupLogging():
    """Configure le système de logs global."""
    logging.basicConfig(
        level=logging.INFO,  # Niveau minimal enregistré
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
