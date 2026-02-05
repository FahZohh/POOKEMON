import logging
import os
import threading

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

from entity.player import Player
from exception import GlobalDatabaseException, PlayerMemoryException
from managers.loggingManager import setupLogging
from memory.player import loadPlayersInMemory, getPlayerFromMemory, addPlayerInMemory
from routes.evolution import evolution
from routes.fight import fight
from routes.player import players
from routes.userMenu import userMenu
from utils import (
    getDbConnection,
    registerInternalId,
    validatePassword,
    isValidEmail,
    emailExist,
    usernameExist,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

app.register_blueprint(fight)
app.register_blueprint(players)
app.register_blueprint(userMenu)
app.register_blueprint(evolution)

logger = logging.getLogger(__name__)

DELAYED_LOAD_SECONDS = 1

setupLogging()


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Page d'accueil avec gestion de la connexion et de l'inscription
    """
    if request.method == "POST":
        formType = request.form.get("formType")

        if formType == "login":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Tous les champs sont obligatoires.", "error")
                return redirect(url_for("home"))

            with getDbConnection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, password FROM player WHERE email = %s", (email,)
                    )
                    result = cursor.fetchone()

            if result is None:
                flash(
                    "Les informations fournies correspondent à un compte inexistant.",
                    "error",
                )
                return redirect(url_for("home"))

            player = getPlayerFromMemory(result[0])
            if player is None:
                flash(
                    "Les informations fournies correspondent à un compte inexistant.",
                    "error",
                )
                return redirect(url_for("home"))

            if check_password_hash(result[1], password):
                registerInternalId(player.id)
                flash("Connexion réussie !", "success")
                return redirect(url_for("userMenu.menu"))
            else:
                flash("Les informations fournies sont incorrectes.", "error")
                return redirect(url_for("home"))

        elif formType == "register":
            username = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not all([username, email, password]):
                flash("Tous les champs sont obligatoires.", "error")
                return redirect(url_for("home"))

            errorPassword = validatePassword(password)
            if errorPassword:
                flash(errorPassword, "error")
                return redirect(url_for("home"))

            if not isValidEmail(email):
                flash("L'adresse email n'est pas valide.", "error")
                return redirect(url_for("home"))

            if emailExist(email):
                flash(
                    "Les informations fournies correspondent à un compte existant.",
                    "error",
                )
                return redirect(url_for("home"))

            if usernameExist(username):
                flash(
                    "Le nom d'utilisateur est déjà pris.",
                    "error",
                )
                return redirect(url_for("home"))

            try:
                with getDbConnection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO player (username, email, password)
                            VALUES (%s, %s, %s)
                            """,
                            (
                                username,
                                email,
                                generate_password_hash(password),
                            ),
                        )
                        conn.commit()
                        playerId = cursor.lastrowid
            except GlobalDatabaseException as e:
                logger.error(
                    f"Database error during player registration: {e}", exc_info=True
                )
                flash("Une erreur est survenue. Veuillez réessayer plus tard.", "error")
                return redirect(url_for("home"))

            newPlayer = Player(
                id=playerId, username=username, email=email, wins=0, losses=0
            )

            try:
                addPlayerInMemory(newPlayer)
            except PlayerMemoryException as e:
                logger.error(f"Error adding player to memory: {e}", exc_info=True)
                flash("Une erreur est survenue. Veuillez réessayer plus tard.", "error")
                return redirect(url_for("home"))

            registerInternalId(playerId)

            flash(
                "Vous êtes maintenant connecté !",
                "success",
            )
            return redirect(url_for("userMenu.chooseFirstPokemon"))

    return render_template("home.html")


def loadData():
    """
    Permet de charger les datas en mémoire après un délai
    """
    try:
        loadPlayersInMemory()
        print("Chargement en mémoire terminé.")
    except Exception as e:
        print(f"Erreur lors du chargement en mémoire : {e}")


threading.Timer(DELAYED_LOAD_SECONDS, loadData).start()
# charge les utilisateurs en mémoire après un délai pour ne pas bloquer le démarrage de l'application


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
