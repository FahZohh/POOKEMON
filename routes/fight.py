import logging

import pymysql
from flask import request, render_template, session, redirect, url_for, flash, Blueprint

from entity.pokemon import Pokemon
from exception import GlobalDatabaseException, PlayerMemoryException
from memory.player import addWinToPlayer, addLossToPlayer
from pokeUtils import (
    playerHasPokemon,
    getPlayerActivePokemon,
    getRandomWildPokemon,
    chooseTheBestSpeed,
    getPlayerAllPokemons,
    getPokemonById,
    executeTurn,
    aiChooseAction,
    updatePokemon,
    canEvolve,
)
from utils import (
    getDbConnection,
    fetchAuthenticatedPlayer,
)

fight = Blueprint("fight", __name__)

logger = logging.getLogger(__name__)


@fight.route("/battle/start")
def battleStart():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    playerId = player.id

    if not playerHasPokemon(playerId):
        flash("Vous n'avez pas de Pokémon", "error")
        return redirect(url_for("userMenu.chooseFirstPokemon"))

    playerPokemon = getPlayerActivePokemon(playerId)
    aiPokemon = getRandomWildPokemon()

    playerPokemon.currentHealth = playerPokemon.maxHealth
    aiPokemon.currentHealth = aiPokemon.maxHealth

    # le _ sert à ignorer la deuxième valeur de retour
    first, _ = chooseTheBestSpeed(playerPokemon, aiPokemon)

    session["playerPokemon"] = playerPokemon.toDict()
    session["aiPokemon"] = aiPokemon.toDict()
    session["battleActive"] = True
    session["battleLog"] = []
    session["turn"] = 1
    session["forceSwap"] = False
    session["phase"] = "player" if first == playerPokemon else "ai"

    flash(f"{first.name} commence le combat !", "info")
    return redirect(url_for("fight.battle"))


@fight.route("/battle")
def battle():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    if not session.get("battleActive"):
        return redirect(url_for("fight.battleStart"))

    playerPokemons = getPlayerAllPokemons(player.id)

    return render_template(
        "battle.html",
        player=session.get("playerPokemon"),
        ai=session.get("aiPokemon"),
        battleLog=session.get("battleLog", []),
        turn=session.get("turn", 1),
        battleActive=session.get("battleActive"),
        phase=session.get("phase"),
        playerPokemons=playerPokemons,
        forceSwap=session.get("forceSwap", False),
    )


@fight.route("/battle/action", methods=["POST"])
def battleAction():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    if not session.get("battleActive"):
        flash("Aucun combat actif", "error")
        return redirect(url_for("fight.battleStart"))

    playerId = player.id
    playerAction = request.form.get("action")
    playerPokemon = Pokemon.fromDict(session["playerPokemon"])
    aiPokemon = Pokemon.fromDict(session["aiPokemon"])
    battleLog = session.get("battleLog", [])
    phase = session.get("phase")

    # variable pour tracker le Pokémon qui attaque réellement (pour l'XP)
    attackingPokemon = playerPokemon

    if phase == "player" and playerAction in ["attack", "heal", "catch", "swap"]:
        if playerAction == "swap":
            swapPokemonId = request.form.get("swapPokemonId")
            if not swapPokemonId:
                flash("Veuillez sélectionner un Pokémon.", "error")
                return redirect(url_for("fight.battle"))

            try:
                with getDbConnection() as conn:
                    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                        cursor.execute(
                            "SELECT id FROM team WHERE playerId = %s", (playerId,)
                        )
                        team = cursor.fetchone()
                        if not team:
                            flash("Vous n'avez pas d'équipe.", "error")
                            return redirect(url_for("fight.battle"))

                        teamId = team["id"]

                        # vérifie que le nouveau pokémon appartient à cette team et récupérer les positions
                        cursor.execute(
                            """
                            SELECT pokemonId, position
                            FROM team_pokemon
                            WHERE pokemonId IN (%s, %s) AND teamId = %s
                            """,
                            (swapPokemonId, playerPokemon.id, teamId),
                        )
                        results = cursor.fetchall()

                        if len(results) != 2:
                            flash("Ce Pokémon ne vous appartient pas.", "error")
                            return redirect(url_for("fight.battle"))

                        # identifier les positions
                        positions = {
                            row["pokemonId"]: row["position"] for row in results
                        }
                        oldPokemonPosition = positions[playerPokemon.id]
                        newPokemonPosition = positions[int(swapPokemonId)]

                        # echanger les positions (avec position temporaire)
                        tempPosition = 7
                        cursor.execute(
                            "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s AND teamId = %s",
                            (tempPosition, playerPokemon.id, teamId),
                        )
                        cursor.execute(
                            "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s AND teamId = %s",
                            (oldPokemonPosition, int(swapPokemonId), teamId),
                        )
                        cursor.execute(
                            "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s AND teamId = %s",
                            (newPokemonPosition, playerPokemon.id, teamId),
                        )
                        conn.commit()

            except GlobalDatabaseException as e:
                logger.error(f"Erreur lors du swap en combat: {e}")
                flash("Erreur lors du changement de Pokémon.", "error")
                return redirect(url_for("fight.battle"))

            newPokemon = getPokemonById(int(swapPokemonId))

            if newPokemon.id == playerPokemon.id:
                flash("Ce Pokémon est déjà en combat !", "error")
                return redirect(url_for("fight.battle"))

            if newPokemon.isKO():
                flash("Ce Pokémon est KO !", "error")
                return redirect(url_for("fight.battle"))

            message = executeTurn(playerPokemon, aiPokemon, "swap", newPokemon)
            battleLog.append(message)
            flash(message, "success")

            # sauvegarder l'ancien Pokémon avec son état actuel AVANT le swap
            updatePokemon(playerPokemon.id, playerPokemon.toDict())
            playerPokemon = newPokemon
            session["playerPokemon"] = playerPokemon.toDict()
            session["forceSwap"] = False  # réinitialiser forceSwap après le changement

        else:
            attackingPokemon = playerPokemon
            message = executeTurn(playerPokemon, aiPokemon, playerAction)
            battleLog.append(message)
            flash(message, "success")

        if aiPokemon.isKO():
            # enleve le caractère shiny du pokemon sauvage
            try:
                with getDbConnection() as conn:
                    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                        cursor.execute(
                            "SELECT playerId FROM pokemon WHERE id = %s",
                            (aiPokemon.id,),
                        )
                        checkCapture = cursor.fetchone()

                        # Si playerId est NULL, ça veut dire qu'il est mort sauvage -> on enlève le shiny
                        if checkCapture and checkCapture["playerId"] is None:
                            cursor.execute(
                                "UPDATE pokemon SET isShiny = 0 WHERE id = %s",
                                (aiPokemon.id,),
                            )

                        cursor.execute(
                            "UPDATE player SET wins = wins + 1 WHERE id = %s",
                            (playerId,),
                        )
                        conn.commit()

            except GlobalDatabaseException as e:
                logger.error(f"Erreur lors du changement en pokemon normal: {e}")
                flash("Erreur, veuillez contacter un admin.", "error")
                return redirect(url_for("fight.battle"))

            try:
                addWinToPlayer(playerId, 1)
            except PlayerMemoryException as e:
                logger.error(f"Erreur lors de l'ajout de la victoire en mémoire: {e}")
                flash("Erreur, veuillez contacter un admin.", "error")
                return redirect(url_for("fight.battle"))

            baseXp = 20 + 2 * aiPokemon.level
            xpRatio = aiPokemon.level / max(1, attackingPokemon.level)
            finalXp = int(baseXp * xpRatio)
            attackingPokemon.gainExp(finalXp)

            battleLog.append(
                f"{attackingPokemon.name} a gagné le combat ! +{finalXp} XP"
            )
            flash(f"Victoire ! +{finalXp} XP", "winner")

            # sauvegarder le Pokémon vainqueur (celui qui a attaqué) avec ses XP et sa santé actuelle
            updatePokemon(attackingPokemon.id, attackingPokemon.toDict())

            # si le Pokémon vainqueur est différent du Pokémon actuel, sauvegarder aussi le Pokémon actuel
            if playerPokemon.id != attackingPokemon.id:
                updatePokemon(playerPokemon.id, playerPokemon.toDict())

            session["battleActive"] = False
            session["forceSwap"] = False

        else:
            session["phase"] = "ai"

    elif phase == "ai" and playerAction == "aiTurn":
        aiAction = aiChooseAction(aiPokemon)
        message = executeTurn(aiPokemon, playerPokemon, aiAction)
        battleLog.append(message)
        flash(message, "danger")

        if playerPokemon.isKO():
            battleLog.append(f"{playerPokemon.name} est KO !")

            # sauvegarder le Pokémon KO avec 0 HP en base de données
            updatePokemon(playerPokemon.id, playerPokemon.toDict())

            # vérifier s'il reste des Pokémon vivants
            playerPokemons = getPlayerAllPokemons(playerId)
            alivePokemons = []
            for poke in playerPokemons:
                if not poke.isKO() and poke.id != playerPokemon.id:
                    alivePokemons.append(poke)

            if alivePokemons:
                flash(
                    f"{playerPokemon.name} est KO ! Choisissez un autre Pokémon.",
                    "warning",
                )
                session["playerPokemon"] = playerPokemon.toDict()
                session["aiPokemon"] = aiPokemon.toDict()
                session["battleLog"] = battleLog
                session["forceSwap"] = True
                session["phase"] = (
                    "player"  # remettre en phase joueur pour permettre le swap
                )
                return redirect(url_for("fight.battle"))
            else:
                # plus de Pokémon vivants, défaite
                try:
                    with getDbConnection() as conn:
                        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                            cursor.execute(
                                "UPDATE player SET losses = losses + 1 WHERE id = %s",
                                (playerId,),
                            )
                            cursor.execute(
                                "UPDATE pokemon SET isShiny = 0 WHERE id = %s ",
                                (aiPokemon.id,),
                            )
                            conn.commit()

                except GlobalDatabaseException as e:
                    logger.error(f"Erreur lors du changement en pokemon normal: {e}")
                    flash("Erreur, veuillez contacter un admin.", "error")
                    return redirect(url_for("fight.battle"))

                try:
                    addLossToPlayer(playerId, 1)
                except PlayerMemoryException as e:
                    logger.error(
                        f"Erreur lors de l'ajout de la défaite en mémoire: {e}"
                    )
                    flash("Erreur, veuillez contacter un admin.", "error")
                    return redirect(url_for("fight.battle"))

                battleLog.append(f"{aiPokemon.name} a gagné le combat !")
                flash("Tous vos Pokémon sont KO ! Allez les soigner.", "loser")
                session["battleActive"] = False
                session["forceSwap"] = False
                session["playerPokemon"] = playerPokemon.toDict()
                session["aiPokemon"] = aiPokemon.toDict()
                session["battleLog"] = battleLog
                return redirect(url_for("userMenu.inventoryPokemons"))
        else:
            session["phase"] = "player"
            session["turn"] += 1

    else:
        flash("Action invalide ou ce n'est pas votre tour", "error")

    # gérer le level up du Pokémon qui a attaqué (qui a reçu l'XP)
    if attackingPokemon.id:
        while attackingPokemon.canLevelUp():
            attackingPokemon.levelUp()
            flash(
                f"{attackingPokemon.name} est monté au niveau {attackingPokemon.level} !",
                "info",
            )
        updatePokemon(attackingPokemon.id, attackingPokemon.toDict())

    # si le pokémon actuel est différent de celui qui a attaqué, le sauvegarder aussi
    if playerPokemon.id and playerPokemon.id != attackingPokemon.id:
        updatePokemon(playerPokemon.id, playerPokemon.toDict())

    if canEvolve(attackingPokemon):
        return redirect(url_for("userMenu.evolvePokemon"))

    session["playerPokemon"] = playerPokemon.toDict()
    session["aiPokemon"] = aiPokemon.toDict()
    session["battleLog"] = battleLog

    return redirect(url_for("fight.battle"))
