# Projet Pokémon - Guide d'Installation

Bienvenue, jeune dresseur ! Avant de partir à l'aventure, il te faudra préparer ton laboratoire.

## 📋 Prérequis

Assure-toi d'avoir ces outils installés sur ta machine :
- **Python** (version 3.7 ou supérieure)
- **MySQL** (ou MariaDB)
- **pip** (gestionnaire de paquets Python)

## 🚀 Installation

### Étape 1 : Récupération du projet

Clone ce dépôt sur ton ordinateur :
```bash
git clone <https://github.com/FahZohh/POOKEMON>
cd <POOKEMON>
```

### Étape 2 : Installation des dépendances

Installe toutes les bibliothèques nécessaires :
```bash
pip install -r requirements.txt
```

### Étape 3 : Configuration de la base de données

#### 3.1 - Création de la base
Ouvre ton client MySQL et exécute le script de création :
```bash
mysql -u root -p < db.sql
```
#### 3.2 - Migration des données
Completer la connexion à votre database dans scripMigration.py :
Exécute les scripts de migration dans l'ordre suivant :
```bash
python scriptMigration.py
```

Ces scripts vont peupler ta base avec :
- La liste complète des Pokémon
- Les évolutions possibles
- Les sprites animés

### Étape 4 : Lancement de l'application

Démarre le serveur :
```bash
python app.py
```

Ouvre ton navigateur et rends-toi à l'adresse :
```
http://localhost:80
```

## 🎉 C'est parti !

Ton aventure Pokémon peut maintenant commencer. Bonne chance, dresseur !

---

*En cas de problème, n'hésite pas à consulter les logs ou à ouvrir une issue sur le dépôt.*