import sqlite3
import pymysql

# --- CONNEXIONS ---
# On pointe vers le nouveau fichier unique
sqliteConn = sqlite3.connect("dbBrother/pokemon.db")
sqliteConn.row_factory = sqlite3.Row
sqliteCursor = sqliteConn.cursor()

mysqlConn = pymysql.connect(
    **{
        "host": "votre-nom-host",
        "user": "votre-nom-user",
        "password": "votre-mot-de-passe",
        "database": "votre-databse",
    }
)
mysqlCursor = mysqlConn.cursor()


def migrate_table(table_name, columns_list, placeholders):
    print(f"Migration de la table {table_name}...")
    sqliteCursor.execute(f"SELECT * FROM {table_name}")
    rows = sqliteCursor.fetchall()

    count = 0
    columns = ", ".join(columns_list)
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    for row in rows:
        try:
            # on transforme la ligne SQLite en liste de valeurs
            values = [row[col] for col in columns_list]
            mysqlCursor.execute(query, values)
            count += 1
        except Exception as e:
            print(f"Erreur dans {table_name} à la ligne {count + 1}: {e}")

    mysqlConn.commit()
    print(f"-> {count} lignes migrees pour {table_name}.")


# --- EXECUTION ---

try:
    migrate_table(
        "pokemon",
        [
            "id",
            "name",
            "currentHealth",
            "powerAttack",
            "speed",
            "maxHealth",
            "experience",
            "level",
            "necessaryExp",
            "type1",
            "type2",
            "isShiny",
            "playerId",
        ],
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s",
    )

    migrate_table(
        "evolution",
        ["id", "pokemonId", "evolutionId", "levelRequirement"],
        "%s, %s, %s, %s",
    )

    # 3. Migrer les Sprites
    migrate_table(
        "sprites",
        [
            "id",
            "pokemonId",
            "spriteFace",
            "spriteDos",
            "spriteChromatiqueFace",
            "spriteChromatiqueDos",
        ],
        "%s, %s, %s, %s, %s, %s",
    )

    print("\n[SUCCESS] Migration totale terminee !")

except Exception as global_e:
    print(f"\n[ERROR] Migration interrompue : {global_e}")

finally:
    sqliteConn.close()
    mysqlConn.close()
