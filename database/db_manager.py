"""
database/db_manager.py - Gestionnaire des fichiers JSON (base de données locale)
"""
import json
import os
import shutil
from datetime import datetime, date
from typing import List, Optional, Dict
import sys

# Chemin vers les données
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

FICHIERS = {
    'aliments': os.path.join(DATA_DIR, 'aliments.json'),
    'journal': os.path.join(DATA_DIR, 'journal.json'),
    'objectifs': os.path.join(DATA_DIR, 'objectifs.json'),
    'supplements': os.path.join(DATA_DIR, 'supplements.json'),
}

# Import des modèles
sys.path.insert(0, BASE_DIR)
from models.aliment import Aliment, ValeursNutritionnelles, EntreeJournal, ProfilUtilisateur


def _charger_json(chemin: str) -> dict:
    """Charge un fichier JSON, retourne un dict vide si absent"""
    try:
        with open(chemin, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _sauvegarder_json(chemin: str, data: dict):
    """Sauvegarde un dict en JSON avec backup automatique"""
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    # Backup avant écrasement
    if os.path.exists(chemin):
        backup = chemin + '.bak'
        shutil.copy2(chemin, backup)
    with open(chemin, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── ALIMENTS ────────────────────────────────────────────────────────────────

def charger_aliments() -> List[Aliment]:
    """Charge tous les aliments depuis la base de données"""
    data = _charger_json(FICHIERS['aliments'])
    return [Aliment.from_dict(a) for a in data.get('aliments', [])]


def sauvegarder_aliments(aliments: List[Aliment]):
    """Sauvegarde la liste complète des aliments"""
    data = _charger_json(FICHIERS['aliments'])
    data['aliments'] = [a.to_dict() for a in aliments]
    _sauvegarder_json(FICHIERS['aliments'], data)


def ajouter_aliment(aliment: Aliment) -> bool:
    """Ajoute un nouvel aliment, retourne False si doublon"""
    aliments = charger_aliments()
    # Vérification doublon par nom (insensible à la casse)
    noms_existants = [a.nom.lower().strip() for a in aliments]
    if aliment.nom.lower().strip() in noms_existants:
        return False
    aliments.append(aliment)
    sauvegarder_aliments(aliments)
    return True


def modifier_aliment(aliment_modifie: Aliment) -> bool:
    """Modifie un aliment existant par son ID"""
    aliments = charger_aliments()
    for i, a in enumerate(aliments):
        if a.id == aliment_modifie.id:
            aliments[i] = aliment_modifie
            sauvegarder_aliments(aliments)
            return True
    return False


def supprimer_aliment(aliment_id: str) -> bool:
    """Supprime un aliment par ID"""
    aliments = charger_aliments()
    avant = len(aliments)
    aliments = [a for a in aliments if a.id != aliment_id]
    if len(aliments) < avant:
        sauvegarder_aliments(aliments)
        return True
    return False


def basculer_favori(aliment_id: str):
    """Bascule l'état favori d'un aliment"""
    aliments = charger_aliments()
    for a in aliments:
        if a.id == aliment_id:
            a.favoris = not a.favoris
            break
    sauvegarder_aliments(aliments)


def rechercher_aliment(query: str) -> List[Aliment]:
    """Recherche approximative d'aliments par nom"""
    import difflib
    aliments = charger_aliments()
    if not query.strip():
        return aliments
    query = query.lower().strip()
    resultats = []
    for a in aliments:
        nom = a.nom.lower()
        # Recherche directe (contient)
        if query in nom:
            resultats.append((0, a))
            continue
        # Recherche approximative avec difflib
        ratio = difflib.SequenceMatcher(None, query, nom).ratio()
        # Recherche par mots
        mots_query = query.split()
        mots_nom = nom.split()
        score_mots = sum(1 for m in mots_query if any(m in mn for mn in mots_nom))
        score_total = ratio + (score_mots * 0.3)
        if score_total > 0.4 or ratio > 0.5:
            resultats.append((1 - score_total, a))

    resultats.sort(key=lambda x: x[0])
    return [a for _, a in resultats]


# ─── JOURNAL ─────────────────────────────────────────────────────────────────

def _date_str(d: date = None) -> str:
    return (d or date.today()).isoformat()


def charger_journal(jour: date = None) -> List[EntreeJournal]:
    """Charge les entrées du journal pour un jour donné"""
    data = _charger_json(FICHIERS['journal'])
    jour_str = _date_str(jour)
    entrees_brutes = data.get('journal', {}).get(jour_str, [])
    return [EntreeJournal.from_dict(e) for e in entrees_brutes]


def ajouter_entree_journal(entree: EntreeJournal, jour: date = None):
    """Ajoute une entrée dans le journal du jour"""
    data = _charger_json(FICHIERS['journal'])
    jour_str = _date_str(jour)
    if 'journal' not in data:
        data['journal'] = {}
    if jour_str not in data['journal']:
        data['journal'][jour_str] = []
    data['journal'][jour_str].append(entree.to_dict())
    _sauvegarder_json(FICHIERS['journal'], data)


def supprimer_entree_journal(id_entree: str, jour: date = None):
    """Supprime une entrée du journal"""
    data = _charger_json(FICHIERS['journal'])
    jour_str = _date_str(jour)
    if 'journal' in data and jour_str in data['journal']:
        data['journal'][jour_str] = [
            e for e in data['journal'][jour_str]
            if e.get('id_entree') != id_entree
        ]
    _sauvegarder_json(FICHIERS['journal'], data)


def modifier_entree_journal(entree_modifiee: EntreeJournal, jour: date = None):
    """Modifie une entrée existante"""
    data = _charger_json(FICHIERS['journal'])
    jour_str = _date_str(jour)
    if 'journal' in data and jour_str in data['journal']:
        for i, e in enumerate(data['journal'][jour_str]):
            if e.get('id_entree') == entree_modifiee.id_entree:
                data['journal'][jour_str][i] = entree_modifiee.to_dict()
                break
    _sauvegarder_json(FICHIERS['journal'], data)


def charger_dates_journal() -> List[str]:
    """Retourne toutes les dates du journal (pour historique)"""
    data = _charger_json(FICHIERS['journal'])
    return sorted(data.get('journal', {}).keys(), reverse=True)


# ─── OBJECTIFS & PROFIL ──────────────────────────────────────────────────────

def charger_profil() -> ProfilUtilisateur:
    """Charge le profil utilisateur"""
    data = _charger_json(FICHIERS['objectifs'])
    profil_data = data.get('profil', {})
    return ProfilUtilisateur.from_dict(profil_data) if profil_data else ProfilUtilisateur()


def sauvegarder_profil(profil: ProfilUtilisateur):
    """Sauvegarde le profil utilisateur et recalcule les objectifs"""
    data = _charger_json(FICHIERS['objectifs'])
    data['profil'] = profil.to_dict()
    data['objectifs_journaliers'] = profil.calcul_objectifs()
    _sauvegarder_json(FICHIERS['objectifs'], data)


def charger_objectifs() -> dict:
    """Charge les objectifs journaliers"""
    data = _charger_json(FICHIERS['objectifs'])
    return data.get('objectifs_journaliers', {
        'calories': 2000, 'proteines': 150, 'glucides': 200,
        'lipides': 65, 'fibres': 25, 'sel': 6, 'sucres': 50
    })


# ─── TOTAUX JOURNALIERS ───────────────────────────────────────────────────────

def calculer_totaux(entrees: List[EntreeJournal]) -> ValeursNutritionnelles:
    """Calcule les totaux nutritionnels d'une liste d'entrées"""
    total = ValeursNutritionnelles()
    for entree in entrees:
        total = total + entree.valeurs_calculees
    return total
