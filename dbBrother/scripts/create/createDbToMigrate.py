import sqlite3
import requests
import time
from bs4 import BeautifulSoup


def getFrenchName(pokemonId):
    """Récupère le nom français via l'espèce du Pokémon avec gestion d'erreur"""
    try:
        url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemonId}/"
        res = requests.get(url, timeout=10).json()
        for entry in res["names"]:
            if entry["language"]["name"] == "fr":
                return entry["name"]
        return None
    except Exception:
        return None


def get5gAnimatedSpriteUrls(englishName):
    cleanName = englishName.lower().replace(" ", "-").replace(".", "").replace("'", "")
    url = f"https://pokemondb.net/sprites/{cleanName}"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        gen5Section = soup.find("h2", string="Generation 5")
        if not gen5Section:
            return None
        table = gen5Section.find_next("table")
        animatedRow = None
        for row in table.find_all("tr"):
            text = row.get_text()
            if "Black 2" in text and "Animated" in text:
                animatedRow = row
                break
        if not animatedRow:
            return None
        sprites = {}
        links = animatedRow.find_all("a", class_="sprite-share-link")
        for link in links:
            img = link.find("img")
            if img and img.get("src"):
                src = img.get("src")
                if "anim/normal" in src:
                    sprites["spriteFace"] = src
                elif "anim/shiny" in src:
                    sprites["spriteChromatiqueFace"] = src
                elif "anim/back-normal" in src:
                    sprites["spriteDos"] = src
                elif "anim/back-shiny" in src:
                    sprites["spriteChromatiqueDos"] = src
        return sprites
    except Exception:
        return None


def getEvolutionData(pokemonId):
    """Récupère l'URL de la chaîne d'évolution"""
    try:
        url_species = f"https://pokeapi.co/api/v2/pokemon-species/{pokemonId}/"
        res_species = requests.get(url_species, timeout=10).json()
        chain_url = res_species["evolution_chain"]["url"]
        chain_id = chain_url.split("/")[-2]
        return chain_url, chain_id
    except:
        return None, None


def processChain(chain):
    """Parcourt la chaîne d'évolution récursivement"""
    results = []
    current_pokemon = chain["species"]["name"]

    for evo in chain["evolves_to"]:
        next_pokemon = evo["species"]["name"]
        details = evo["evolution_details"]

        # Niveau 25 par défaut si évolution spéciale (objet, bonheur, échange, etc.)
        level = 25
        if details and details[0].get("min_level"):
            level = details[0]["min_level"]

        results.append((current_pokemon, next_pokemon, level))
        # Récursion pour les évolutions à 3 stades (ex: Bulbizarre -> Herbizarre -> Florizarre)
        results.extend(processChain(evo))

    return results


def createDatabase():
    conn = sqlite3.connect("dbBrother/pokemon.db")
    cursor = conn.cursor()

    # Création des tables (PK AUTOINCREMENT garantit l'unicité des IDs)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS player
        (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            money     INTEGER   DEFAULT 0,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemon
        (
            id            INTEGER PRIMARY KEY, -- On utilise l'ID de l'API comme PK
            name          TEXT    NOT NULL,
            currentHealth INTEGER NOT NULL,
            powerAttack   INTEGER NOT NULL,
            speed         INTEGER NOT NULL,
            maxHealth     INTEGER NOT NULL,
            experience    INTEGER DEFAULT 0,
            level         INTEGER DEFAULT 1,
            necessaryExp  INTEGER DEFAULT 40,
            type1         TEXT    NOT NULL,
            type2         TEXT,
            isShiny       INTEGER DEFAULT 0,
            playerId      INTEGER,
            FOREIGN KEY (playerId) REFERENCES player (id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sprites
        (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemonId             INTEGER NOT NULL,
            spriteFace            TEXT,
            spriteDos             TEXT,
            spriteChromatiqueFace TEXT,
            spriteChromatiqueDos  TEXT,
            FOREIGN KEY (pokemonId) REFERENCES pokemon (id) ON DELETE CASCADE
        )
        """
    )

    # --- NOUVELLE TABLE EVOLUTION ---
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evolution
        (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemonId        INTEGER NOT NULL,   -- Le Pokémon qui évolue
            evolutionId      INTEGER NOT NULL,   -- Vers quel Pokémon il évolue
            levelRequirement INTEGER DEFAULT 25, -- Niveau requis pour l'évolution
            FOREIGN KEY (pokemonId) REFERENCES pokemon (id) ON DELETE CASCADE,
            FOREIGN KEY (evolutionId) REFERENCES pokemon (id) ON DELETE CASCADE,
            UNIQUE (pokemonId, evolutionId)      -- Éviter les doublons
        )
        """
    )

    conn.commit()
    return conn


def fillEvolutionTable(conn, limit):
    """Remplit la table evolution après avoir chargé les Pokémon"""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("[*] PHASE 2 : Remplissage de la table EVOLUTION")
    print("=" * 60)

    processed_chains = set()
    evolution_count = 0
    skipped_chains = 0
    errors = 0

    print(f"[*] Analyse de {limit} Pokémon pour détecter les chaînes d'évolution...")
    print("-" * 60)

    for pokemon_id in range(1, limit + 1):
        try:
            # Vérifier si le Pokémon existe dans la DB
            cursor.execute("SELECT id, name FROM pokemon WHERE id = ?", (pokemon_id,))
            result = cursor.fetchone()
            if not result:
                continue

            pokemon_name = result[1]

            # Récupérer la chaîne d'évolution
            chain_url, chain_id = getEvolutionData(pokemon_id)

            if not chain_id:
                continue

            if chain_id in processed_chains:
                skipped_chains += 1
                continue

            # Marquer cette chaîne comme traitée
            processed_chains.add(chain_id)

            print(
                f"\n[🔍] Chaîne #{chain_id} détectée via {pokemon_name} (ID: {pokemon_id})"
            )

            # Récupérer les données de la chaîne
            res = requests.get(chain_url, timeout=10).json()
            relations = processChain(res["chain"])

            if not relations:
                print(f"    ⚠️  Aucune évolution trouvée dans cette chaîne")
                continue

            print(f"    📊 {len(relations)} évolution(s) détectée(s) dans cette chaîne")

            # Insérer chaque relation d'évolution
            chain_evos = 0
            for parent_name, child_name, level in relations:
                try:
                    # Récupérer les IDs depuis l'API
                    p_res = requests.get(
                        f"https://pokeapi.co/api/v2/pokemon/{parent_name}", timeout=10
                    ).json()
                    c_res = requests.get(
                        f"https://pokeapi.co/api/v2/pokemon/{child_name}", timeout=10
                    ).json()

                    parent_id = p_res["id"]
                    child_id = c_res["id"]

                    # Vérifier que les deux Pokémon existent dans notre DB
                    cursor.execute(
                        "SELECT name FROM pokemon WHERE id = ?", (parent_id,)
                    )
                    parent_db = cursor.fetchone()
                    if not parent_db:
                        print(
                            f"    ⏭️  {parent_name.capitalize()} (ID:{parent_id}) pas en base, skip"
                        )
                        continue

                    cursor.execute("SELECT name FROM pokemon WHERE id = ?", (child_id,))
                    child_db = cursor.fetchone()
                    if not child_db:
                        print(
                            f"    ⏭️  {child_name.capitalize()} (ID:{child_id}) pas en base, skip"
                        )
                        continue

                    # Insérer la relation d'évolution
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO evolution (pokemonId, evolutionId, levelRequirement)
                        VALUES (?, ?, ?)
                        """,
                        (parent_id, child_id, level),
                    )

                    if cursor.rowcount > 0:
                        print(f"    ✅ {parent_db[0]} → {child_db[0]} (Niv.{level})")
                        evolution_count += 1
                        chain_evos += 1
                    else:
                        print(f"    ⏭️  {parent_db[0]} → {child_db[0]} (déjà en base)")

                except Exception as e:
                    print(f"    ❌ Erreur sur {parent_name} → {child_name}: {e}")
                    errors += 1
                    continue

            if chain_evos > 0:
                print(
                    f"    🎉 {chain_evos} évolution(s) ajoutée(s) pour cette chaîne !"
                )

            # Commit toutes les 10 chaînes
            if len(processed_chains) % 10 == 0:
                conn.commit()
                print(
                    f"\n[💾 SAVE] Checkpoint - {len(processed_chains)} chaînes traitées, {evolution_count} évolutions totales"
                )
                print("-" * 60)

            time.sleep(0.1)

        except Exception as e:
            print(f"[❌] Erreur chaîne Pokémon {pokemon_id}: {e}")
            errors += 1
            continue

    conn.commit()

    print("\n" + "=" * 60)
    print("📊 STATISTIQUES FINALES")
    print("=" * 60)
    print(f"✅ Chaînes traitées    : {len(processed_chains)}")
    print(f"✅ Évolutions ajoutées : {evolution_count}")
    print(f"⏭️  Chaînes skippées   : {skipped_chains}")
    print(f"❌ Erreurs rencontrées : {errors}")
    print("=" * 60 + "\n")


def main():
    conn = createDatabase()
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("[*] Connexion établie. Vérification du catalogue...")
        print("=" * 60)

        # Demander la limite
        print("\n1. Gen 1 (151) | 2. Gen 1-2 (251) | 3. Gen 1-5 (649) | 4. Full (1025)")
        choice = input("Votre choix : ").strip()
        limit = {"1": 151, "2": 251, "3": 649}.get(choice, 1025)

        print("\n" + "=" * 60)
        print(f"[*] PHASE 1 : Chargement des Pokémon (1-{limit})")
        print("=" * 60 + "\n")

        for i in range(1, limit + 1):
            try:
                # --- ÉTAPE 1 : Vérifier si le Pokémon existe déjà ---
                cursor.execute("SELECT id FROM pokemon WHERE id = ?", (i,))
                if cursor.fetchone():
                    print(f"[SKIP] {i}/{limit} : Pokémon déjà en base")
                    continue  # On passe au suivant sans requêter l'API

                # --- ÉTAPE 2 : Requête API Pokémon ---
                res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}", timeout=15)
                if res.status_code != 200:
                    print(f"\n[!] Erreur API pour ID {i}, passage...")
                    continue

                apiData = res.json()
                englishName = apiData["name"]
                frenchName = getFrenchName(i)
                displayName = (
                    frenchName.capitalize() if frenchName else englishName.capitalize()
                )

                stats = {s["stat"]["name"]: s["base_stat"] for s in apiData["stats"]}
                hp = stats.get("hp", 50)
                atk = (stats.get("attack", 50) + stats.get("special-attack", 50)) // 2

                # Insertion Pokémon (on force l'ID pour correspondre à l'API)
                cursor.execute(
                    """
                    INSERT INTO pokemon (id, name, currentHealth, powerAttack, speed, maxHealth, type1, type2)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        i,
                        displayName,
                        hp,
                        atk,
                        stats.get("speed", 50),
                        hp,
                        apiData["types"][0]["type"]["name"],
                        (
                            apiData["types"][1]["type"]["name"]
                            if len(apiData["types"]) > 1
                            else None
                        ),
                    ),
                )

                # --- ÉTAPE 3 : Requête Sprites ---
                urls = get5gAnimatedSpriteUrls(englishName)
                if urls:
                    cursor.execute(
                        """
                        INSERT INTO sprites (pokemonId, spriteFace, spriteDos, spriteChromatiqueFace,
                                             spriteChromatiqueDos)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            i,
                            urls.get("spriteFace"),
                            urls.get("spriteDos"),
                            urls.get("spriteChromatiqueFace"),
                            urls.get("spriteChromatiqueDos"),
                        ),
                    )
                    sprite_status = "✓"
                else:
                    sprite_status = "✗"

                print(f"[+] {i}/{limit} : {displayName} (Sprites: {sprite_status})")

                # Sauvegarde régulière pour ne pas tout perdre en cas de crash
                if i % 20 == 0:
                    conn.commit()
                    print(f"[SAVE] Checkpoint à {i}/{limit}")

                time.sleep(0.1)  # Pause pour éviter le ban IP / SSL Error

            except requests.exceptions.SSLError:
                print(f"\n[!] Erreur SSL au Pokémon {i}. Pause de 5s...")
                time.sleep(5)
            except Exception as e:
                print(f"\n[!] Erreur sur le Pokémon {i} : {e}")
                continue

        # --- PHASE 2 : Remplissage des évolutions ---
        conn.commit()
        fillEvolutionTable(conn, limit)

    except KeyboardInterrupt:
        print("\n" + "!" * 60)
        print("[!] Arrêt demandé par l'utilisateur (Ctrl+C)")
        print("!" * 60)
    finally:
        conn.commit()
        conn.close()
        print("\n" + "=" * 60)
        print("[*] Données sauvegardées. Base de données fermée.")
        print("=" * 60)


if __name__ == "__main__":
    main()
