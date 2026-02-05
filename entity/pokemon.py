from entity.types import Types


class Pokemon:
    def __init__(
        self,
        id: int,
        name: str,
        pa: int,
        maxHealth: int,
        speed: int,
        level: int,
        spriteFace: str,
        spriteDos: str,
        spriteChromatiqueFace: str,
        spriteChromatiqueDos: str,
        exp: int = 0,
        type1: Types = None,
        type2: Types = None,
        isShiny: int = 0,
    ):
        self.id = id
        self.name = name
        self.pa = pa
        self.maxHealth = maxHealth
        self.speed = speed
        self.level = level
        self.spriteFace = spriteFace
        self.spriteDos = spriteDos
        self.spriteChromatiqueFace = spriteChromatiqueFace
        self.spriteChromatiqueDos = spriteChromatiqueDos
        self.exp = exp
        self.necessaryExp = self.computeNecessaryExp()
        self.type1 = type1.type if type1 else None
        self.type2 = type2.type if type2 else None
        if isShiny == 1:
            self.isShiny = True
        else:
            self.isShiny = False
        self.currentHealth = maxHealth

    def computeNecessaryExp(self) -> int:
        """Permet de calculer l'XP nécessaire pour passer au niveau suivant"""
        # formule cubique : (n+1)³ - n³
        return (self.level + 1) ** 3 - self.level**3

    def getNecessaryExp(self) -> None:
        """Permet de mettre à jour l'XP nécessaire selon le niveau actuel"""
        self.necessaryExp = self.computeNecessaryExp()

    def canLevelUp(self) -> bool:
        """Permet de vérifier si le Pokémon a assez d'XP pour monter de niveau"""
        return self.exp >= self.necessaryExp

    def gainExp(self, amount: int, enemyLevel: int = None):
        """Permet d'ajouter de l'XP au Pokémon et gère les montées de niveau automatiques"""
        xpRatio = 1

        # bonus d'XP si l'ennemi est plus fort
        if enemyLevel:
            xpRatio = enemyLevel / self.level

        # calcul de l'XP finale avec le ratio
        finalXp = int(amount * xpRatio)
        self.exp += finalXp

        # montée de niveau automatique tant qu'il y a assez d'XP
        while self.canLevelUp():
            self.levelUp()

    def levelUp(self):
        """Permet de faire monter le Pokémon d'un niveau et améliore ses stats"""
        self.level += 1

        # retire l'XP utilisée pour la montée de niveau
        self.exp -= self.necessaryExp

        # recalcule l'XP nécessaire pour le prochain niveau
        self.getNecessaryExp()

        # attribution des stats selon le niveau atteint
        if self.level < 20:
            self.addStat(speed=1, pa=1, maxHealth=3)
        elif self.level < 40:
            self.addStat(speed=3, pa=4, maxHealth=8)
        elif self.level < 60:
            self.addStat(speed=4, pa=5, maxHealth=12)
        elif self.level < 80:
            self.addStat(speed=5, pa=6, maxHealth=15)
        else:
            self.addStat(speed=6, pa=7, maxHealth=20)

    def addStat(self, speed: int = 0, pa: int = 0, maxHealth: int = 0):
        """Permet d'ajouter des points aux statistiques et met à jour la base de données"""
        from pokeUtils import updatePokemon

        self.speed += speed
        self.pa += pa
        self.maxHealth += maxHealth

        self.currentHealth = self.maxHealth

        updatePokemon(self.id, self.toDict())

    def isKO(self) -> bool:
        """Permet de vérifier si le Pokémon est KO (PV <= 0)"""
        return self.currentHealth <= 0

    def heal(self, amount: float):
        """Permet de soigner le Pokémon d'un certain montant de PV"""
        return self.__add__(amount)

    def __add__(self, amount: float):
        """
        permet d'ajouter des PV sans dépasser le maximum
        (méthode demandée dans le TP, mais bon pas trés opti, autant tout faire dans une func?)
        """
        self.currentHealth += amount

        if self.currentHealth > self.maxHealth:
            self.currentHealth = self.maxHealth

        return amount

    def takeDamage(self, damage: int):
        """Permet d'nfliger des dégâts au Pokémon"""
        return self.__sub__(damage)

    def __sub__(self, damage: int):
        """
        Retire des PV sans descendre en dessous de 0
        (pareil que pour add, pas opti ?)
        """
        self.currentHealth -= damage

        if self.currentHealth < 0:
            self.currentHealth = 0

        return damage

    def toDict(self) -> dict:
        """permet de convertir le Pokémon en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "pa": self.pa,
            "maxHealth": self.maxHealth,
            "speed": self.speed,
            "level": self.level,
            "spriteFace": self.spriteFace,
            "spriteDos": self.spriteDos,
            "spriteChromatiqueFace": self.spriteChromatiqueFace,
            "spriteChromatiqueDos": self.spriteChromatiqueDos,
            "exp": self.exp,
            "necessaryExp": self.necessaryExp,
            "currentHealth": self.currentHealth,
            "type1": self.type1,
            "type2": self.type2,
            "isShiny": self.isShiny,
        }

    @classmethod
    def fromDict(cls, data: dict):
        """Crée un Pokémon à partir d'un dictionnaire"""
        # cls représente la classe Pokemon (pas une instance)
        # permet de créer un nouveau Pokemon sans passer par __init__
        pokemon = cls.__new__(cls)

        pokemon.id = data["id"]
        pokemon.name = data["name"]
        pokemon.pa = data["pa"]
        pokemon.maxHealth = data["maxHealth"]
        pokemon.speed = data["speed"]
        pokemon.level = data["level"]
        pokemon.spriteFace = data["spriteFace"]
        pokemon.spriteDos = data["spriteDos"]
        pokemon.spriteChromatiqueFace = data["spriteChromatiqueFace"]
        pokemon.spriteChromatiqueDos = data["spriteChromatiqueDos"]
        pokemon.exp = data["exp"]
        pokemon.necessaryExp = data["necessaryExp"]
        pokemon.currentHealth = data["currentHealth"]
        pokemon.type1 = data["type1"]
        pokemon.type2 = data["type2"]
        pokemon.isShiny = data["isShiny"]

        return pokemon
