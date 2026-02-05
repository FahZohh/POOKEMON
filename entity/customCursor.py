import pymysql

from exception import GlobalDatabaseException


class CustomCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, *args, **kwargs):
        try:
            return self._cursor.execute(*args, **kwargs)
        except pymysql.MySQLError as e:
            # Do not log the full SQL query to avoid potential information disclosure
            raise GlobalDatabaseException(
                "Erreur lors de l'exécution de la requête : %s" % e
            )

    def fetchone(self):
        try:
            return self._cursor.fetchone()
        except pymysql.MySQLError as e:
            raise GlobalDatabaseException(
                "Erreur SQL lors de la récupération d'une ligne : %s" % e
            )

    def fetchall(self):
        try:
            return self._cursor.fetchall()
        except pymysql.MySQLError as e:
            raise GlobalDatabaseException(
                "Erreur SQL lors de la récupération de toutes les lignes : %s" % e
            )

    def __getattr__(self, name):
        # Si customCursor n'a pas la méthode demandée,
        # on le récupère automatiquement depuis le vrai curseur.
        return getattr(self._cursor, name)

    # Support du "with" pour le context manager
    def __enter__(self):
        return self

    def __exit__(self, excType, excVal, excTb):
        # on ne gère pas commit/rollback ici car c'est géré par la connexion
        # return False pour toujours laisser remonter l'exception, si elle existe ou non
        self._cursor.close()
        return False
