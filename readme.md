# 🎮 POOKEMON - Jeu de Combat Pokémon POO

<div align="center">

**Bienvenue dans le monde des Pokémon, jeune dresseur !**

*Je suis le Professeur Chen. Les gens m'appellent le dingo des Pokémon !*  
*Ce monde est peuplé de créatures appelées Pokémon. Pour certaines personnes, les Pokémon sont des animaux de compagnie. Pour d'autres, comme moi, ils sont des objets d'étude...*

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![POO](https://img.shields.io/badge/POO-Architecture_Orientée_Objet-orange.svg)](https://github.com/FahZohh/POOKEMON)

[🎯 Fonctionnalités](#-fonctionnalités) •
[📦 Installation](#-installation) •
[🎮 Gameplay](#-gameplay) •
[🏗️ Architecture](#-architecture-poo) •
[🐛 Dépannage](#-dépannage)

</div>

---

## 📖 À Propos

**POOKEMON** est un jeu de combat Pokémon développé en **Python** avec une architecture **Programmation Orientée Objet (POO)** robuste. Ce projet éducatif met en pratique les concepts avancés de la POO tout en offrant une expérience de jeu authentique inspirée des classiques Pokémon Rouge/Bleu.

### 🎯 Fonctionnalités

#### ⚔️ Système de Combat Stratégique
- **Combat au tour par tour** avec phases joueur/IA
- **Système de types** complet (Feu 🔥, Eau 💧, Plante 🌿, Électrik ⚡, etc.)
- **Multiplicateurs de dégâts** selon les forces/faiblesses de types
- **Actions variées** : Attaque, Soin, Changement de Pokémon, Capture
- **IA adaptative** qui soigne son Pokémon quand ses PV sont bas

#### 🌟 Gestion d'Équipe Complète
- **Équipe de 6 Pokémon maximum** avec système de positions
- **Changement stratégique** en plein combat
- **Statistiques évolutives** : HP, Attaque, Défense, Vitesse
- **Système d'évolution** au niveau requis avec choix multiples
- **Pokémon Shiny** ultra-rares (1/200 de chance !)

#### 📊 Progression & Expérience
- **Système d'XP** avec gains de niveau
- **Stats dynamiques** qui augmentent à chaque niveau
- **Évolutions débloquables** selon le niveau atteint
- **Historique de combat** : Victoires et défaites trackées

#### 🎨 Interface Moderne
- **Application web Flask** avec interface responsive
- **Sprites animés** pour chaque Pokémon (normaux et chromatiques)
- **Authentification sécurisée** avec mots de passe hashés
- **Sessions persistantes** pour sauvegarder la progression
- **Flash messages** informatifs pour chaque action

#### 🎲 Fonctionnalités Avancées
- **Pokémon sauvages aléatoires** pour des combats variés
- **Capture système** avec taux de succès de 30%
- **Soin intelligent** : 30% de récupération si < 50% HP, sinon 10%
- **Centre Pokémon** pour soigner son équipe
- **Gestion de profil** : modifier username, email, mot de passe

---

## 📋 Prérequis

Avant de commencer ton aventure, assure-toi d'avoir ces outils installés :

| Outil | Version Minimale | Commande de Vérification |
|-------|------------------|--------------------------|
| **Python** | 3.7+ | `python --version` |
| **pip** | 20.0+ | `pip --version` |
| **MySQL** | 5.7+ ou MariaDB 10.2+ | `mysql --version` |
| **Git** | 2.0+ | `git --version` |

### 📦 Dépendances Python

Le projet utilise les packages suivants (voir `requirements.txt`) :
- `Flask==3.1.0` - Framework web
- `PyMySQL==1.1.1` - Driver MySQL pour Python
- `python-dotenv==1.0.1` - Gestion des variables d'environnement
- `Werkzeug==3.1.3` - Utilitaires WSGI et sécurité
- `cryptography==44.0.0` - Chiffrement
- `beautifulsoup4==4.12.3` - Parsing HTML

---

## 🚀 Installation

### Étape 1️⃣ : Cloner le Projet

```bash
git clone https://github.com/FahZohh/POOKEMON.git
cd POOKEMON
```

### Étape 2️⃣ : Environnement Virtuel (Recommandé)

Un bon dresseur isole ses expériences ! Crée un environnement virtuel :

**Sur Windows :**
```bash
python -m venv venv
venv\Scripts\activate
```

**Sur macOS/Linux :**
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ Tu verras `(venv)` apparaître dans ton terminal !

### Étape 3️⃣ : Installer les Dépendances

```bash
pip install -r requirements.txt
```

### Étape 4️⃣ : Configuration de la Base de Données

#### 4.1 - Créer la Base MySQL

**Option A - Depuis le terminal :**
```bash
mysql -u root -p < db.sql
```

**Option B - Depuis MySQL Workbench/phpMyAdmin :**
1. Ouvre ton client MySQL
2. Créez une nouvelle requête SQL
3. Copie le contenu de `db.sql`
4. Exécute le script

Cela va créer :
- Une base de données `pokemondb`
- Les tables : `player`, `pokemon`, `sprites`, `evolution`, `team`, `team_pokemon`

#### 4.2 - Configurer les Variables d'Environnement

Crée un fichier `.env` à la racine du projet :

```env
# Configuration MySQL
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=ton_mot_de_passe
MYSQL_DB=pokemondb

# Clé secrète Flask (génère une clé aléatoire sécurisée)
FLASK_SECRET_KEY=ta_cle_secrete_super_longue_et_aleatoire
```

**🔐 Génération d'une clé secrète Flask :**
```python
import secrets
print(secrets.token_hex(32))
```

#### 4.3 - Migration des Données Pokémon

Le projet utilise une base SQLite (`dbBrother/pokemon.db`) qui contient tous les Pokémon. Tu dois migrer ces données vers MySQL :

**⚠️ Important :** Modifie d'abord `scriptMigration.py` avec tes identifiants MySQL :

```python
mysqlConn = pymysql.connect(
    **{
        "host": "localhost",
        "user": "root",              # TON utilisateur MySQL
        "password": "ton_mot_de_passe",          # TON mot de passe MySQL
        "database": "pokemondb",
    }
)
```

Ensuite, lance la migration :

```bash
python scriptMigration.py
```

Ce script va :
- ✅ Transférer **tous les Pokémon** de SQLite vers MySQL
- ✅ Migrer les **évolutions** possibles
- ✅ Importer les **sprites** (normaux et chromatiques)

⏱️ *Cela prend environ 1-2 minutes selon ta machine.*

---

## 🎮 Gameplay

### Lancer le Jeu

Démarre le serveur Flask :

```bash
python app.py
```

Tu verras :
```
 * Running on http://0.0.0.0:80
 * Debug mode: off
```

### Accéder au Jeu

Ouvre ton navigateur et va sur :
- 🌐 **http://localhost:80**
- 🌐 **http://127.0.0.1:80**

### 🎯 Comment Jouer

#### 1. **Création de Compte** 🆕
- Clique sur "S'inscrire"
- Choisis un **nom d'utilisateur unique**
- Entre une **adresse email valide**
- Crée un **mot de passe sécurisé** (12+ caractères, majuscules, minuscules, chiffres, symboles)

#### 2. **Choisir ton Starter** 🌟
- Après inscription, tu dois créer une équipe
- Choisis parmi **3 Pokémon aléatoires** proposés
- Ce sera ton **premier compagnon** !

#### 3. **Combats Sauvages** ⚔️

##### Actions Disponibles :
| Action | Description | Détails |
|--------|-------------|---------|
| **⚔️ Attaquer** | Inflige des dégâts | Multiplicateur selon les types |
| **💊 Soigner** | Récupère des HP | 30% si < 50% HP, sinon 10% |
| **🔄 Changer** | Switch de Pokémon | Stratégique selon les types |
| **🎯 Capturer** | Tente de capturer | 30% de chance de succès |

##### Déroulement d'un Combat :
1. Le Pokémon le **plus rapide** attaque en premier
2. **Phase joueur** : Choisis ton action
3. **Phase IA** : L'adversaire riposte
4. Répète jusqu'à **KO** d'un des deux Pokémon

##### Victoire :
- Ton Pokémon gagne de l'**XP** (basée sur le niveau de l'adversaire)
- +1 **Victoire** dans ton profil
- Possibilité d'**évolution** si niveau requis atteint

##### Défaite :
- Si tous tes Pokémon sont KO, retour au **menu**
- +1 **Défaite** dans ton profil
- Soigne tes Pokémon avant de recommencer !

#### 4. **Évolution** ⬆️
Quand un Pokémon atteint le niveau requis :
- Un écran d'évolution s'affiche automatiquement
- **Choisis** vers quelle forme évoluer (certains ont plusieurs options)
- Ou **refuse** l'évolution pour garder la forme actuelle
- L'ancien Pokémon est **libéré** (retourne à l'état sauvage)

#### 5. **Gestion d'Équipe** 👥

Dans le menu "Mes Pokémon" :
- **Voir les stats** détaillées de chaque Pokémon
- **Soigner** un Pokémon blessé (HP à 100%)
- **Relâcher** un Pokémon (libère une place)
- **Changer l'ordre** de ton équipe (détermine qui combat en premier)

---

## 🏗️ Architecture POO

Ce projet est un exemple d'architecture **Programmation Orientée Objet** bien structurée.

### 📁 Structure du Projet

```
POOKEMON/
│
├── 📂 entity/                    # Entités métier (Classes POO)
│   ├── pokemon.py               # Classe Pokemon (HP, attaque, types, etc.)
│   ├── player.py                # Classe Player (utilisateur du jeu)
│   ├── types.py                 # Enum Types + Tableau d'efficacité
│   └── customConnection.py      # Wrapper de connexion MySQL
│
├── 📂 managers/                  # Gestionnaires (Logique métier)
│   └── loggingManager.py        # Configuration des logs
│
├── 📂 memory/                    # Cache en mémoire
│   └── player.py                # Gestion des joueurs en RAM
│
├── 📂 routes/                    # Routes Flask (Endpoints)
│   ├── fight.py                 # Routes de combat (/battle/*)
│   ├── player.py                # Routes joueur (/profil, /logout)
│   ├── userMenu.py              # Menu utilisateur (/menu, /pokemons)
│   └── evolution.py             # Routes d'évolution (/evolve)
│
├── 📂 templates/                 # Templates HTML (Jinja2)
│   ├── home.html                # Page d'accueil (login/register)
│   ├── battle.html              # Interface de combat
│   ├── evolve.html              # Écran d'évolution
│   └── player/                  # Sous-dossier profil utilisateur
│       ├── userMenu.html
│       ├── profile.html
│       ├── viewPokemons.html
│       └── ...
│
├── 📂 static/                    # Assets statiques
│   ├── css/                     # Feuilles de style
│   ├── js/                      # Scripts JavaScript
│   └── images/                  # Sprites Pokémon
│
├── 📂 dbBrother/                 # Base de données SQLite source
│   └── pokemon.db               # Données Pokémon originales
│
├── app.py                       # Point d'entrée Flask
├── utils.py                     # Utilitaires généraux (DB, sessions, etc.)
├── pokeUtils.py                 # Utilitaires Pokémon (combats, captures, etc.)
├── exception.py                 # Exceptions personnalisées
├── db.sql                       # Schéma MySQL
├── scriptMigration.py           # Migration SQLite → MySQL
├── requirements.txt             # Dépendances Python
├── .env                         # Variables d'environnement (à créer)
└── README.md                    # Ce fichier !
```

### 🎓 Concepts POO Utilisés

#### 1. **Encapsulation** 🔒

Les classes encapsulent leurs données et comportements.

```python
# entity/pokemon.py
class Pokemon:
    def __init__(self, id, name, pa, maxHealth, speed, level, ...):
        self.__id = id              # Attributs privés
        self.__name = name
        self.__pa = pa
        self.__currentHealth = maxHealth
        # ...
    
    def takeDamage(self, damage):   # Méthode publique
        """Inflige des dégâts au Pokémon"""
        self.__currentHealth = max(0, self.__currentHealth - damage)
    
    def heal(self, amount):
        """Soigne le Pokémon"""
        self.__currentHealth = min(self.__maxHealth, self.__currentHealth + amount)
```

#### 2. **Abstraction** 🧩

Les managers abstraient la complexité.

```python
# pokeUtils.py
def executeTurn(attacker, victim, action, newPokemon=None):
    """
    Abstraction complète d'un tour de combat.
    Le code appelant n'a pas besoin de connaître la logique interne.
    """
    if action == "attack":
        coefficient = getCoefficient(attacker, victim)
        damage = int(attacker.pa * coefficient)
        victim.takeDamage(damage)
        # ...
    elif action == "heal":
        # Logique de soin
    # ...
```

#### 3. **Séparation des Responsabilités** 📦

Chaque module a une responsabilité claire :

| Module | Responsabilité |
|--------|---------------|
| `entity/` | **Modèles de données** (Pokemon, Player, Types) |
| `routes/` | **Endpoints HTTP** (réception des requêtes) |
| `utils.py` | **Utilitaires généraux** (DB, sessions, validation) |
| `pokeUtils.py` | **Logique Pokémon** (combats, captures, évolutions) |
| `memory/` | **Cache** (optimisation des accès DB) |
| `managers/` | **Services** (logging, configuration) |

#### 4. **Gestion d'Erreurs Personnalisées** ⚠️

```python
# exception.py
class GlobalDatabaseException(Exception):
    """Erreur lors de l'accès à la base de données."""

class PlayerMemoryException(Exception):
    """Erreur lors de la gestion en mémoire des joueurs."""

# Utilisation dans le code
try:
    with getDbConnection() as conn:
        # ...
except GlobalDatabaseException as e:
    logger.error(f"Database error: {e}")
    flash("Une erreur est survenue.", "error")
```

---

## 🛠️ Technologies Utilisées

### Backend
- **Python 3.7+** - Langage principal
- **Flask 3.1.0** - Framework web WSGI
- **PyMySQL 1.1.1** - Driver MySQL pur Python
- **Werkzeug 3.1.3** - Utilitaires WSGI + hash de mots de passe
- **python-dotenv 1.0.1** - Gestion des variables d'environnement

### Frontend
- **HTML5** - Structure sémantique
- **CSS3** - Styles et animations
- **JavaScript** - Interactivité côté client
- **Jinja2** - Moteur de templating Flask

### Base de Données
- **MySQL 8.0+** - Base de données relationnelle
- **SQLite 3** - Base source pour la migration

### Sécurité
- **Werkzeug Security** - Hash bcrypt pour les mots de passe
- **Flask Sessions** - Sessions côté serveur chiffrées
- **Validation stricte** - Email, mot de passe, inputs utilisateur

---

## 🐛 Dépannage

### ❌ Problème : `ModuleNotFoundError: No module named 'flask'`

**Cause :** Les dépendances ne sont pas installées.

**Solution :**
```bash
# Active l'environnement virtuel
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Réinstalle les dépendances
pip install -r requirements.txt
```

---

### ❌ Problème : `pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost'")`

**Cause :** Identifiants MySQL incorrects.

**Solution :** Vérifie ton fichier `.env` :
```env
MYSQL_HOST=localhost
MYSQL_USER=ton_vrai_utilisateur
MYSQL_PASSWORD=ton_vrai_mot_de_passe
MYSQL_DB=pokemondb
```

---

### ❌ Problème : `OSError: [Errno 98] Address already in use`

**Cause :** Le port 80 est déjà utilisé.

**Solution 1 - Tuer le processus :**
```bash
# Linux/Mac
sudo lsof -ti:80 | xargs kill -9

# Windows
netstat -ano | findstr :80
taskkill /PID <PID> /F
```

**Solution 2 - Changer de port :**

Modifie `app.py` :
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Utilise le port 5000
```

Puis accède à http://localhost:5000

---

### ❌ Problème : `RuntimeError: The session is unavailable because no secret key was set`

**Cause :** La clé secrète Flask n'est pas définie.

**Solution :**

Ajoute dans ton `.env` :
```env
FLASK_SECRET_KEY=ta_cle_secrete_super_longue_et_aleatoire_minimum_32_caracteres
```

Ou génère-en une :
```python
import secrets
print(secrets.token_hex(32))
```

---

### ❌ Problème : "La base de données est vide, pas de Pokémon"

**Cause :** La migration n'a pas été exécutée.

**Solution :**

1. Vérifie que `dbBrother/pokemon.db` existe
2. Relance la migration :
```bash
python scriptMigration.py
```

---

### ❌ Problème : "Tous les champs sont obligatoires" lors de l'inscription

**Cause :** Le mot de passe ne respecte pas les critères.

**Solution :** Ton mot de passe DOIT contenir :
- ✅ Au moins **12 caractères**
- ✅ Au moins **1 majuscule**
- ✅ Au moins **1 minuscule**
- ✅ Au moins **1 chiffre**
- ✅ Au moins **1 caractère spécial** (!@#$%^&*, etc.)

**Astuce :** Utilise le bouton "Générer un mot de passe" sur la page d'inscription !

---

### ❌ Problème : "Ce Pokémon ne peut pas évoluer pour le moment"

**Cause :** Le Pokémon n'a pas atteint le niveau requis.

**Solution :** 
- Continue à combattre pour gagner de l'XP
- L'évolution se déclenchera automatiquement au bon niveau
- Tu peux refuser l'évolution si tu veux

---

### ❌ Problème : Les sprites ne s'affichent pas

**Cause :** Les URLs des sprites sont peut-être invalides.

**Solution :**
1. Vérifie la table `sprites` dans MySQL :
```sql
SELECT * FROM sprites LIMIT 5;
```
2. Les URLs doivent commencer par `https://`
3. Si nécessaire, re-migre les données

---

## 🎓 Concepts Pédagogiques

Ce projet est parfait pour apprendre :

- ✅ **POO en Python** - Classes, méthodes, encapsulation
- ✅ **Flask** - Routes, templates, sessions, blueprints
- ✅ **SQL** - Requêtes complexes, jointures, transactions
- ✅ **Architecture logicielle** - Séparation des responsabilités,
- ✅ **Gestion d'erreurs** - Try/except, exceptions personnalisées
- ✅ **Logging** - Traçabilité et débogage

---

## 💡 Idées d'Amélioration

Tu veux continuer le développement ? Voici des pistes :

### Fonctionnalités Gameplay
- [ ] **Arènes et Champions** - Combats contre des boss
- [ ] **Système de badges** - Collection après chaque victoire
- [ ] **Pokédex** - Enregistrement automatique des Pokémon rencontrés
- [ ] **Talents** - Capacités spéciales par Pokémon
- [ ] **Objets** - Potions, Balls variées, Pierres d'évolution
- [ ] **Météo** - Affecte les combats (pluie booste Eau, etc.)
- [ ] **Chat en ligne** - Discuter avec d'autres joueurs

### Technique
- [ ] **API REST** - Endpoints JSON pour un client mobile
- [ ] **WebSockets** - Combat en temps réel
- [ ] **Tests unitaires** - PyTest pour la couverture de code
- [ ] **Docker** - Containerisation de l'application
- [ ] **CI/CD** - GitHub Actions pour le déploiement auto

### Social
- [ ] **Multijoueur** - Combat entre joueurs réels
- [ ] **Échanges** - Trading de Pokémon
- [ ] **Classement** - Leaderboard des meilleurs dresseurs
- [ ] **Notifications** - Emails ou push pour les événements

---

## 🤝 Contribution

Tu veux améliorer le jeu ? Super !

1. **Fork** le projet sur GitHub
2. Crée une **branche** pour ta fonctionnalité :
   ```bash
   git checkout -b feature/SystemeDeCapacites
   ```
3. **Commit** tes changements :
   ```bash
   git commit -m "✨ Ajout du système de capacités spéciales"
   ```
4. **Push** vers ta branche :
   ```bash
   git push origin feature/SystemeDeCapacites
   ```
5. Ouvre une **Pull Request** avec une description détaillée

### 📝 Conventions de Commit

Utilise les préfixes suivants :
- ✨ `feat:` - Nouvelle fonctionnalité
- 🐛 `fix:` - Correction de bug
- 📝 `docs:` - Documentation
- 💄 `style:` - CSS/UI
- ♻️ `refactor:` - Refactoring de code
- ⚡️ `perf:` - Amélioration des performances
- ✅ `test:` - Ajout de tests

---

## 📝 License

**⚠️ Note Importante :** Pokémon est une marque déposée de **Nintendo/Game Freak/Creatures Inc.** Ce projet est un **fan-game éducatif** créé à des fins d'apprentissage. Il n'est **pas affilié** à Nintendo et n'a **aucun but lucratif**.

---

## Crédits

- **Données Pokémon** : Base SQLite préexistante
- **Inspiration** : Pokémon Rouge/Bleu (Game Boy, 1996)
- **Framework** : [Flask](https://flask.palletsprojects.com/)
- **Sprites** : Pokémon officiel © Game Freak/Nintendo

---

## 👨‍🔬 Message Final du Professeur Chen

> *"Félicitations, jeune dresseur ! Tu as installé ton propre jeu Pokémon et tu es maintenant prêt à partir à l'aventure !"*
>
> *"Mais souviens-toi : être un dresseur Pokémon ne se résume pas à gagner des combats. C'est créer des liens avec tes Pokémon, comprendre leurs forces et faiblesses, et grandir ensemble."*
>
> *"Ce projet t'aidera aussi à devenir un meilleur programmeur. La POO, c'est comme dresser des Pokémon : il faut de la pratique, de la patience, et de la passion pour ce que tu fais !"*
>
> *"Tu as désormais toutes les connaissances nécessaires pour :"*
> - *Comprendre l'architecture d'une application web complète*
> - *Maîtriser les concepts de la Programmation Orientée Objet*
> - *Gérer une base de données relationnelle*
> - *Sécuriser une application avec authentification*
>
> *"Maintenant, va ! Le monde des Pokémon t'attend !"*

<div align="center">

---

**⭐ Si ce projet t'a plu, donne-lui une étoile sur GitHub ! ⭐**

**🐛 Un bug ? Une idée ? [Ouvre une issue](https://github.com/FahZohh/POOKEMON/issues) !**

**💬 Des questions ? N'hésite pas à me contacter !**


**Bon courage, et n'oublie pas : Attrapez-les tous !.. enfin les 6 meilleurs**

---

*"Certaines personnes collectionnent des timbres. D'autres collectionnent des pièces de monnaie. Moi, je collectionne les connaissances sur les Pokémon !"*  
— **Professeur Chen**

</div>