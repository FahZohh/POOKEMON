import logging
import threading
from dataclasses import replace

import pymysql

from entity.player import Player
from exception import GlobalDatabaseException, PlayerMemoryException

playersMemory = {}
playersThreadLock = threading.Lock()

logger = logging.getLogger(__name__)


def loadPlayersInMemory():
    """
    Charge tous les joueurs de la base de données en mémoire.
    U N I Q U E M E N T appelé au démarrage de l'application.
    """
    from utils import getDbConnection

    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, username, email, wins, losses FROM player")
                playersList = cursor.fetchall()
    except GlobalDatabaseException as e:
        logger.error(
            "Échec du chargement des membres depuis la DB : %s", e, exc_info=True
        )
        return

    for player in playersList:
        try:
            addPlayerInMemory(
                Player(
                    id=player["id"],
                    username=player["username"],
                    email=player["email"],
                    wins=player["wins"],
                    losses=player["losses"],
                )
            )
        except PlayerMemoryException as e:
            logger.error("Erreur conversion ligne en joueur : %s", e, exc_info=True)


def addPlayerInMemory(player: Player) -> None:
    """Ajoute ou met à jour un joueur en mémoire (thread-safe)."""
    try:
        with playersThreadLock:
            playersMemory[player.id] = player
    except Exception as e:
        logger.error(
            "Erreur lors de l'ajout/mise à jour du joueur en mémoire : %s",
            e,
            exc_info=True,
        )
        raise PlayerMemoryException(
            f"Erreur lors de l'ajout/mise à jour du joueur en mémoire : {e}"
        )


def getPlayerFromMemory(playerId: int) -> Player:
    """Récupère un joueur en mémoire ou lève une exception s'il n'existe pas."""
    with playersThreadLock:
        player = playersMemory.get(playerId)
        if player is None:
            logger.error("Le joueur avec l'ID %d n'existe pas en mémoire.", playerId)
            raise PlayerMemoryException(
                f"Le joueur avec l'ID {playerId} n'existe pas en mémoire."
            )
    return player


def getAllPlayersFromMemory():
    """Récupère tous les joueurs de la mémoire (thread-safe)"""
    with playersThreadLock:
        players = list(playersMemory.values())
    return players


def removePlayerFromMemory(playerId: int):
    """Supprime un joueur de la mémoire (thread-safe)"""
    with playersThreadLock:
        playersMemory.pop(playerId, None)


def updatePlayerInMemory(playerId: int, username: str, email: str) -> None:
    """Met à jour un joueur en mémoire de manière thread-safe (immutable)."""
    player = getPlayerFromMemory(playerId)
    with playersThreadLock:
        playersMemory[playerId] = replace(player, username=username, email=email)


def addWinToPlayer(playerId: int, wins: int) -> None:
    """Ajoute un nombre de victoires à un joueur en mémoire (thread-safe)."""
    player = getPlayerFromMemory(playerId)
    with playersThreadLock:
        playersMemory[playerId] = replace(player, wins=player.wins + wins)


def addLossToPlayer(playerId: int, losses: int) -> None:
    """Ajoute un nombre de défaites à un joueur en mémoire (thread-safe)."""
    player = getPlayerFromMemory(playerId)
    with playersThreadLock:
        playersMemory[playerId] = replace(player, losses=player.losses + losses)
