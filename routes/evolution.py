import logging

from flask import request, render_template, session, redirect, url_for, Blueprint, flash
from utils import (
    fetchAuthenticatedPlayer,
)
from pokeUtils import (
    getPlayerActivePokemon,
    evolvePokemon,
    getEvolutions,
    canEvolve,
)

evolution = Blueprint("evolution", __name__)

logger = logging.getLogger(__name__)


@evolution.route("/evolve", methods=["GET", "POST"])
def evolve():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))
    pokemon = getPlayerActivePokemon(player.id)

    if not canEvolve(pokemon):
        flash(
            "Ce Pokémon ne peut pas évoluer pour le moment. Vous devez l'xp avant",
            "error",
        )
        return redirect(url_for("userMenu.inventoryPokemons"))

    player = fetchAuthenticatedPlayer()

    evolutions = getEvolutions(pokemon)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "dontEvolve":
            return redirect(url_for("userMenu.inventoryPokemons"))

        if action == "evolve":
            evolutionId = request.form.get("evolutionId")
            if evolutionId:
                evolvePokemon(pokemon.id, int(evolutionId), player)
                return redirect(url_for("userMenu.inventoryPokemons"))
            else:
                flash("Veuillez sélectionner une évolution.", "error")
                return render_template(
                    "evolve.html", evolutions=evolutions, pokemon=pokemon
                )

    return render_template("evolve.html", evolutions=evolutions, pokemon=pokemon)
