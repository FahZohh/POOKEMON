import logging
import random
from typing import Any, Optional

import pymysql
from flask import redirect, url_for, flash

from entity.player import Player
from entity.pokemon import Pokemon
from entity.types import typeChart, Types
from exception import GlobalDatabaseException
from utils import fetchAuthenticatedPlayer, getDbConnection

logger = logging.getLogger(__name__)


# ============================================================================
# Section Combat
# ============================================================================


def chooseTheBestSpeed(pokemon1: Pokemon, pokemon2: Pokemon) -> tuple[Pokemon, Pokemon]:
    """
    Permet de déterminer l'ordre d'attaque des Pokémon en fonction de leur vitesse.
    Si les deux Pokémon ont la même vitesse l'ordre est déterminé aléatoirement.
    """
    if pokemon1.speed > pokemon2.speed:
        first = pokemon1
        last = pokemon2
    elif pokemon2.speed > pokemon1.speed:
        first = pokemon2
        last = pokemon1
    else:
        # si égalité de vitesse, tirage aléatoire
        if random.randint(1, 2) == 1:
            first = pokemon1
            last = pokemon2
        else:
            first = pokemon2
            last = pokemon1
    return first, last


def getCoefficient(attacker: Pokemon, victim: Pokemon) -> float:
    """
    Permet de calculer le coefficient d'efficacité de type entre l'attaquant et la victime.
    """
    coefficient = 1.0

    if attacker.type1 in typeChart:
        # calculer l'efficacité contre le type1 de la victime
        if victim.type1 in typeChart[attacker.type1]:
            coefficient *= typeChart[attacker.type1][victim.type1]

        # calculer l'efficacité contre le type2 de la victime (s'il existe)
        if victim.type2 is not None:
            if victim.type2 in typeChart[attacker.type1]:
                coefficient *= typeChart[attacker.type1][victim.type2]

    return coefficient


def catchPokemon(aiTarget: Pokemon):
    """
    Permet d'ajouter le Pokémon capturé à l'équipe du joueur authentifié.
    """
    player = fetchAuthenticatedPlayer()
    pokemonId = aiTarget.id

    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM team WHERE playerId = %s", (player.id,))
                team = cursor.fetchone()
                teamId = team[0]

                # compte le nombre de Pokémon dans l'équipe pour déterminer la position
                cursor.execute(
                    "SELECT COUNT(*) FROM team_pokemon WHERE teamId = %s",
                    (teamId,),
                )
                position = cursor.fetchone()[0] + 1

                if position >= 6:
                    flash(
                        "Votre équipe est déjà complète, il faut relâcher un pokémon si vous voulez capturer à nouveau.",
                        "error",
                    )
                    return redirect(url_for("fight.battle"))
                else:
                    cursor.execute(
                        """
                        INSERT INTO team_pokemon (teamId, pokemonId, position)
                        VALUES (%s, %s, %s)
                        """,
                        (teamId, pokemonId, position),
                    )
                    cursor.execute(
                        "UPDATE pokemon SET playerId = %s WHERE id = %s",
                        (player.id, pokemonId),
                    )
                    conn.commit()

    except GlobalDatabaseException as e:
        logger.error(f"Database error while capture ai pokemon: {e}")
        flash("Erreur lors de l'ajout du Pokémon.", "error")
        return redirect(url_for("fight.battle"))
    aiTarget.takeDamage(aiTarget.currentHealth + 1)  # met le pokémon KO

    flash(f"Tu as capturé {aiTarget.name} !", "success")
    return redirect(url_for("fight.battle"))


def executeTurn(
    attacker: Pokemon,
    victim: Pokemon,
    action: str,
    newPokemon: Optional[Pokemon] = None,
) -> str:
    """
    Permet d'exécuter un tour de combat en fonction de l'action choisie.
    Cette fonction gère les différentes actions possibles pendant un combat :
    - heal : Soigne le Pokémon attaquant (30% des PV max si < 50% PV, sinon 10%)
    - attack : Attaque l'adversaire en calculant les dégâts avec le coefficient de type
    - swap : Change de Pokémon actif (uniquement pour le joueur)
    - catch : Tente de capturer le Pokémon adverse (30% de chance de succès)
    """
    if action == "heal":
        if attacker.currentHealth == attacker.maxHealth:
            return f"{attacker.name} est déjà à pleine santé !"

        # calculer les points de vie à heal selon la vie actuelle
        if attacker.currentHealth <= attacker.maxHealth * 0.5:
            # soigne 30% des PV max
            healed = int(attacker.maxHealth * 0.3)
        else:
            # soigne seulement 10% des PV max
            healed = int(attacker.maxHealth * 0.1)

        attacker.heal(healed)
        return f"{attacker.name} se soigne de {healed} HP"

    elif action == "attack":
        coefficient = getCoefficient(attacker, victim)

        # calculer les dégâts infligés
        damage = int(attacker.pa * coefficient)

        victim.takeDamage(damage)

        effectMessage = ""
        if coefficient > 1:
            effectMessage = " (Super efficace!)"
        elif coefficient < 1:
            effectMessage = " (Peu efficace...)"

        return f"{attacker.name} attaque {victim.name} et inflige {damage} dégâts{effectMessage}"

    elif action == "swap":
        # verifie qu'un Pokémon de remplacement a été fourni
        if newPokemon is None:
            return "aucun Pokémon sélectionné pour le changement."
        return f"Reviens {attacker.name}! Go {newPokemon.name}!"

    elif action == "catch":
        # tentative de capture avec 30% de chance de succès
        if random.randint(1, 100) <= 30:
            catchPokemon(victim)
            return f"{attacker.name} a capturé {victim.name}!"
        else:
            return f"{attacker.name} a essayé de capturer {victim.name}, mais a échoué."

    return ""


def aiChooseAction(aiPokemon: Pokemon) -> str:
    """
    Permet de déterminer l'action que l'IA doit effectuer pour son Pokémon.

    Stratégie de l'IA :
    - Si le Pokémon a moins de 30% de ses PV max : se soigne
    - Sinon : attaque
    """
    if aiPokemon.currentHealth < aiPokemon.maxHealth * 0.3:
        return "heal"
    else:
        return "attack"


# ============================================================================
# Section : Pokémon de l'utilisateur
# ============================================================================


def getPlayerActivePokemon(playerId: int) -> Optional[Pokemon]:
    """
    Permet de récupèrer le Pokémon actif du joueur (premier dans l'ordre de position).
    Le Pokémon actif est celui en position 1 dans l'équipe.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                        SELECT p.*,
                               s.spriteFace,
                               s.spriteDos,
                               s.spriteChromatiqueFace,
                               s.spriteChromatiqueDos
                        FROM pokemon p
                                 JOIN team_pokemon tp ON p.id = tp.pokemonId
                                 JOIN team t ON tp.teamId = t.id
                                 LEFT JOIN sprites s ON p.id = s.pokemonId
                        WHERE t.playerId = %s
                        ORDER BY tp.position
                        LIMIT 1
                        """
                cursor.execute(query, playerId)
                data = cursor.fetchone()

                if data:
                    return _createPokemonFromData(data)

                return None

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB getPlayerActivePokemon: {e}")
        return None


def playerHasPokemon(playerId: int) -> Optional[bool]:
    """
    Permet de vérifier si le joueur possède au moins un Pokémon dans son équipe.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                # vérifier si le joueur a une équipe
                cursor.execute("SELECT id FROM team WHERE playerId = %s", (playerId,))
                team = cursor.fetchone()

                if not team:
                    return False

                # compter le nombre de Pokémon dans l'équipe
                cursor.execute(
                    "SELECT COUNT(*) FROM team_pokemon WHERE teamId = %s",
                    (team[0],),
                )
                count = cursor.fetchone()[0]
                return count > 0

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB playerHasPokemon: {e}")
        return None


def getPlayerAllPokemons(playerId: int) -> Optional[list[Pokemon]]:
    """
    Permet de récupèrer tous les Pokémon de l'équipe du joueur, ordonnés par position.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                        SELECT p.*,
                               s.spriteFace,
                               s.spriteDos,
                               s.spriteChromatiqueFace,
                               s.spriteChromatiqueDos,
                               tp.position,
                               t.id AS teamId
                        FROM pokemon p
                                 JOIN team_pokemon tp ON p.id = tp.pokemonId
                                 JOIN team t ON tp.teamId = t.id
                                 LEFT JOIN sprites s ON p.id = s.pokemonId
                        WHERE t.playerId = %s
                        ORDER BY tp.position
                        """,
                    (playerId,),
                )
                data = cursor.fetchall()

                # convertir chaque ligne de données en objet Pokemon
                pokemons = []
                for row in data:
                    pokemons.append(_createPokemonFromData(row))
                return pokemons

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB getPlayerAllPokemons: {e}")
        return None


# ============================================================================
# Section : Gestion des Pokémon
# ============================================================================


def getPokemonById(pokemonId: int) -> Optional[Pokemon]:
    """
    Permet de récupèrer un Pokémon spécifique par son identifiant unique.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # LEFT JOIN : même si le Pokémon n'a pas de sprite,
                # la requête retournera quand même le Pokémon avec NULL pour les colonnes sprites
                cursor.execute(
                    """
                        SELECT p.*,
                               s.spriteFace,
                               s.spriteDos,
                               s.spriteChromatiqueFace,
                               s.spriteChromatiqueDos
                        FROM pokemon p
                                 LEFT JOIN sprites s ON p.id = s.pokemonId
                        WHERE p.id = %s
                        """,
                    (pokemonId,),
                )
                data = cursor.fetchone()

                if data:
                    return _createPokemonFromData(data)

                return None

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB getPokemonById: {e}")
        return None


def getRandomWildPokemon() -> Optional[Pokemon]:
    """
    Permet de récuperer vun Pokémon sauvage aléatoire avec une petite chance qu'il soit shiny.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # compte le nombre total de Pokémon sauvages disponibles
                cursor.execute(
                    "SELECT COUNT(*) as count FROM pokemon WHERE playerId IS NULL"
                )
                total = cursor.fetchone()["count"]

                # générer un offset aléatoire pour sélectionner un Pokémon au hasard (sans avoir à charger tous les pokemons)
                offset = random.randint(0, total - 1)

                # récupérer le Pokémon à la position aléatoire avec ses sprites
                cursor.execute(
                    """
                    SELECT p.*,
                           s.spriteFace,
                           s.spriteDos,
                           s.spriteChromatiqueFace,
                           s.spriteChromatiqueDos
                    FROM pokemon p
                             LEFT JOIN sprites s ON p.id = s.pokemonId
                    WHERE p.playerId IS NULL
                    LIMIT 1 OFFSET %s
                    """,
                    (offset,),
                )
                data = cursor.fetchone()

                # chance de 1/200 de rendre le Pokémon shiny
                if random.randint(1, 200) == 1:
                    cursor.execute(
                        "UPDATE pokemon SET isShiny = 1 WHERE id = %s",
                        (data["id"],),
                    )
                    conn.commit()
                    data["isShiny"] = 1

                return _createPokemonFromData(data)

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB getRandomWildPokemon: {e}")
        return None


def updatePokemon(pokemonId: int, pokemonData: dict[str, Any]) -> None:
    """
    Permet de mettre à jour les statistiques d'un Pokémon dans la base de données.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                        UPDATE pokemon
                        SET currentHealth = %s,
                            experience    = %s,
                            level         = %s,
                            powerAttack   = %s,
                            maxHealth     = %s,
                            speed         = %s
                        WHERE id = %s \
                        """
                cursor.execute(
                    query,
                    (
                        pokemonData["currentHealth"],
                        pokemonData["exp"],
                        pokemonData["level"],
                        pokemonData["pa"],
                        pokemonData["maxHealth"],
                        pokemonData["speed"],
                        pokemonId,
                    ),
                )
                conn.commit()

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB updatePokemon: {e}")


def canEvolve(pokemon: Pokemon) -> bool:
    """
    Vérifie si le Pokémon a une évolution et le niveau requis en une seule fois.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                # On récupère le niveau requis parmi les évolutions possibles
                cursor.execute(
                    "SELECT levelRequirement FROM evolution WHERE pokemonId = %s",
                    (pokemon.id,),
                )
                res = cursor.fetchone()
                # Si res[0] est None, pas d'évolution. Sinon on compare au niveau actuel.
                return res[0] is not None and pokemon.level == res[0]
    except Exception as e:
        logger.error(f"Erreur canEvolve: {e}")
        return False


def getEvolutions(pokemon: Pokemon) -> Optional[list[Pokemon]]:
    """
    Permet de récupérer les identifiants des Pokémon vers lesquels le Pokémon peut évoluer.
    """
    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT evolutionId FROM evolution WHERE pokemonId = %s",
                    (pokemon.id,),
                )
                results = cursor.fetchall()
                evolutions = []
                for row in results:
                    evolvesToId = row[0]
                    evolvedPokemon = getPokemonById(evolvesToId)
                    if evolvedPokemon:
                        evolutions.append(evolvedPokemon)
                return evolutions

    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB getEvolution: {e}")
        return None


def evolvePokemon(
    oldPokemonId: int, newPokemonId: int, player: Player
) -> Optional[redirect]:
    """
    Logique compétitive : Transfert de propriété et reset de l'ancien.
    """
    oldPokemon = getPokemonById(oldPokemonId)

    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                # on récupère le status shiny de l'ancien pour l'appliquer au nouveau
                shinyStatus = 1 if oldPokemon.isShiny else 0

                cursor.execute(
                    """UPDATE pokemon
                       SET playerId      = %s,
                           isShiny       = %s,
                           currentHealth = maxHealth
                       WHERE id = %s
                    """,
                    (player.id, shinyStatus, newPokemonId),
                )

                # ancien Pokémon est libéré (devient sauvage et converse ses stats)
                cursor.execute(
                    "UPDATE pokemon SET playerId = NULL, isShiny = 0, level = 1, experience = 0 WHERE id = %s",
                    (oldPokemonId,),
                )

                # mise à jour de la Team
                cursor.execute("SELECT id FROM team WHERE playerId = %s", (player.id,))
                teamId = cursor.fetchone()[0]
                if teamId:
                    cursor.execute(
                        "UPDATE team_pokemon SET pokemonId = %s WHERE pokemonId = %s AND teamId = %s",
                        (newPokemonId, oldPokemonId, teamId),
                    )

                conn.commit()
                flash(
                    f"Evolution réussie ! Vous avez libéré {oldPokemon.name}.",
                    "success",
                )
                return redirect(url_for("userMenu.inventoryPokemons"))

    except GlobalDatabaseException as e:
        logger.error(f"Erreur lors de l'évolution : {e}")
        flash("Un problème est survenu lors de l'évolution.", "error")
        return redirect(url_for("userMenu.inventoryPokemons"))


# ============================================================================
# Fonctions privées / Utilitaires
# ============================================================================


def _createPokemonFromData(data: dict[str, Any]) -> Pokemon:
    """
    Permet de convertir les données de la base de données en objet Pokemon

    Cette fonction est privée (préfixe _) et DOIT ETRE UTILISÉE UNIQUEMENT ICI.
    """
    type1 = Types(data["type1"]) if data.get("type1") else None
    type2 = Types(data["type2"]) if data.get("type2") else None

    pokemon = Pokemon(
        id=data["id"],
        name=data["name"],
        pa=data["powerAttack"],
        maxHealth=data["maxHealth"],
        speed=data["speed"],
        level=data["level"],
        spriteFace=data["spriteFace"],
        spriteDos=data["spriteDos"],
        spriteChromatiqueFace=data["spriteChromatiqueFace"],
        spriteChromatiqueDos=data["spriteChromatiqueDos"],
        exp=data["experience"],
        type1=type1,
        type2=type2,
        isShiny=data.get("isShiny"),
    )

    pokemon.currentHealth = data["currentHealth"]

    # met les attributs d'équipe si présents (optionnels)
    pokemon.teamId = data.get("teamId")
    pokemon.position = data.get("position")

    return pokemon
