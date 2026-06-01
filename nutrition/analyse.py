"""
nutrition/analyse.py - Analyse de la qualité nutritionnelle et suggestions
"""
from typing import List, Tuple
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.aliment import Aliment, ValeursNutritionnelles


# ─── ALTERNATIVES SANTÉ ──────────────────────────────────────────────────────
ALTERNATIVES = {
    "nutella": ("Beurre de cacahuète naturel", "nettement moins sucré, plus protéiné"),
    "soda": ("Eau gazeuse + citron", "zéro sucre, zéro calorie"),
    "chips": ("Galettes de riz", "beaucoup moins calorique"),
    "biscuits": ("Fruits frais + amandes", "fibres et bons lipides"),
    "viennoiserie": ("Pain complet + fromage blanc", "plus de protéines, moins de sucres"),
    "fromage": ("Skyr ou cottage cheese", "plus protéiné, moins gras"),
    "yaourt sucre": ("Skyr nature + fruits", "plus protéiné, sans sucres ajoutés"),
    "pain blanc": ("Pain complet ou de seigle", "plus de fibres, IG plus bas"),
    "frites": ("Patate douce au four", "plus nutritif, moins de graisses"),
    "creme fraiche": ("Fromage blanc 0%", "protéiné, très peu de graisses"),
    "confiture": ("Purée de fruits sans sucre ajouté", "sans sucres raffinés"),
    "mayonnaise": ("Fromage blanc + moutarde", "beaucoup moins calorique"),
    "dessert": ("Skyr + fruits rouges", "protéiné, peu sucré"),
    "gâteau": ("Banana bread protéiné", "moins sucré, plus protéiné"),
    "hamburger": ("Burger maison poulet grillé", "moins gras, plus protéiné"),
    "pizza": ("Pizza sur base de chou-fleur", "moins de glucides"),
    "pâtes blanches": ("Pâtes complètes ou lentilles", "plus de fibres et protéines"),
    "riz blanc": ("Riz complet ou quinoa", "plus de fibres, IG plus bas"),
    "lait entier": ("Lait demi-écrémé ou végétal", "moins de graisses saturées"),
    "beurre": ("Huile d'olive", "meilleurs acides gras"),
    "sel": ("Herbes aromatiques + épices", "moins de sodium"),
    "charcuterie": ("Jambon blanc ou poulet tranché", "moins gras, moins de sel"),
}


def analyser_aliment(aliment: Aliment) -> List[Tuple[str, str]]:
    """
    Analyse un aliment et retourne une liste de (type_alerte, message).
    Types : 'attention' (orange), 'danger' (rouge), 'info' (bleu), 'ok' (vert)
    """
    v = aliment.valeurs_100g
    alertes = []

    # Sucres
    if v.sucres > 20:
        alertes.append(('danger', f"Très riche en sucres ({v.sucres}g/100g) — limite recommandée : 12g/100g"))
    elif v.sucres > 12:
        alertes.append(('attention', f"Assez sucré ({v.sucres}g/100g)"))

    # Graisses saturées
    if v.acides_gras_satures > 10:
        alertes.append(('danger', f"Très riche en graisses saturées ({v.acides_gras_satures}g/100g)"))
    elif v.acides_gras_satures > 5:
        alertes.append(('attention', f"Graisses saturées élevées ({v.acides_gras_satures}g/100g)"))

    # Sel
    if v.sel > 1.5:
        alertes.append(('danger', f"Très salé ({v.sel}g/100g) — limite : 1.5g/100g"))
    elif v.sel > 0.6:
        alertes.append(('attention', f"Sel modéré à élevé ({v.sel}g/100g)"))

    # Fibres (positif)
    if v.fibres > 5:
        alertes.append(('ok', f"Excellente source de fibres ({v.fibres}g/100g)"))
    elif v.fibres > 2.5:
        alertes.append(('info', f"Bonne source de fibres ({v.fibres}g/100g)"))

    # Protéines (positif)
    if v.proteines > 20:
        alertes.append(('ok', f"Très riche en protéines ({v.proteines}g/100g)"))
    elif v.proteines > 10:
        alertes.append(('info', f"Bonne source de protéines ({v.proteines}g/100g)"))

    # Ratio sucres/glucides (indicateur ultra-transformation)
    if v.glucides > 0 and v.sucres / v.glucides > 0.8:
        alertes.append(('attention', "Majorité des glucides sous forme de sucres simples"))

    # Rapport lipides/proteines suspect
    if v.lipides > 30 and v.proteines < 5:
        alertes.append(('attention', "Aliment très gras et peu protéiné"))

    # Calories
    if v.calories > 400:
        alertes.append(('info', f"Aliment très calorique ({v.calories} kcal/100g)"))

    if not alertes:
        alertes.append(('ok', "Profil nutritionnel équilibré"))

    return alertes


def score_sante(aliment: Aliment) -> int:
    """
    Calcule un score santé de 0 à 100 basé sur les valeurs nutritionnelles.
    Plus le score est élevé, plus l'aliment est sain.
    """
    v = aliment.valeurs_100g
    score = 50

    # Points positifs
    score += min(v.proteines * 0.5, 15)
    score += min(v.fibres * 2, 15)

    # Points négatifs
    score -= min(v.sucres * 0.8, 20)
    score -= min(v.acides_gras_satures * 1.5, 20)
    score -= min(v.sel * 5, 15)

    # Bonus si peu calorique et nutritif
    if v.calories < 100 and v.proteines > 5:
        score += 10

    return max(0, min(100, int(score)))


def couleur_score(score: int) -> str:
    """Retourne une couleur selon le score santé"""
    if score >= 70:
        return '#2ecc71'
    elif score >= 50:
        return '#f39c12'
    elif score >= 30:
        return '#e67e22'
    else:
        return '#e74c3c'


def suggestions_alternatives(aliment: Aliment, objectif: str = "maintien") -> List[str]:
    """Propose des alternatives selon l'objectif fitness"""
    suggestions = []
    nom_lower = aliment.nom.lower()
    v = aliment.valeurs_100g

    # Recherche dans la base d'alternatives
    for cle, (alt, raison) in ALTERNATIVES.items():
        if cle in nom_lower:
            suggestions.append(f"→ {alt} : {raison}")

    # Suggestions selon l'objectif
    if objectif == "seche":
        if v.calories > 300:
            suggestions.append("→ Chercher une version moins calorique (objectif sèche)")
        if v.lipides > 15:
            suggestions.append("→ Préférer une version moins grasse")
        if v.proteines < 10 and v.calories > 100:
            suggestions.append("→ Ajouter une source protéinée (poulet, skyr, œufs)")

    elif objectif == "prise_masse":
        if v.calories < 100:
            suggestions.append("→ Associer avec une source calorique dense (avoine, beurre de cacahuète)")
        if v.proteines < 5:
            suggestions.append("→ Compléter avec whey ou poulet pour les protéines")

    elif objectif == "maintien":
        if v.sucres > 15:
            suggestions.append("→ Limiter les portions ou choisir une version sans sucres ajoutés")

    if not suggestions:
        suggestions.append("✓ Aliment adapté à votre objectif")

    return suggestions[:4]  # Max 4 suggestions


def analyser_journee(entrees, objectifs: dict) -> List[Tuple[str, str]]:
    """Analyse globale de la journée alimentaire"""
    from database.db_manager import calculer_totaux
    totaux = calculer_totaux(entrees)
    conseils = []

    cal_obj = objectifs.get('calories', 2000)
    prot_obj = objectifs.get('proteines', 150)

    # Protéines
    pct_prot = (totaux.proteines / prot_obj * 100) if prot_obj > 0 else 0
    if pct_prot < 50:
        conseils.append(('attention', "Protéines insuffisantes — ajoutez viande, œufs ou légumineuses"))
    elif pct_prot > 150:
        conseils.append(('info', "Apport protéiné très élevé aujourd'hui"))

    # Fibres
    if totaux.fibres < 15:
        conseils.append(('attention', "Manque de fibres — plus de légumes et légumineuses"))

    # Sel
    if totaux.sel > 6:
        conseils.append(('danger', f"Apport en sel excessif ({totaux.sel:.1f}g — max recommandé : 6g)"))

    # Sucres
    sucres_obj = objectifs.get('sucres', 50)
    if totaux.sucres > sucres_obj:
        conseils.append(('attention', f"Sucres dépassés ({totaux.sucres:.0f}g/{sucres_obj}g)"))

    # Calories
    pct_cal = (totaux.calories / cal_obj * 100) if cal_obj > 0 else 0
    if pct_cal < 70:
        conseils.append(('info', f"Apport calorique faible ({int(pct_cal)}% de l'objectif)"))
    elif pct_cal > 110:
        conseils.append(('attention', f"Objectif calorique dépassé ({int(pct_cal)}%)"))

    if not conseils:
        conseils.append(('ok', "Excellente journée nutritionnelle !"))

    return conseils
