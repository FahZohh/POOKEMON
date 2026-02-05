CREATE DATABASE pokemondb;
USE pokemondb;

CREATE TABLE player (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0
);

CREATE TABLE pokemon (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    currentHealth INT NOT NULL,
    powerAttack INT NOT NULL,
    speed INT NOT NULL,
    maxHealth INT NOT NULL,
    experience INT DEFAULT 0,
    level INT DEFAULT 1,
    necessaryExp INT DEFAULT 40,
    type1 VARCHAR(50) NOT NULL,
    type2 VARCHAR(50),
    isShiny BOOLEAN DEFAULT FALSE,
    playerId INT,
    FOREIGN KEY (playerId) REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE sprites (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    pokemonId INT NOT NULL,
    spriteFace TEXT,
    spriteDos TEXT,
    spriteChromatiqueFace TEXT,
    spriteChromatiqueDos TEXT,
    FOREIGN KEY (pokemonId) REFERENCES pokemon(id) ON DELETE CASCADE
);

CREATE TABLE evolution (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pokemonId INT NOT NULL,
    evolutionId INT NOT NULL,
    levelRequirement INT,
    FOREIGN KEY (pokemonId) REFERENCES pokemon(id) ON DELETE CASCADE,
    FOREIGN KEY (evolutionId) REFERENCES pokemon(id) ON DELETE CASCADE
);
CREATE TABLE team (
    id INT PRIMARY KEY AUTO_INCREMENT,
    playerId INT NOT NULL,
    name VARCHAR(100) DEFAULT 'Mon équipe',
    FOREIGN KEY (playerId) REFERENCES player(id) ON DELETE CASCADE
);

CREATE TABLE team_pokemon (
    teamId INT,
    pokemonId INT,
    position INT NOT NULL CHECK (position BETWEEN 1 AND 7),
    PRIMARY KEY (teamId, pokemonId),
    FOREIGN KEY (teamId) REFERENCES team(id) ON DELETE CASCADE,
    FOREIGN KEY (pokemonId) REFERENCES pokemon(id) ON DELETE CASCADE,
    UNIQUE KEY unique_position (teamId, position)
);