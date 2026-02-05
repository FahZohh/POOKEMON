import logging

import pymysql
from flask import render_template, session, redirect, Blueprint, url_for, flash, request

from exception import GlobalDatabaseException
from pokeUtils import (
    getPokemonById,
    playerHasPokemon,
    getPlayerAllPokemons,
    getRandomWildPokemon,
)
from utils import fetchAuthenticatedPlayer, getDbConnection

userMenu = Blueprint("userMenu", __name__)

logger = logging.getLogger(__name__)


@userMenu.route("/menu")
def menu():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    # poké du joueur depuis son équipe
    playerPokemon = playerHasPokemon(player.id)

    if not playerPokemon:
        flash("Vous n'avez pas de Pokémon dans votre équipe", "error")
        return redirect(url_for("userMenu.chooseFirstPokemon"))

    return render_template("player/userMenu.html")


@userMenu.route("/choose-first-pokemon", methods=["GET", "POST"])
def chooseFirstPokemon():
    """Permet de créer une équipe et choisir le premier Pokémon."""

    player = fetchAuthenticatedPlayer()
    if player is None:
        flash("Vous devez être connecté pour accéder à cette page.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "teamName":
            teamName = request.form.get("teamName", f"Équipe {player.username}")

            if not teamName:
                flash("Le nom de l'équipe ne peut pas être vide.", "error")
                return redirect(url_for("userMenu.chooseFirstPokemon"))

            try:
                with getDbConnection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT id FROM team WHERE playerId = %s", (player.id,)
                        )
                        if cursor.fetchone():
                            flash("Vous avez déjà une équipe !", "error")
                        else:
                            cursor.execute(
                                "INSERT INTO team (playerId, name) VALUES (%s, %s)",
                                (player.id, teamName),
                            )
                            conn.commit()

            except GlobalDatabaseException as e:
                logger.error(f"Database error while creating team: {e}")
                flash("Erreur lors de la création de l'équipe.", "error")
                return redirect(url_for("userMenu.chooseFirstPokemon"))

            flash(f"Équipe « {teamName} » créée !", "success")

            return redirect(url_for("userMenu.chooseFirstPokemon"))

        elif action == "choosePokemon":
            pokemonId = request.form.get("pokemonId", type=int)

            if not pokemonId:
                flash("Veuillez choisir un Pokémon.", "error")
                return redirect(url_for("userMenu.chooseFirstPokemon"))

            try:
                with getDbConnection() as conn:
                    with conn.cursor() as cursor:
                        # Récupérer l'équipe
                        cursor.execute(
                            "SELECT id FROM team WHERE playerId = %s", (player.id,)
                        )
                        team = cursor.fetchone()

                        if not team:
                            flash("Créez d'abord votre équipe.", "error")
                            return redirect(url_for("userMenu.chooseFirstPokemon"))

                        teamId = team[0]

                        # Vérifier si un Pokémon existe déjà
                        cursor.execute(
                            "SELECT COUNT(*) FROM team_pokemon WHERE teamId = %s",
                            (teamId,),
                        )
                        if cursor.fetchone()[0] > 0:
                            flash(
                                "Vous avez déjà choisi votre premier Pokémon !", "error"
                            )
                            return redirect(url_for("userMenu.menu"))

                        cursor.execute(
                            """
                            INSERT INTO team_pokemon (teamId, pokemonId, position)
                            VALUES (%s, %s, %s)
                            """,
                            (teamId, pokemonId, 1),
                        )
                        cursor.execute(
                            "UPDATE pokemon SET playerId = %s WHERE id = %s",
                            (player.id, pokemonId),
                        )
                        conn.commit()

                pokemon = getPokemonById(pokemonId)

                flash(f"Tu as choisi {pokemon.name} !", "success")
                return redirect(url_for("userMenu.menu"))

            except GlobalDatabaseException as e:
                logger.error(f"Database error while choosing first pokemon: {e}")
                flash("Erreur lors de l'ajout du Pokémon.", "error")
                return redirect(url_for("userMenu.chooseFirstPokemon"))

    try:
        with getDbConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM team WHERE playerId = %s", (player.id,))
                hasTeam = cursor.fetchone() is not None

        pokemons = []
        while len(pokemons) < 3:
            pokemon = getRandomWildPokemon()
            if pokemon not in pokemons:
                pokemons.append(pokemon)

        pokemon1, pokemon2, pokemon3 = pokemons
    except GlobalDatabaseException as e:
        logger.error(f"Database error while fetching first pokemons: {e}")
        flash("Erreur lors de la récupération des Pokémons.", "error")
        return redirect(url_for("userMenu.menu"))

    return render_template(
        "player/chooseFirstPokemon.html",
        pokemon1=pokemon1,
        pokemon2=pokemon2,
        pokemon3=pokemon3,
        player=player,
        has_team=hasTeam,
    )


@userMenu.route("/pokemon/<int:pokemonId>/stats")
def viewPokemonStats(pokemonId):
    """Affiche les statistiques d’un Pokémon"""
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash("Vous devez être connecté pour accéder à cette page.", "error")
        return redirect(url_for("home"))

    pokemon = getPokemonById(pokemonId)

    if pokemon is None:
        flash("Pokémon introuvable.", "error")
        return redirect(url_for("userMenu.inventoryPokemons"))

    try:
        with getDbConnection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT t.id
                    FROM team_pokemon tp
                    JOIN team t ON tp.teamId = t.id
                    WHERE tp.pokemonId = %s AND t.playerId = %s
                """,
                    (pokemonId, player.id),
                )
                if cursor.fetchone() is None:
                    flash("Vous ne pouvez pas voir ce Pokémon.", "error")
                    return redirect(url_for("userMenu.inventoryPokemons"))
    except GlobalDatabaseException as e:
        logger.error(f"Erreur DB vérification Pokémon: {e}")
        flash("Erreur lors de la vérification du Pokémon.", "error")
        return redirect(url_for("userMenu.inventoryPokemons"))

    return render_template("player/viewPokemonStats.html", pokemon=pokemon)


@userMenu.route("/pokemons", methods=["GET", "POST"])
def inventoryPokemons():
    """Affiche tous les Pokémon et gère les actions (rename, drop, swap)"""
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash("Vous devez être connecté pour accéder à cette page.", "error")
        return redirect(url_for("home"))

    pokemons = getPlayerAllPokemons(player.id)

    if request.method == "POST":
        action = request.form.get("action")
        pokemonId = request.form.get("pokemonId", type=int)
        if action == "drop":
            try:
                with getDbConnection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE pokemon SET playerId = NULL, isShiny = 0 WHERE id = %s",
                            (pokemonId,),
                        )
                        cursor.execute(
                            "SELECT id from team WHERE playerId = %s", (player.id,)
                        )
                        team = cursor.fetchone()
                        cursor.execute(
                            "DELETE FROM team_pokemon WHERE pokemonId = %s AND teamId = %s",
                            (pokemonId, team[0]),
                        )
                        conn.commit()
                        flash("Le Pokémon a été relâché !", "success")
                        return redirect(url_for("userMenu.inventoryPokemons"))
            except GlobalDatabaseException as e:
                logger.error(f"Erreur DB lors du drop : {e}")
                flash("Erreur lors de la suppression du Pokémon.", "error")
                return redirect(url_for("userMenu.inventoryPokemons"))

        elif action == "heal":
            try:
                with getDbConnection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE pokemon SET currentHealth = maxHealth WHERE id = %s",
                            (pokemonId,),
                        )
                        conn.commit()
                        flash("Le Pokémon a été soigné !", "success")
            except GlobalDatabaseException as e:
                logger.error(f"Erreur DB lors du soin : {e}")
                flash("Erreur lors du soin du Pokémon.", "error")
                return redirect(url_for("userMenu.inventoryPokemons"))
        elif action == "swap":
            swapWithId = request.form.get("swapWith", type=int)

            # Vérifie qu'on ne swap pas le Pokémon avec lui-même
            if pokemonId == swapWithId:
                flash("Impossible d'échanger un Pokémon avec lui-même.", "error")
            else:
                try:
                    with getDbConnection() as conn:
                        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                            # récup les deux Pokémon
                            cursor.execute(
                                """
                                SELECT pokemonId, teamId, position
                                FROM team_pokemon
                                WHERE pokemonId IN (%s, %s)
                                """,
                                (pokemonId, swapWithId),
                            )
                            results = cursor.fetchall()
                except GlobalDatabaseException as e:
                    logger.error(f"Erreur DB lors du swap : {e}")
                    flash("Erreur lors de l'échange des Pokémon.", "error")
                    return redirect(url_for("userMenu.inventoryPokemons"))
                if len(results) != 2:
                    flash("Les deux Pokémon doivent être dans la même équipe.", "error")
                else:
                    p1, p2 = results[0], results[1]

                    if p1["teamId"] != p2["teamId"]:
                        flash(
                            "Les deux Pokémon doivent être dans la même équipe.",
                            "error",
                        )
                    else:
                        try:
                            with getDbConnection() as conn:
                                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                                    tempPosition = (
                                        7  # valeur temporaire qui n'existe pas
                                    )

                                    # étape 1 : donner une position temporaire au premier Pokémon

                                    cursor.execute(
                                        "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s",
                                        (tempPosition, p1["pokemonId"]),
                                    )

                                    # étape 2 : mettre la position du premier Pokémon à l'autre

                                    cursor.execute(
                                        "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s",
                                        (p1["position"], p2["pokemonId"]),
                                    )

                                    # étape 3 : mettre la position du deuxième Pokémon dans la position du premier

                                    cursor.execute(
                                        "UPDATE team_pokemon SET position = %s WHERE pokemonId = %s",
                                        (p2["position"], p1["pokemonId"]),
                                    )

                                    conn.commit()
                        except GlobalDatabaseException as e:
                            logger.error(f"Erreur DB lors du swap : {e}")
                            flash("Erreur lors de l'échange des Pokémon.", "error")
                            return redirect(url_for("userMenu.inventoryPokemons"))

                    newPokemon = getPokemonById(int(p2["pokemonId"]))

                    session["playerPokemon"] = newPokemon.toDict()
                    flash("Les Pokémon ont été échangés !", "success")
                    return redirect(url_for("userMenu.inventoryPokemons"))

    return render_template("player/viewPokemons.html", pokemons=pokemons)
