"""
models/aliment.py - Modèles de données pour l'application nutritionnelle
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import uuid


@dataclass
class ValeursNutritionnelles:
    """Valeurs nutritionnelles pour 100g/100ml"""
    calories: float = 0.0
    proteines: float = 0.0
    glucides: float = 0.0
    sucres: float = 0.0
    lipides: float = 0.0
    acides_gras_satures: float = 0.0
    fibres: float = 0.0
    sel: float = 0.0

    def calculer_pour_quantite(self, grammes: float) -> 'ValeursNutritionnelles':
        """Calcule les valeurs pour une quantité donnée en grammes"""
        facteur = grammes / 100.0
        return ValeursNutritionnelles(
            calories=round(self.calories * facteur, 1),
            proteines=round(self.proteines * facteur, 1),
            glucides=round(self.glucides * facteur, 1),
            sucres=round(self.sucres * facteur, 1),
            lipides=round(self.lipides * facteur, 1),
            acides_gras_satures=round(self.acides_gras_satures * facteur, 1),
            fibres=round(self.fibres * facteur, 1),
            sel=round(self.sel * facteur, 2),
        )

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'ValeursNutritionnelles':
        return cls(
            calories=float(d.get('calories', 0)),
            proteines=float(d.get('proteines', 0)),
            glucides=float(d.get('glucides', 0)),
            sucres=float(d.get('sucres', 0)),
            lipides=float(d.get('lipides', 0)),
            acides_gras_satures=float(d.get('acides_gras_satures', 0)),
            fibres=float(d.get('fibres', 0)),
            sel=float(d.get('sel', 0)),
        )

    def __add__(self, other: 'ValeursNutritionnelles') -> 'ValeursNutritionnelles':
        return ValeursNutritionnelles(
            calories=round(self.calories + other.calories, 1),
            proteines=round(self.proteines + other.proteines, 1),
            glucides=round(self.glucides + other.glucides, 1),
            sucres=round(self.sucres + other.sucres, 1),
            lipides=round(self.lipides + other.lipides, 1),
            acides_gras_satures=round(self.acides_gras_satures + other.acides_gras_satures, 1),
            fibres=round(self.fibres + other.fibres, 1),
            sel=round(self.sel + other.sel, 2),
        )


@dataclass
class Aliment:
    """Représente un aliment dans la base de données"""
    nom: str
    categorie: str
    valeurs_100g: ValeursNutritionnelles
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    marque: str = "Standard"
    favoris: bool = False

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'marque': self.marque,
            'categorie': self.categorie,
            'favoris': self.favoris,
            'valeurs_100g': self.valeurs_100g.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Aliment':
        return cls(
            id=d.get('id', str(uuid.uuid4())[:8]),
            nom=d['nom'],
            marque=d.get('marque', 'Standard'),
            categorie=d.get('categorie', 'autre'),
            favoris=d.get('favoris', False),
            valeurs_100g=ValeursNutritionnelles.from_dict(d.get('valeurs_100g', {})),
        )

    def __str__(self):
        return f"{self.nom} ({self.marque})" if self.marque != "Standard" else self.nom


@dataclass
class EntreeJournal:
    """Une entrée dans le journal quotidien"""
    aliment_id: str
    aliment_nom: str
    quantite_g: float
    valeurs_calculees: ValeursNutritionnelles
    id_entree: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    repas: str = "déjeuner"  # petit-déjeuner, déjeuner, dîner, collation
    heure: str = ""

    def to_dict(self):
        return {
            'id_entree': self.id_entree,
            'aliment_id': self.aliment_id,
            'aliment_nom': self.aliment_nom,
            'quantite_g': self.quantite_g,
            'repas': self.repas,
            'heure': self.heure,
            'valeurs_calculees': self.valeurs_calculees.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'EntreeJournal':
        return cls(
            id_entree=d.get('id_entree', str(uuid.uuid4())[:8]),
            aliment_id=d['aliment_id'],
            aliment_nom=d['aliment_nom'],
            quantite_g=float(d['quantite_g']),
            repas=d.get('repas', 'déjeuner'),
            heure=d.get('heure', ''),
            valeurs_calculees=ValeursNutritionnelles.from_dict(d.get('valeurs_calculees', {})),
        )


@dataclass
class ProfilUtilisateur:
    """Profil fitness de l'utilisateur"""
    nom: str = ""
    age: int = 25
    taille_cm: float = 175.0
    poids_kg: float = 75.0
    sexe: str = "homme"
    activite: str = "moderee"
    objectif: str = "maintien"

    FACTEURS_ACTIVITE = {
        "sedentaire": 1.2,
        "legere": 1.375,
        "moderee": 1.55,
        "intense": 1.725,
        "tres_intense": 1.9,
    }

    def calcul_bmr(self) -> float:
        """Calcul du métabolisme de base (formule Mifflin-St Jeor)"""
        if self.sexe == "homme":
            return 10 * self.poids_kg + 6.25 * self.taille_cm - 5 * self.age + 5
        else:
            return 10 * self.poids_kg + 6.25 * self.taille_cm - 5 * self.age - 161

    def calcul_tdee(self) -> float:
        """Dépense calorique totale journalière"""
        facteur = self.FACTEURS_ACTIVITE.get(self.activite, 1.55)
        return round(self.calcul_bmr() * facteur)

    def calcul_objectifs(self) -> dict:
        """Calcule les objectifs selon l'objectif fitness"""
        tdee = self.calcul_tdee()

        if self.objectif == "seche":
            calories = int(tdee * 0.80)
            proteines = int(self.poids_kg * 2.2)
        elif self.objectif == "prise_masse":
            calories = int(tdee * 1.15)
            proteines = int(self.poids_kg * 1.8)
        else:  # maintien
            calories = tdee
            proteines = int(self.poids_kg * 1.6)

        glucides = int((calories * 0.40) / 4)
        lipides = int((calories * 0.25) / 9)
        fibres = 25
        sel = 6

        return {
            'calories': calories,
            'proteines': proteines,
            'glucides': glucides,
            'lipides': lipides,
            'fibres': fibres,
            'sel': sel,
            'sucres': int(calories * 0.05 / 4),
        }

    def to_dict(self):
        return {
            'nom': self.nom,
            'age': self.age,
            'taille_cm': self.taille_cm,
            'poids_kg': self.poids_kg,
            'sexe': self.sexe,
            'activite': self.activite,
            'objectif': self.objectif,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'ProfilUtilisateur':
        return cls(
            nom=d.get('nom', ''),
            age=int(d.get('age', 25)),
            taille_cm=float(d.get('taille_cm', 175)),
            poids_kg=float(d.get('poids_kg', 75)),
            sexe=d.get('sexe', 'homme'),
            activite=d.get('activite', 'moderee'),
            objectif=d.get('objectif', 'maintien'),
        )
