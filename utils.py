import logging
import os
import re
import string
from typing import Optional

import pymysql
from flask import session
from dotenv import load_dotenv

from entity.customConnection import CustomConnection
from entity.player import Player
from exception import GlobalDatabaseException

# charger les variables d'environnement depuis le fichier .env
load_dotenv()

# configurer le logger
logger = logging.getLogger(__name__)

# configuration de la base de données MySQL à partir des variables d'environnement
dbConfig = {
    "host": os.environ.get("MYSQL_HOST"),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "database": os.environ.get("MYSQL_DB"),
}


"""
Séction Utilisateur
"""


def isValidEmail(email):
    """Vérifie si l'email est valide."""
    # - ^[a-zA-Z0-9._%+-]+ : commence par des lettres minuscules ou maj, ou chiffres ou . _ % + -
    # - @ : doit contenir un arobase
    # - [a-zA-Z0-9.-]+ : nom de domaine avec lettres, chiffres, points ou tirets
    # - \. : point obligatoire avant l'extension
    # - [a-zA-Z]{2,}$ : se termine par au moins 2 lettres (com, fr, org, etc.)
    emailRegex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    # Retourne True si l'email correspond au motif, False sinon
    return re.match(emailRegex, email) is not None


def usernameExist(username):
    """
    Vérifie si un pseudo existe déjà dans la base de données.
    """
    conn = getDbConnection()
    with conn.cursor() as cur:
        query = "SELECT COUNT(*) FROM player WHERE username = %s"
        cur.execute(query, (username,))
        return cur.fetchone()[0] > 0


def emailExist(email):
    """
    Vérifie si un email existe déjà dans la base de données.
    """
    conn = getDbConnection()
    with conn.cursor() as cur:
        query = "SELECT COUNT(*) FROM player WHERE email = %s"
        cur.execute(query, (email,))
        return cur.fetchone()[0] > 0


def validatePassword(password: str) -> Optional[str]:
    """Permet de valider le mot de passe selon les critères définis."""
    if len(password) < 12:
        return "Le mot de passe doit contenir au moins 12 caractères."
    if not any(c.isdigit() for c in password):
        return "Le mot de passe doit contenir au moins un chiffre."
    if not any(c.isupper() for c in password):
        return "Le mot de passe doit contenir au moins une majuscule."
    if not any(c.islower() for c in password):
        return "Le mot de passe doit contenir au moins une minuscule."
    if not any(c in string.punctuation for c in password):
        return "Le mot de passe doit contenir au moins un caractère spécial."
    return None


def fetchAuthenticatedPlayer() -> Optional[Player]:
    """
    Retourne le joueur connecté ou None si absent/incohérent.
    Peut également vider la session si le membre n'est pas trouvé en mémoire.
    """
    if "id" not in session:
        return None

    from memory.player import getPlayerFromMemory

    player = getPlayerFromMemory(getInternalId())
    if player is None:
        logger.error("Player not found.")
        clearInternalSession()
        return None

    return player


def registerInternalId(sessionId: int) -> None:
    """Enregistre l'ID de l'utilisateur dans la session."""
    session["id"] = sessionId


def getInternalId() -> int:
    """Retourne l'ID de l'utilisateur connecté."""
    return session.get("id")


def clearInternalSession() -> None:
    """Vide la session de l'utilisateur."""
    session.clear()


def getDbConnection():
    """
    Retourne une connexion custom à la base de données MySQL
    La connexion custom permet de gérer les erreurs avec des erreurs personnalisées.
    """
    try:
        return CustomConnection(pymysql.connect(**dbConfig, autocommit=False))
    except pymysql.MySQLError as e:
        raise GlobalDatabaseException(
            f"Impossible de se connecter à la base de données MySQL : {e}"
        )
