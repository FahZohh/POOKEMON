import logging
import secrets
import string

import pymysql
from flask import (
    session,
    render_template,
    request,
    redirect,
    url_for,
    Blueprint,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash

from exception import GlobalDatabaseException, PlayerMemoryException
from memory.player import (
    updatePlayerInMemory,
)
from utils import (
    emailExist,
    getDbConnection,
    isValidEmail,
    fetchAuthenticatedPlayer,
    validatePassword,
    usernameExist,
)

players = Blueprint("players", __name__)

logger = logging.getLogger(__name__)


@players.route("/generer_motdepasse")
def generatePassword():
    """Génère un mot de passe de 16 caractères avec au moins une majuscule, une minuscule, un chiffre et un caractère spécial."""
    # On force au moins un de chaque type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]

    # On complète avec 12 caractères aléatoires
    all_chars = string.ascii_letters + string.digits + string.punctuation
    password += [
        secrets.choice(all_chars) for _ in range(12)
    ]  # le _ signifique qqu'on use pas la variable

    # On mélange tout
    secrets.SystemRandom().shuffle(password)

    return jsonify({"password": "".join(password)})


@players.route("/profil", methods=["GET", "POST"])
def profile():
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    return render_template("player/profile.html", player=player)


@players.route("/profil/modifier", methods=["GET", "POST"])
def profileEdit():
    """
    Permet à un joueur de modifier son profil
    """
    player = fetchAuthenticatedPlayer()
    if player is None:
        flash(
            "Vous devez être connecté pour accéder à cette page.",
            "error",
        )
        return redirect(url_for("home"))

    if request.method == "POST":
        newUsername = request.form.get("name", "").strip()
        newEmail = request.form.get("email", "").strip()
        newPasswordInput = request.form.get("password")

        if not all([newUsername, newEmail]):
            flash(
                "Tout les champs sont obligatoires.",
                "error",
            )
            return redirect(url_for("players.profileEdit"))

        passwordToStore = None
        if newPasswordInput:
            errorPassword = validatePassword(newPasswordInput)
            if errorPassword:
                flash(errorPassword, "error")
                return redirect(url_for("players.profileEdit"))
            passwordToStore = generate_password_hash(newPasswordInput)
        else:
            with getDbConnection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT password FROM player WHERE id = %s", (player.id,)
                    )
                    passwordToStore = cursor.fetchone()["password"]

        if not isValidEmail(newEmail):
            flash(
                "L'adresse email n'est pas valide.",
                "error",
            )
            return redirect(url_for("players.profileEdit"))

        if newEmail != player.email and emailExist(newEmail):
            flash(
                "Les informations fournies correspondent à un compte existant.",
                "error",
            )
            return redirect(url_for("players.profileEdit"))

        if newUsername != player.username and usernameExist(newUsername):
            flash(
                "Le nom d'utilisateur est déjà pris.",
                "error",
            )
            return redirect(url_for("players.profileEdit"))

        try:
            with getDbConnection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE player
                        SET username=%s, email=%s, password=%s
                        WHERE id=%s
                        """,
                        (newUsername, newEmail, passwordToStore, player.id),
                    )
                conn.commit()
        except GlobalDatabaseException as e:
            logger.error("Erreur base : %s", e, exc_info=True)
            flash(
                "Une erreur est survenue. Veuillez réessayer plus tard.",
                "error",
            )
            return redirect(url_for("players.profileEdit"))

        try:
            updatePlayerInMemory(
                playerId=player.id, username=newUsername, email=newEmail
            )
        except PlayerMemoryException as e:
            logger.warning("Cache non mis à jour : %s", e)

        flash(
            "Profil mis à jour avec succès !",
            "success",
        )
        return redirect(url_for("players.profileEdit"))

    return render_template("player/profileEdit.html", player=player)


@players.route("/deconnexion", methods=["GET", "POST"])
def logout():
    """
    Permet à un utilisateur de se déconnecter
    """
    session.clear()
    return redirect(url_for("home"))
