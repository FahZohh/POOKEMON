import pymysql

from entity.customCursor import CustomCursor
from exception import GlobalDatabaseException


class CustomConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return CustomCursor(self._conn.cursor(*args, **kwargs))

    def commit(self):
        try:
            return self._conn.commit()
        except pymysql.MySQLError as e:
            raise GlobalDatabaseException("Erreur commit DB : %s" % e)

    def rollback(self):
        try:
            return self._conn.rollback()
        except pymysql.MySQLError as e:
            raise GlobalDatabaseException("Échec du rollback automatique : %s" % e)

    def __getattr__(self, name):
        # Si customConnection n'a pas la méthode demandée,
        # on le récupère automatiquement depuis la vraie connexion.
        return getattr(self._conn, name)

    # Support du "with" pour le context manager
    # Cela permet d'utiliser la connexion avec la syntaxe :
    #     with getDbConnection() as conn:
    def __enter__(self):
        """
        Méthode appelée automatiquement au début du bloc 'with'
        Pour que toutes les méthodes et protections de CustomConnection
          (cursor, commit, rollback, gestion des erreurs) soient disponibles
          dans le bloc 'with'.
        """
        return self

    def __exit__(self, excType, excVal, excTb):
        """
        Méthode appelée automatiquement à la fin du bloc 'with'
        Un rollback automatique est effectué si une exception survient, puis la connexion est toujours fermée.
        Le commit/rollback manuel n'est pas géré ici pour éviter les doubles commit/rollback.
        return False pour laisser remonter l'exception si elle existe
        """
        try:
            if excType is not None:
                try:
                    self._conn.rollback()
                except pymysql.MySQLError as e:
                    raise GlobalDatabaseException(
                        "Échec du rollback automatique : %s" % e
                    )
        finally:
            self._conn.close()
        return False
